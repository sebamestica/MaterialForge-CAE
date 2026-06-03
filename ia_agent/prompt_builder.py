import json
from typing import Dict, Any, List

class PromptBuilder:
    @staticmethod
    def build_system_prompt(config_summary: str, context: Dict[str, Any]) -> str:
        """
        Builds a compact system prompt describing the active configuration, 
        experimental RAG database records, ML predictions, and Domain Guard alerts.
        Forces the model to output ONLY the requested structural optimizer layout.
        """
        from backend.src.config import RAG_TOP_K, TABULAR_TOP_K

        # Format similar experiments
        experiments_str = ""
        sim_exps = context.get("similar_experiments", [])
        if sim_exps:
            exps = []
            for exp in sim_exps[:TABULAR_TOP_K]:
                exps.append(
                    f"- Probeta {exp.get('specimen_id')}: Material {exp.get('material').upper()}, Infill {exp.get('infill_density_percent')}%, "
                    f"UTS {exp.get('max_stress_MPa') or exp.get('ultimate_tensile_strength_MPa') or 'N/A'} MPa, "
                    f"Young Modulus {exp.get('young_modulus_MPa')} MPa."
                )
            experiments_str = "\n".join(exps)
        else:
            experiments_str = "No hay ensayos experimentales registrados en la vecindad."

        # Format RAG sources
        rag_str = ""
        rag_sources = context.get("rag_sources", [])
        if rag_sources:
            sources = []
            for src in rag_sources[:RAG_TOP_K]:
                sources.append(f"[Fuente: {src['source']}] (Confianza: {src['confidence']:.2f})\n{src['text']}")
            rag_str = "\n\n".join(sources)
        else:
            rag_str = "No se encontraron referencias documentales de literatura."

        # Format domain warnings
        warnings_str = ""
        domain_warnings = context.get("domain_warnings", [])
        if domain_warnings:
            warnings_str = "\n".join([f"- {w.get('text', w)}" for w in domain_warnings])
        else:
            warnings_str = "Parámetros dentro del dominio de entrenamiento."

        prediction = context.get("prediction", {})
        pred_modulus = prediction.get("predicted_young_modulus_MPa", "N/A")
        pred_stress = prediction.get("predicted_max_stress_MPa", "N/A")
        pred_energy = prediction.get("predicted_energy_density_MJ_m3", "N/A")

        solver_guidance = ""
        solver_res = context.get("optimized_solver_result")
        if solver_res:
            solver_guidance = (
                "=== SOLUCIONADOR MULTIOBJETIVO GEOMÉTRICO (BACKEND) ===\n"
                "El solucionador geométrico del backend ha calculado que la configuración óptima para cumplir con los requerimientos es:\n"
                f"- Patrón TPMS recomendado: '{solver_res['pattern']}'\n"
                f"- Infill Density recomendado: {solver_res['infillDensity']}%\n"
                f"- Wall Thickness recomendado: {solver_res['wallThickness']} mm\n"
                f"- Cell Size recomendado: {solver_res['cellSize']} mm\n"
                f"- Masa Geométrica Real calculada: {solver_res['estimated_mass_g']} g (≤ 100g)\n"
                f"- Capacidad de Carga mecánica estimada: {solver_res['estimated_load_kg']} kg\n"
                "REGLA DE OBLIGATORIEDAD: DEBES usar exactamente este infill, wallThickness y cellSize en tu CONFIG_PATCH para garantizar la factibilidad física y de carga.\n\n"
            )

        system_prompt = (
            "Actúas como un MOTOR DE OPTIMIZACIÓN ESTRUCTURAL y Copiloto CAD/CAE Técnico de MaterialForge.\n"
            "Tu comportamiento debe ser el de un kernel de optimización mecánica. Evita explicaciones redundantes o introducciones.\n\n"
            "=== REGLA DE CONCISION CRÍTICA (AL GRANO) ===\n"
            "- El usuario exige respuestas muy cortas, directas y sin rodeos.\n"
            "- La sección ## SUMMARY debe contener como MÁXIMO 2 oraciones muy breves describiendo la justificación física de la variante propuesta y su limitación.\n"
            "- No agregues explicaciones adicionales fuera de la estructura obligatoria.\n\n"
            "=== CONFIGURACIÓN ACTUAL DEL DISEÑO ===\n"
            f"{config_summary}\n"
            "=== LÍMITES FÍSICOS OBLIGATORIOS ===\n"
            "- Dimensiones máximas: 5.0 x 5.0 x 5.0 cm por eje (volumen máximo de 125.0 cm³).\n"
            "- Peso máximo: 100.0 gramos (100.0 g) o menos.\n"
            "- Formas permitidas: Cubo, Esfera, Cilindro, Cono, Toro, Pirámide o Prisma Hexagonal.\n\n"
            "=== CONTEXTO EXPERIMENTAL (DATASET REAL) ===\n"
            f"{experiments_str}\n\n"
            "=== PREDICCIÓN MODELO ML (MUESTRA VIRTUAL) ===\n"
            f"- Módulo de Young predicho: {pred_modulus} MPa\n"
            f"- Esfuerzo Máximo predicho: {pred_stress} MPa\n"
            f"- Densidad de Energía Absorbida predicha: {pred_energy} MJ/m³\n"
            f"- Nivel de Confianza: {context.get('domain_confidence', 'LOW')}\n\n"
            "=== ALERTAS DE EXTRAPOLACIÓN (DOMAIN GUARD) ===\n"
            f"{warnings_str}\n\n"
            "=== LITERATURA CIENTÍFICA (RAG) ===\n"
            f"{rag_str}\n\n"
            f"{solver_guidance}"
            "=== FORMATO OBLIGATORIO DE RESPUESTA (ESTRICTO) ===\n"
            "Tu respuesta debe ser corta, estructurada, técnica y accionable. Responde ÚNICAMENTE en el siguiente formato, sin saludos ni introducciones ni texto fuera del esquema:\n\n"
            "# RESULT\n\n"
            "## SUMMARY\n"
            "Máximo 2 oraciones cortas explicando la configuración sugerida y su principal tradeoff.\n\n"
            "## SCORES\n"
            "compression_strength: XX\n"
            "energy_absorption: XX\n"
            "printability: XX\n"
            "buckling_resistance: XX\n"
            "manufacturing_risk: XX\n"
            "confidence: XX\n"
            "(Escala 0-100 para cada score)\n\n"
            "## TRADEOFFS\n"
            "- [Tradeoff 1: ej. más rigidez vs menos absorción]\n"
            "- [Tradeoff 2: ej. más shell vs más tiempo impresión]\n"
            "- [Tradeoff 3: ej. más densidad vs más peso]\n"
            "(Máximo 4 bullets técnicos)\n\n"
            "## CONFIG_PATCH\n"
            "```json\n"
            "{\n"
            "  \"intent\": \"optimize_compression_strength\",\n"
            "  \"candidate\": \"graded_gyroid_v2\",\n"
            "  \"confidence\": 0.91,\n"
            "  \"estimated_improvement\": {\n"
            "    \"compression_strength_pct\": 28,\n"
            "    \"buckling_resistance_pct\": 21,\n"
            "    \"energy_absorption_pct\": 14,\n"
            "    \"printability_pct\": 8\n"
            "  },\n"
            "  \"config_patch\": {\n"
            "    \"material\": \"TPU_95A\",\n"
            "    \"geometry\": {\n"
            "      \"size_x_mm\": 50,\n"
            "      \"size_y_mm\": 50,\n"
            "      \"size_z_mm\": 50\n"
            "    },\n"
            "    \"structure\": {\n"
            "      \"pattern\": \"graded_gyroid\",\n"
            "      \"infill_density\": 62,\n"
            "      \"cell_size_mm\": 2.2,\n"
            "      \"cell_thickness_mm\": 1.15,\n"
            "      \"density_gradient\": true\n"
            "    },\n"
            "    \"shell\": {\n"
            "      \"wall_thickness_mm\": 2.4,\n"
            "      \"wall_count\": 5,\n"
            "      \"top_bottom_mm\": 2.2\n"
            "    },\n"
            "    \"print\": {\n"
            "      \"layer_height_mm\": 0.2,\n"
            "      \"speed_mm_s\": 28,\n"
            "      \"nozzle_temp_c\": 232,\n"
            "      \"bed_temp_c\": 55,\n"
            "      \"cooling\": 0.35\n"
            "    },\n"
            "    \"orientation\": {\n"
            "      \"build_axis\": \"vertical_z\",\n"
            "      \"continuous_load_alignment\": true\n"
            "    }\n"
            "  }\n"
            "}\n"
            "```\n\n"
            "## UI_ACTIONS\n"
            "- apply\n"
            "- compare\n"
            "- simulate\n"
        )
        return system_prompt

    @staticmethod
    def build_extraction_prompt(conversation_history: List[Dict[str, str]], assistant_response: str, current_config: Dict[str, Any]) -> str:
        """
        Builds the prompt for the JSON extraction model to produce a structured CopilotStructuredResponse.
        Explains how to map the new nested CONFIG_PATCH to flat parameters.
        """
        history_summary = ""
        for msg in conversation_history:
            history_summary += f"{msg['role'].upper()}: {msg['content']}\n"
        
        history_summary += f"ASSISTANT: {assistant_response}\n"

        prompt = (
            "Deberás actuar como un extractor de JSON estructurado a partir del historial de conversación "
            "entre un ingeniero y el copiloto de MaterialForge. Tu objetivo es parsear la conversación y "
            "generar un objeto JSON estructurado que represente la intención del asistente y las variantes de "
            "configuración paramétrica sugeridas.\n\n"
            "=== CONTEXTO DE LA CONFIGURACIÓN ACTUAL ===\n"
            f"{json.dumps(current_config, indent=2)}\n\n"
            "=== CONVERSACIÓN A ANALIZAR ===\n"
            f"{history_summary}\n"
            "=== INSTRUCCIONES DE EXTRACCIÓN ===\n"
            "Debes devolver un objeto JSON con el siguiente esquema exacto (respeta tipos de datos y nombres de campos):\n"
            "{\n"
            "  \"analysis\": {\n"
            "    \"text\": \"Resumen completo de la explicación del asistente en español. Debe incluir el SUMMARY, los SCORES y los TRADEOFFS en formato markdown técnico.\",\n"
            "    \"objective_detected\": \"Objetivo detectado (ej. compresión, absorción, rigidez, balance)\",\n"
            "    \"key_findings\": \"Hallazgos clave de literatura y simulación en español\",\n"
            "    \"mechanical_justification\": \"Justificación física y estructural en español\"\n"
            "  },\n"
            "  \"variants\": [\n"
            "    {\n"
            "      \"id\": \"variant_A\",\n"
            "      \"name\": \"Nombre corto de la variante (ej. Resistencia Máxima, Absorción Progresiva, Balance Eficiente)\",\n"
            "      \"description\": \"Justificación breve del diseño propuesto\",\n"
            "      \"score\": 90.0,\n"
            "      \"compression_score\": 95.0,\n"
            "      \"energy_absorption_score\": 80.0,\n"
            "      \"stability_score\": 90.0,\n"
            "      \"printability_score\": 85.0,\n"
            "      \"risk_level\": \"LOW\" o \"MEDIUM\" o \"HIGH\",\n"
            "      \"estimated_print_time\": \"ej. 1h 45m\",\n"
            "      \"estimated_mass\": \"ej. 42.5g\",\n"
            "      \"pros\": [\"pro 1\", \"pro 2\"],\n"
            "      \"cons\": [\"con 1\"],\n"
            "      \"warnings\": [\"advertencia si aplica\"],\n"
            "      \"config_patch\": {\n"
            "        \"material\": \"PLA\" o \"TPU\" (opcional),\n"
            "        \"infill\": número (10 a 100) (mapear de structure.infill_density) (opcional),\n"
            "        \"pattern\": \"gyroid\" o \"honeycomb\" o \"triply_periodic\" o \"grid\" (mapear de structure.pattern, ej. graded_gyroid se mapea a gyroid) (opcional),\n"
            "        \"cellSize\": número (1.0 a 10.0) (mapear de structure.cell_size_mm) (opcional),\n"
            "        \"cellThickness\": número (0.1 a 2.0) (mapear de structure.cell_thickness_mm) (opcional),\n"
            "        \"wallThickness\": número (0.4 a 4.0) (mapear de shell.wall_thickness_mm) (opcional),\n"
            "        \"dimX\": número (1.0 a 5.0) (mapear de geometry.size_x_mm / 10.0) (opcional),\n"
            "        \"dimY\": número (1.0 a 5.0) (mapear de geometry.size_y_mm / 10.0) (opcional),\n"
            "        \"dimZ\": número (1.0 a 5.0) (mapear de geometry.size_z_mm / 10.0) (opcional),\n"
            "        \"resolution\": \"Baja\" o \"Media\" o \"Alta\" (opcional),\n"
            "        \"layerHeight\": número (0.05 a 0.40) (mapear de print.layer_height_mm) (opcional),\n"
            "        \"printSpeed\": número (10 a 150) (mapear de print.speed_mm_s) (opcional),\n"
            "        \"shapeType\": \"Cubo\" (opcional)\n"
            "      }\n"
            "    }\n"
            "  ],\n"
            "  \"recommended_variant\": \"variant_A\",\n"
            "  \"ui_actions\": [\"apply\", \"compare\", \"simulate\"]\n"
            "}\n\n"
            "Reglas de extracción:\n"
            "1. MAPEA los parámetros del JSON anidado del asistente a la estructura de campos plana de config_patch descrita arriba (ej. structure.infill_density -> infill).\n"
            "2. Procura generar de 1 a 3 variantes basadas en lo que sugirió el asistente o en lo que consideres óptimo para su objetivo.\n"
            "3. Devuelve únicamente el objeto JSON bien formado."
        )
        return prompt
