import json
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from .schemas import CopilotStructuredResponse, ConfigPatch, ValidationReport, PredictionReport, RetrievedSource, AIAnalysis, VariantData
from .validators import validate_config_patch
from .tools.prediction_tool import PredictionTool
from .tools.domain_guard import DomainGuardTool
from .ollama_client import OllamaClient
from .prompt_builder import PromptBuilder

class ResponseParser:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or OllamaClient()
        self.predictor = PredictionTool()
        self.guard = DomainGuardTool()

    def extract_structured_response(
        self, 
        conversation_history: List[Dict[str, str]], 
        assistant_response: str, 
        current_config: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> CopilotStructuredResponse:
        """
        Extracts structured payload from assistant chat conversation.
        Runs a fast regex-based direct parser first to optimize speed and accuracy.
        Falls back to a 2-retry LLM repair mechanism if direct parsing fails.
        """
        # Try direct regex/string parser first
        direct_parsed = self._try_parse_markdown_response(assistant_response, current_config)
        if direct_parsed is not None:
            return direct_parsed

        # Formulate extraction prompt fallback
        extraction_prompt = PromptBuilder.build_extraction_prompt(
            conversation_history, assistant_response, current_config
        )

        messages = [
            {"role": "system", "content": "Eres un extractor estricto de JSON. Devuelve únicamente el objeto JSON solicitado."},
            {"role": "user", "content": extraction_prompt}
        ]

        parsed_json = None
        retries = 2
        
        for attempt in range(retries + 1):
            try:
                # Call Ollama in JSON mode
                parsed_json = self.client.chat_json(messages, options={"temperature": 0.0})
                break
            except Exception as e:
                if attempt == retries:
                    print(f"ResponseParser: structured extraction failed after {retries} retries: {e}")
                    # Return fallback
                    return self._generate_fallback(assistant_response, current_config, context_data, [f"Error de extracción JSON: {str(e)}"])
                
                # Add error context for retry
                messages.append({"role": "assistant", "content": json.dumps(parsed_json) if parsed_json else "Error"})
                messages.append({
                    "role": "user", 
                    "content": f"El JSON anterior falló o causó un error: {str(e)}. Por favor, corrígelo y devuelve únicamente el objeto JSON válido."
                })

        # Run Pydantic and physical validator checks
        try:
            # 1. Parse analysis
            analysis_dict = parsed_json.get("analysis") or {}
            analysis_obj = AIAnalysis(
                text=analysis_dict.get("text", assistant_response),
                objective_detected=analysis_dict.get("objective_detected", "balance"),
                key_findings=analysis_dict.get("key_findings", "Análisis estructural conversacional."),
                mechanical_justification=analysis_dict.get("mechanical_justification", "Justificación física nominal.")
            )

            # 2. Parse variants
            variants_list = []
            parsed_variants = parsed_json.get("variants") or []
            
            # If no variants were extracted, create a default candidate representing current config
            if not parsed_variants:
                parsed_variants = [{
                    "id": "variant_A",
                    "name": "Configuración Sugerida por Defecto",
                    "description": "Estado paramétrico sugerido por la IA para balance estructural.",
                    "score": 78.0,
                    "compression_score": 80.0,
                    "energy_absorption_score": 75.0,
                    "stability_score": 80.0,
                    "printability_score": 80.0,
                    "risk_level": "LOW",
                    "estimated_print_time": "1h 50m",
                    "estimated_mass": "42.0g",
                    "pros": ["Conserva el equilibrio general del diseño"],
                    "cons": [],
                    "warnings": [],
                    "config_patch": {}
                }]

            for v in parsed_variants:
                patch_data = v.get("config_patch") or {}
                # Validate the config patch
                validation_data = validate_config_patch(current_config, patch_data)
                
                # Merge patch for mass/volume calculations
                merged_config = current_config.copy()
                for k, val in validation_data["corrected_patch"].items():
                    if val is not None:
                        merged_config[k] = val
                
                # Estimate mass using calculator if not provided as string
                mass_val = v.get("estimated_mass")
                if not mass_val:
                    volume_cm3 = validation_data.get("estimated_volume_cm3", 125.0)
                    infill = merged_config.get("infill", 35.0)
                    mat = str(merged_config.get("material", "TPU")).lower()
                    wall = merged_config.get("wallThickness", 1.2)
                    from .tools.physics_calculator import PhysicsCalculator
                    mass_g = PhysicsCalculator.estimate_mass(volume_cm3, infill, mat, wall)
                    mass_val = f"{round(mass_g, 1)}g"
                
                config_patch_obj = ConfigPatch(**validation_data["corrected_patch"])
                
                variants_list.append(VariantData(
                    id=v.get("id", "candidate_A"),
                    name=v.get("name", "Propuesta de IA"),
                    description=v.get("description", "Ajuste de parámetros sugeridos por optimización."),
                    score=float(v.get("score", 80.0)),
                    compression_score=float(v.get("compression_score", 80.0)),
                    energy_absorption_score=float(v.get("energy_absorption_score", 80.0)),
                    stability_score=float(v.get("stability_score", 80.0)),
                    printability_score=float(v.get("printability_score", 80.0)),
                    risk_level=v.get("risk_level", "LOW"),
                    estimated_print_time=v.get("estimated_print_time", "1h 30m"),
                    estimated_mass=str(mass_val),
                    pros=v.get("pros") or [],
                    cons=v.get("cons") or [],
                    warnings=validation_data["warnings"] + (v.get("warnings") or []),
                    config_patch=config_patch_obj
                ))

            recommended_variant = parsed_json.get("recommended_variant") or (variants_list[0].id if variants_list else "variant_A")
            ui_actions = parsed_json.get("ui_actions") or ["apply", "compare", "simulate"]

            return CopilotStructuredResponse(
                analysis=analysis_obj,
                variants=variants_list,
                recommended_variant=recommended_variant,
                ui_actions=ui_actions
            )

        except (ValidationError, Exception) as val_err:
            print(f"ResponseParser: validation exception: {val_err}")
            return self._generate_fallback(assistant_response, current_config, context_data, [f"Error de validación de esquema: {str(val_err)}"])

    def _try_parse_markdown_response(
        self, 
        assistant_response: str, 
        current_config: Dict[str, Any]
    ) -> Optional[CopilotStructuredResponse]:
        """Runs a fast regex-based direct parser for the strict markdown structure."""
        try:
            import re
            
            # Helper to extract balanced JSON block
            def extract_json_block(text: str) -> str:
                start_idx = text.find('{')
                if start_idx == -1:
                    raise ValueError("No '{' found")
                brace_count = 0
                for i in range(start_idx, len(text)):
                    char = text[i]
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            return text[start_idx:i+1]
                raise ValueError("Unbalanced braces")

            # 1. Extract SUMMARY
            summary_match = re.search(r"## SUMMARY\s*\n(.*?)(?=\n## |\Z)", assistant_response, re.DOTALL | re.IGNORECASE)
            summary_text = summary_match.group(1).strip() if summary_match else ""
            if not summary_text:
                return None  # If the strict formatting is missing, fall back to LLM extraction

            # 2. Extract SCORES
            scores_match = re.search(r"## SCORES\s*\n(.*?)(?=\n## |\Z)", assistant_response, re.DOTALL | re.IGNORECASE)
            scores = {}
            if scores_match:
                for line in scores_match.group(1).split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip().lower()
                        val_match = re.search(r"(\d+(\.\d+)?)", val)
                        if val_match:
                            scores[key] = float(val_match.group(1))

            compression_score = scores.get("compression_strength", 80.0)
            energy_absorption_score = scores.get("energy_absorption", 80.0)
            printability_score = scores.get("printability", 80.0)
            stability_score = scores.get("buckling_resistance", 80.0)
            risk_score = scores.get("manufacturing_risk", 20.0)
            confidence_val = scores.get("confidence", 90.0)

            risk_level = "LOW"
            if risk_score > 70:
                risk_level = "HIGH"
            elif risk_score > 40:
                risk_level = "MEDIUM"

            # 3. Extract TRADEOFFS
            tradeoffs_match = re.search(r"## TRADEOFFS\s*\n(.*?)(?=\n## |\Z)", assistant_response, re.DOTALL | re.IGNORECASE)
            tradeoffs = []
            if tradeoffs_match:
                for line in tradeoffs_match.group(1).split("\n"):
                    line_str = line.strip()
                    if line_str.startswith("-") or line_str.startswith("*"):
                        tradeoffs.append(line_str.lstrip("-* ").strip())

            # 4. Extract CONFIG_PATCH JSON
            config_patch_sect = assistant_response
            config_patch_match = re.search(r"## CONFIG_PATCH\s*\n(.*)", assistant_response, re.DOTALL | re.IGNORECASE)
            if config_patch_match:
                config_patch_sect = config_patch_match.group(1)
            
            json_str = extract_json_block(config_patch_sect)
            json_data = json.loads(json_str)
            intent = json_data.get("intent", "recommend_config")
            candidate = json_data.get("candidate", "variant_A")
            nested_patch = json_data.get("config_patch", {})

            # 5. Extract UI_ACTIONS
            ui_actions_match = re.search(r"## UI_ACTIONS\s*\n(.*?)(?=\n## |\Z)", assistant_response, re.DOTALL | re.IGNORECASE)
            ui_actions = []
            if ui_actions_match:
                for line in ui_actions_match.group(1).split("\n"):
                    line_str = line.strip()
                    if line_str.startswith("-") or line_str.startswith("*"):
                        ui_actions.append(line_str.lstrip("-* ").strip())
            if not ui_actions:
                ui_actions = ["apply", "compare", "simulate"]

            # 6. Map nested config_patch to flat fields
            flat_patch = {}
            mat = nested_patch.get("material")
            if mat:
                mat_lower = mat.lower()
                if "tpu" in mat_lower:
                    flat_patch["material"] = "TPU"
                elif "pla" in mat_lower:
                    flat_patch["material"] = "PLA"
                elif "abs" in mat_lower:
                    flat_patch["material"] = "ABS"
                elif "petg" in mat_lower:
                    flat_patch["material"] = "PETG"
                else:
                    flat_patch["material"] = mat

            structure = nested_patch.get("structure") or {}
            if "infill_density" in structure:
                flat_patch["infill"] = float(structure["infill_density"])
            if "pattern" in structure:
                pat = structure["pattern"]
                pat_lower = pat.lower()
                if "gyroid" in pat_lower:
                    flat_patch["pattern"] = "gyroid"
                elif "honeycomb" in pat_lower:
                    flat_patch["pattern"] = "honeycomb"
                elif "triply" in pat_lower or "schwarz" in pat_lower or "periodic" in pat_lower:
                    flat_patch["pattern"] = "triply_periodic"
                elif "grid" in pat_lower:
                    flat_patch["pattern"] = "grid"
                else:
                    flat_patch["pattern"] = pat
            if "cell_size_mm" in structure:
                flat_patch["cellSize"] = float(structure["cell_size_mm"])
            if "cell_thickness_mm" in structure:
                flat_patch["cellThickness"] = float(structure["cell_thickness_mm"])

            shell = nested_patch.get("shell") or {}
            if "wall_thickness_mm" in shell:
                flat_patch["wallThickness"] = float(shell["wall_thickness_mm"])

            geometry = nested_patch.get("geometry") or {}
            if "size_x_mm" in geometry:
                flat_patch["dimX"] = float(geometry["size_x_mm"]) / 10.0
            if "size_y_mm" in geometry:
                flat_patch["dimY"] = float(geometry["size_y_mm"]) / 10.0
            if "size_z_mm" in geometry:
                flat_patch["dimZ"] = float(geometry["size_z_mm"]) / 10.0

            print_settings = nested_patch.get("print") or {}
            if "layer_height_mm" in print_settings:
                flat_patch["layerHeight"] = float(print_settings["layer_height_mm"])
            if "speed_mm_s" in print_settings:
                flat_patch["printSpeed"] = float(print_settings["speed_mm_s"])

            # Validate the flat patch
            validation_data = validate_config_patch(current_config, flat_patch)

            merged_config = current_config.copy()
            for k, val in validation_data["corrected_patch"].items():
                if val is not None:
                    merged_config[k] = val

            volume_cm3 = validation_data.get("estimated_volume_cm3", 125.0)
            infill = merged_config.get("infill", 35.0)
            mat_val = str(merged_config.get("material", "TPU")).lower()
            wall = merged_config.get("wallThickness", 1.2)
            from .tools.physics_calculator import PhysicsCalculator
            mass_g = PhysicsCalculator.estimate_mass(volume_cm3, infill, mat_val, wall)

            config_patch_obj = ConfigPatch(**validation_data["corrected_patch"])

            variant = VariantData(
                id=candidate,
                name=f"Variante Optimizada ({candidate})",
                description=summary_text,
                score=float(compression_score * 0.4 + printability_score * 0.3 + stability_score * 0.2 + energy_absorption_score * 0.1),
                compression_score=float(compression_score),
                energy_absorption_score=float(energy_absorption_score),
                stability_score=float(stability_score),
                printability_score=float(printability_score),
                risk_level=risk_level,
                estimated_print_time="1h 45m",
                estimated_mass=f"{round(mass_g, 1)}g",
                pros=tradeoffs[:2] if tradeoffs else ["Optimización mecánica avanzada"],
                cons=tradeoffs[2:4] if len(tradeoffs) > 2 else [],
                warnings=validation_data["warnings"],
                config_patch=config_patch_obj
            )

            analysis_obj = AIAnalysis(
                text=assistant_response,
                objective_detected=intent,
                key_findings=summary_text,
                mechanical_justification=summary_text
            )

            return CopilotStructuredResponse(
                analysis=analysis_obj,
                variants=[variant],
                recommended_variant=candidate,
                ui_actions=ui_actions
            )
        except Exception as e:
            print(f"Direct Python markdown parser failed: {e}")
            return None

    def _generate_fallback(
        self, 
        message: str, 
        current_config: Dict[str, Any], 
        context_data: Dict[str, Any], 
        errors: List[str]
    ) -> CopilotStructuredResponse:
        """Generates a safe fallback structured response when parsing or validation fails."""
        analysis_obj = AIAnalysis(
            text=message,
            objective_detected="unknown",
            key_findings="Error en extracción de JSON estructurado. Mostrando fallback heurístico.",
            mechanical_justification=f"Errores de parsing: {', '.join(errors)}"
        )
        
        default_variant = VariantData(
            id="variant_fallback",
            name="Configuración de Resguardo",
            description="Variante generada automáticamente debido a un error de parsing.",
            score=70.0,
            compression_score=70.0,
            energy_absorption_score=70.0,
            stability_score=70.0,
            printability_score=70.0,
            risk_level="LOW",
            estimated_print_time="2h 15m",
            estimated_mass="45.0g",
            pros=["Conserva el estado de diseño activo"],
            cons=["No se aplicaron las sugerencias mecánicas de la IA"],
            warnings=errors,
            config_patch=ConfigPatch()
        )
        
        return CopilotStructuredResponse(
            analysis=analysis_obj,
            variants=[default_variant],
            recommended_variant="variant_fallback",
            ui_actions=["apply", "compare"]
        )
