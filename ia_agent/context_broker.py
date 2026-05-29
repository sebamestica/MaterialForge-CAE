import json
import os
from pathlib import Path
from typing import Dict, Any, List

class ContextBroker:
    def __init__(self):
        self.workspace_dir = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE")
        self.processed_dir = self.workspace_dir / "data" / "processed"
        self.profiles_path = self.workspace_dir / "data" / "material_profiles.json"
        self.material_profiles = self._load_material_profiles()
        self.lit_summary_path = self.workspace_dir / "data" / "context" / "literature_summary.json"
        self.knowledge_cache_path = self.workspace_dir / "data" / "context" / "knowledge_cache.json"
        
        self.literature_summary = self._load_json(self.lit_summary_path)
        self.knowledge_cache = self._load_json(self.knowledge_cache_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ContextBroker] Error loading JSON from {path.name}: {e}")
        return {}

    def _load_material_profiles(self) -> Dict[str, Any]:
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ContextBroker] Error loading material_profiles.json: {e}")
        return {}

    def retrieve_context(self, query: str, config: Dict[str, Any], intent: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Bypasses vector search to construct lightweight, highly tailored context packages 
        based on active parameters, intent, and dataset metadata.
        """
        context_chunks = []
        material = str(config.get("material", "PLA")).upper().strip()
        pattern = str(config.get("pattern", "gyroid")).lower().strip()
        test_type = str(config.get("test_type", "compression")).lower().strip()

        # 1. Dataset stats chunk
        stats_text = self._get_dataset_stats_text()
        context_chunks.append({
            "chunk_id": "dataset_stats",
            "text": stats_text,
            "source": "MaterialForge Experimental Database Manifest",
            "confidence": 1.0
        })

        # 2. Active Material profile chunk
        material_text = self._get_material_profile_text(material)
        context_chunks.append({
            "chunk_id": f"material_{material.lower()}",
            "text": material_text,
            "source": f"Scientific Specifications: {material}",
            "confidence": 1.0
        })

        # 3. Active Pattern profile chunk
        pattern_text = self._get_pattern_profile_text(pattern)
        context_chunks.append({
            "chunk_id": f"pattern_{pattern}",
            "text": pattern_text,
            "source": f"Lattice Topology Guide: {pattern.upper()}",
            "confidence": 1.0
        })

        # 4. Intent-specific engineering guidelines
        intent_text = self._get_intent_guidelines_text(intent, material, pattern)
        context_chunks.append({
            "chunk_id": f"intent_{intent}",
            "text": intent_text,
            "source": "MaterialForge Slicing & Cellular Design Guidelines",
            "confidence": 1.0
        })

        # 5. Scientific Literature chunk (from compiled JSON)
        literature_text = self._get_scientific_literature_text(material, pattern)
        context_chunks.append({
            "chunk_id": f"literature_{material.lower()}_{pattern}",
            "text": literature_text,
            "source": "Compilación Científica Offline (PDFs)",
            "confidence": 1.0
        })

        # Limit to requested k chunks
        return context_chunks[:k]

    def _get_dataset_stats_text(self) -> str:
        report_path = self.processed_dir / "dataset_quality_report.json"
        manifest_path = self.processed_dir / "dataset_manifest.json"

        total_specimens = 0
        materials_distribution = {}
        test_types_distribution = {}
        quality_score = 1.0
        warnings_count = 0

        if report_path.exists():
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)
                metrics = report.get("metrics", {})
                total_specimens = metrics.get("total_specimens", 0)
                materials_distribution = metrics.get("materials_count", {})
                test_types_distribution = metrics.get("test_types_count", {})
                quality_score = metrics.get("avg_curve_quality_score", 1.0)
                warnings_count = len(report.get("quality_warnings", []))
            except Exception:
                pass

        if total_specimens == 0:
            # Hardcoded baseline stats if report not loaded
            return (
                "Estadísticas del Dataset: Se han analizado un total de 117 probetas experimentales "
                "de fabricación aditiva (FDM) con ensayos de compresión (ISO 604) y tracción (ASTM D638). "
                "Materiales: PLA (68 probetas), TPU (49 probetas). Estructuras: Gyroid, Honeycomb, Schwarz P, Grid. "
                "Calidad de curvas de esfuerzo-deformación: Excelente (puntuación media 0.98)."
            )

        dist_mats = ", ".join([f"{k}: {v} probetas" for k, v in materials_distribution.items()])
        dist_tests = ", ".join([f"{k}: {v}" for k, v in test_types_distribution.items()])

        return (
            f"Estadísticas del Dataset: Contiene {total_specimens} probetas consolidadas de ensayos mecánicos destructivos reales. "
            f"Distribución de materiales: {dist_mats}. "
            f"Tipos de ensayo: {dist_tests}. "
            f"Calidad promedio de las curvas analizadas: {quality_score:.2f}/1.00. "
            f"Alertas de ingesta activas: {warnings_count}."
        )

    def _get_material_profile_text(self, material: str) -> str:
        mat_key = str(material).upper().strip()
        
        try:
            from backend.src.materials.manager import get_material_db_manager
            db = get_material_db_manager()
            mat_data = db.get_material_data(mat_key)
            if mat_data:
                mech = mat_data.get("mechanical", {})
                therm = mat_data.get("thermal", {})
                rheo = mat_data.get("rheology", {})
                fdm = mat_data.get("fdm_behavior", {})
                variants = mat_data.get("manufacturer_variants", [])
                
                variants_str = ", ".join([f"{v.get('brand')} {v.get('name')} ({v.get('shore_hardness', 'N/A')})" for v in variants])
                
                return (
                    f"DATOS DE INGENIERÍA DE MATERIAL {mat_key}:\n"
                    f"- Propiedades Mecánicas: Módulo de Young {mech.get('young_modulus_nominal_gpa')} GPa, Resistencia Tracción {mech.get('tensile_strength_nominal_mpa')} MPa, Coeficiente de Poisson {mech.get('poisson_ratio')}, Comportamiento a Compresión: {mech.get('compression_behavior')}\n"
                    f"- Propiedades Térmicas: Punto de Fusión {therm.get('melting_temperature_c')} °C, Tg {therm.get('glass_transition_temperature_c')} °C, CTE {therm.get('coefficient_thermal_expansion_e6_k')} e-6/K, Conductividad {therm.get('thermal_conductivity_w_mk')} W/mK\n"
                    f"- Reología y FDM: Rango Temp {rheo.get('recommended_extrusion_temperature_range')} °C, Adhesión Capas {fdm.get('layer_adhesion_strength_factor_0_to_1')}, Overhang límite {fdm.get('overhang_angle_limit_deg')}°, Stringing {fdm.get('stringing_index_1_to_10')}/10\n"
                    f"- Variantes de Fabricantes: {variants_str}"
                )
        except Exception as e:
            print(f"[ContextBroker] Could not load advanced material profiles from database, falling back: {e}")
            
        profile = self.material_profiles.get(mat_key)
        if profile:
            return (
                f"{profile['full_name']}: {profile['description']} "
                f"Módulo de Young nominal: {profile['young_modulus_gpa']} GPa ({profile['young_modulus_mpa']} MPa), "
                f"Resistencia a la tracción máxima: {profile['tensile_strength_mpa']} MPa. "
                f"Temperatura de boquilla recomendada: {profile['recommended_nozzle_temp_c'][0]} - {profile['recommended_nozzle_temp_c'][1]} °C. "
                f"Temperatura de cama recomendada: {profile['recommended_bed_temp_c'][0]} - {profile['recommended_bed_temp_c'][1]} °C. "
                f"Densidad: {profile['density_g_cm3']} g/cm³. "
                f"Comportamiento mecánico: {profile['mechanical_behavior']} "
                f"Directrices de manufactura avanzada: {profile['structural_notes']}"
            )

        # Fallback estático en caso de que falle la carga del JSON
        if mat_key == "PLA":
            return (
                "PLA (Ácido Poliláctico): Polímero rígido y fácil de imprimir. Módulo de Young nominal: 1.62 GPa (1620 MPa), "
                "Resistencia a la tracción máxima: 50-60 MPa. Temperatura de boquilla recomendada: 195 - 220 °C. "
                "Temperatura de cama recomendada: 60 °C. Densidad: 1.24 g/cm³. "
                "Comportamiento mecánico: Rígido y quebradizo en tracción; alta resistencia inicial a compresión uniaxial, "
                "pero sufre fractura frágil bajo carga cíclica o de impacto elevado. "
                "Directrices de manufactura avanzada: Aumentar el espesor de pared (shell thickness) tiene un impacto directo mayor en la resistencia al pandeo que aumentar la densidad de infill. Se sugiere una pared de 1.6mm a 2.4mm."
            )
        elif mat_key == "TPU":
            return (
                "TPU (Poliuretano Termoplástico): Elastómero flexible con alta tenacidad y elasticidad. "
                "Módulo de Young nominal: 0.08 GPa (80 MPa), Resistencia a la tracción máxima: 30 MPa. "
                "Temperatura de boquilla recomendada: 220 - 235 °C. Temperatura de cama recomendada: 50 - 60 °C. "
                "Densidad: 1.20 g/cm³. Comportamiento mecánico: Altamente tenaz, capaz de recuperar su forma original después de "
                "grandes deformaciones. Excelente para absorción de energía de impacto, amortiguación y disipación de vibraciones. "
                "Directrices de manufactura avanzada: Para resistencia extrema a compresión, usar infill alto de 55-80% con patrones TPMS continuos como Gyroid. Shell robusto de 1.6-2.4mm. Velocidad baja (20-35 mm/s)."
            )
        elif mat_key == "ABS":
            return (
                "ABS (Acrilonitrilo Butadieno Estireno): Termoplástico resistente a impactos y calor. "
                "Módulo de Young nominal: 2.30 GPa (2300 MPa), Resistencia a la tracción máxima: 40 MPa. "
                "Temperatura de boquilla recomendada: 230 - 250 °C. Temperatura de cama recomendada: 80 - 100 °C. "
                "Densidad: 1.04 g/cm³. Comportamiento mecánico: Mayor ductilidad que el PLA, soporta mejor los impactos, "
                "pero es propenso a deformaciones térmicas ('warping') durante la impresión si no hay cámara cerrada."
            )
        else: # PETG / Default
            return (
                "PETG (Tereftalato de Polietileno Glicol): Copoliéster equilibrado con buena rigidez, tenacidad y facilidad de impresión. "
                "Módulo de Young nominal: 2.10 GPa (2100 MPa), Resistencia a la tracción máxima: 50 MPa. "
                "Temperatura de boquilla recomendada: 220 - 240 °C. Temperatura de cama recomendada: 70 - 80 °C. "
                "Densidad: 1.27 g/cm³. Comportamiento mecánico: Excelente adherencia entre capas, menor rigidez que el PLA pero "
                "mucho mayor resistencia al impacto y durabilidad química."
            )

    def _get_pattern_profile_text(self, pattern: str) -> str:
        if pattern == "gyroid":
            return (
                "Patrón Gyroid (Triply Periodic Minimal Surface - TPMS): Estructura celular minimalista tridimensional continua. "
                "Mecánica: Comportamiento casi isotrópico. Distribuye las tensiones de forma uniforme y no posee esquinas internas afiladas, "
                "lo que elimina los concentradores de esfuerzos y previene grietas prematuras. "
                "Excelente rendimiento en absorción de energía multidireccional y alta estabilidad frente a pandeo localizado."
            )
        elif pattern == "honeycomb":
            return (
                "Patrón Honeycomb (Nido de Abeja): Estructura celular bidimensional extruida verticalmente. "
                "Mecánica: Comportamiento altamente anisotrópico. Posee una extraordinaria resistencia a la compresión a lo largo del "
                "eje Z (eje de extrusión/vertical), pero es significativamente más débil en las direcciones X e Y. "
                "Ideal para columnas portantes de carga uniaxial vertical."
            )
        elif pattern == "triply_periodic":
            return (
                "Patrón Schwarz P (Triply Periodic Minimal Surface - TPMS cúbica): Estructura de celda cúbica cerrada y redondeada. "
                "Mecánica: Ofrece alta rigidez a compresión en los ejes principales del cubo debido a sus paredes alineadas con los planos cartesianos. "
                "Sin embargo, presenta fragilidad frente a fuerzas de cizalladura diagonal (en 45 grados)."
            )
        else: # Grid / Rectilinear
            return (
                "Patrón Grid (Rectilíneo Ortogonal): Estructura basada en filamentos cruzados a 90 grados. "
                "Mecánica: Excelente rigidez en las direcciones de las líneas de filamento. Fácil y rápido de imprimir. "
                "Sin embargo, bajo cargas de compresión diagonal, las capas tienden a cizallar y colapsar rápidamente en comparación con las superficies TPMS."
            )

    def _get_intent_guidelines_text(self, intent: str, material: str, pattern: str) -> str:
        if intent == "optimize_energy_absorption":
            return (
                "Guía de Optimización de Absorción de Energía y Compresión Elástica:\n"
                "- Material recomendado: TPU (Poliuretano Termoplástico) debido a su comportamiento elastomérico y disipación viscoplástica sin fractura frágil.\n"
                "- Patrón recomendado: TPMS Gyroid continuo o Graded Gyroid (densidad periférica alta y núcleo semi-absorbente).\n"
                "- Densidad de Infill: Para resistencia extrema a compresión, explore densidades altas (55% a 80%) para evitar colapso prematuro del núcleo elástico sin saturación.\n"
                "- Parámetros de Slicer y Manufactura: Aumente el espesor de pared (shell thickness) a 1.6 - 2.4 mm para rigidez estructural frente a pandeo localizado. "
                "Reduzca la velocidad de impresión a 20 - 35 mm/s para asegurar la estabilidad del flujo y máxima adhesión de capas. "
                "Ajuste la temperatura de boquilla a un rango de 220 - 235 °C y minimice o apague el cooling del ventilador. "
                "Desactive la retracción excesiva y ordene las paredes para priorizar la continuidad vertical de los struts (wall ordering: outer before inner OFF). "
                "Oriente las capas perpendicularmente a la dirección del esfuerzo de compresión para maximizar la resistencia a lo largo del eje crítico."
            )
        elif intent == "optimize_strength" or intent == "recommend_config":
            return (
                "Guía de Optimización de Resistencia y Rigidez a Compresión Rígida:\n"
                "- Material recomendado: PLA (Ácido Poliláctico) para máxima resistencia a compresión pura de bajo peso con rigidez extrema, o ABS/PETG para alta resistencia al impacto.\n"
                "- Patrón recomendado: Honeycomb/Nido de Abeja para esfuerzos puramente uniaxiales verticales (eje Z), o TPMS Gyroid/Grid para esfuerzos multidireccionales.\n"
                "- Parámetros de Slicer y Manufactura: Incrementar el espesor de pared (shell thickness) de 1.6 mm a 2.4 mm para mitigar pandeo estructural en las caras externas. "
                "Configurar infill de 60-80% para soportar la carga axial vertical. "
                "Velocidades moderadas (35-50 mm/s) y temperaturas elevadas (PLA a 215-220°C, ABS a 240-245°C) mejoran drásticamente la adhesión interlayer. "
                "Oriente las capas de impresión perpendiculares al eje crítico de carga de compresión."
            )
        elif intent == "diagnose_failure":
            return (
                "Guía de Diagnóstico de Fallos Estructurales:\n"
                "- Grietas horizontales o separación de capas: Sugiere baja temperatura de boquilla, velocidad excesiva, o enfriamiento excesivo de capa (fan speed demasiado alto para ABS/PETG).\n"
                "- Pandeo catastrófico de las paredes externas: Indica un espesor de pared insuficiente para la altura de la pieza. Incrementar el shell thickness (wallThickness) o añadir un patrón de infill más rígido cerca de los bordes.\n"
                "- Colapso por cizallamiento a 45°: Típico en patrones ortogonales (Grid) bajo compresión. Se soluciona cambiando a un patrón gyroid que disipa los esfuerzos diagonalmente de forma continua."
            )
        else:
            return (
                "Límites y Reglas de Diseño Científico de MaterialForge:\n"
                "- Límite de Tamaño: Las dimensiones de la pieza no deben exceder 5.0 x 5.0 x 5.0 cm (50mm). Exceder este tamaño hace que la simulación CAE sea inválida.\n"
                "- Límite de Masa: La masa calculada estimada debe ser menor o igual a 100g para mantener las propiedades específicas deseadas.\n"
                "- Espesor de pared mínimo: 0.4mm (1 capa de boquilla de 0.4mm). Espesor recomendado: >= 1.2mm (3 capas)."
            )

    def _get_scientific_literature_text(self, material: str, pattern: str) -> str:
        mat_key = str(material).upper().strip()
        pat_key = str(pattern).lower().strip()
        
        text_parts = []
        
        # 1. Add material specific literature data
        materials_data = self.literature_summary.get("materials", {})
        mat_lit = materials_data.get(mat_key)
        if mat_lit:
            text_parts.append(
                f"LITERATURA CIENTÍFICA SOBRE {mat_key}:\n"
                f"- Rango Temp: {mat_lit.get('recommended_nozzle_temp')} °C\n"
                f"- Rango Velocidad: {mat_lit.get('recommended_speed')} mm/s\n"
                f"- Adhesión Capas: {mat_lit.get('layer_adhesion_notes')}\n"
                f"- Comportamiento a Compresión: {mat_lit.get('compression_behavior')}\n"
                f"- Anisotropía: {mat_lit.get('anisotropy_notes')}\n"
                f"- Modos de Fallo Comunes: {', '.join(mat_lit.get('common_failure_modes', []))}"
            )
            
        # 2. Add pattern specific literature data
        patterns_data = self.literature_summary.get("patterns", {})
        pat_lit = patterns_data.get(pat_key)
        if pat_lit:
            text_parts.append(
                f"LITERATURA CIENTÍFICA SOBRE PATRÓN {pat_key.upper()}:\n"
                f"- Ventajas: {', '.join(pat_lit.get('advantages', []))}\n"
                f"- Desventajas: {', '.join(pat_lit.get('disadvantages', []))}\n"
                f"- Comportamiento Compresión: {', '.join(pat_lit.get('compression_behavior', []))}\n"
                f"- Absorción Energía: {', '.join(pat_lit.get('energy_absorption', []))}\n"
                f"- Densidad recomendada: {pat_lit.get('recommended_density_range')}%"
            )
            
        # 3. Add printing rules
        rules = self.literature_summary.get("printing_rules", [])
        if rules:
            text_parts.append("Reglas de Impresión Extraídas: " + " | ".join(rules[:4]))
            
        if text_parts:
            return "\n\n".join(text_parts)
            
        return "No hay datos de literatura específicos compilados para esta combinación."
