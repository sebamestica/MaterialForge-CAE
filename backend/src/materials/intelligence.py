from typing import Dict, Any, List
from .manager import get_material_db_manager

class MaterialIntelligenceEngine:
    def __init__(self):
        self.mgr = get_material_db_manager()

    def predictFailure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        material = str(config.get("material", "PLA")).upper().strip()
        infill = float(config.get("infill", 35.0))
        wall_thickness = float(config.get("wallThickness", 1.2))
        pattern = str(config.get("pattern", "gyroid")).lower().strip()
        orientation = str(config.get("orientation", "Isotrópica")).strip()
        
        failures = []
        overall_risk = "Bajo"
        
        # Check for delamination
        if orientation in ["Anisotrópica X", "Anisotrópica Y", "Anisotrópica Z"]:
            failures.append({
                "mode": "Delaminación Intercapa (Interlayer Delamination)",
                "risk": "Medio" if material != "ABS" else "Alto",
                "trigger": f"Fuerzas aplicadas sobre orientación {orientation}.",
                "prevention": "Aumentar temperatura de extrusión y reducir velocidad de ventilador de capa."
            })
            if material == "ABS":
                overall_risk = "Alto"
            elif overall_risk != "Alto":
                overall_risk = "Medio"
                
        # Check for warping
        if material == "ABS":
            failures.append({
                "mode": "Deformación por Contracción Térmica (Warping)",
                "risk": "Alto",
                "trigger": "Gradiente de temperatura y contracción del 1.5-2.0% del ABS.",
                "prevention": "Imprimir en cámara cerrada calefactada (>=80°C) y cama a >=100°C."
            })
            overall_risk = "Alto"
            
        # Check for local buckling
        if wall_thickness < 1.2 and infill < 30.0:
            failures.append({
                "mode": "Pandeo Localizado del Contorno (Shell Buckling)",
                "risk": "Alto" if material == "TPU" else "Medio",
                "trigger": f"Espesor de pared delgado ({wall_thickness} mm) y baja densidad de relleno ({infill}%).",
                "prevention": "Aumentar wallThickness >= 1.6 mm y usar relleno de soporte."
            })
            if overall_risk != "Alto":
                overall_risk = "Medio" if material != "TPU" else "Alto"
                
        # Check for TPU extrusion buckling
        if material == "TPU":
            failures.append({
                "mode": "Pandeo del Filamento en Extrusor (Extrusion Buckling)",
                "risk": "Medio",
                "trigger": "Compresión del elastómero flexible antes de la boquilla.",
                "prevention": "Utilizar extrusor de accionamiento directo (Direct Drive) y limitar la velocidad a < 35 mm/s."
            })
            
        if not failures:
            failures.append({
                "mode": "Fallo elástico por fatiga ordinaria",
                "risk": "Bajo",
                "trigger": "Ciclos de carga continuos.",
                "prevention": "Mantener factores de seguridad nominales (SF >= 1.5)."
            })
            
        return {
            "overall_risk_level": overall_risk,
            "detected_modes": failures
        }

    def getPrintability(self, config: Dict[str, Any], printer: str) -> Dict[str, Any]:
        material = str(config.get("material", "PLA")).upper().strip()
        speed = float(config.get("printSpeed", 40.0))
        
        # Load rules and check constraints
        mat_data = self.mgr.get_material_data(material)
        printer_rules = self.mgr.get_shared_data("manufacturing_rules").get("material_rules", {}).get(material, [])
        
        score = 100
        warnings = []
        
        # Direct Drive vs Bowden checks
        is_direct = printer in ["Creality K1 Max", "Ender 3 V3 KE"]
        profiles = mat_data.get("printer_profiles", {})
        profile = profiles.get("DirectDrive" if is_direct else "Bowden", {})
        
        max_speed = profile.get("max_print_speed_mm_s", 50.0)
        
        if speed > max_speed:
            diff = speed - max_speed
            deduction = min(30, int(diff * 1.5))
            score -= deduction
            warnings.append(
                f"Velocidad de impresión ({speed} mm/s) excede el límite recomendado para este material y extrusor ({max_speed} mm/s). Deducción: -{deduction} pts."
            )
            
        if material == "TPU" and not is_direct:
            score -= 25
            warnings.append("Peligro de atascamiento: TPU requiere extrusor Direct Drive para alimentación estable.")
            
        # Compile recommended parameters
        rec_temp = mat_data.get("thermal", {}).get("recommended_extrusion_temperature_range", [210, 230])
        retraction_dist = profile.get("retraction_distance_mm", 1.0)
        
        return {
            "printability_score": max(20, score),
            "warnings": warnings,
            "recommended_nozzle_temp_c": f"{rec_temp[0]} - {rec_temp[1]} °C",
            "recommended_retraction_distance_mm": f"{retraction_dist} mm",
            "extruder_type_utilized": "Direct Drive" if is_direct else "Bowden"
        }

    def getOptimalTPMS(self, material: str, variant: str) -> Dict[str, Any]:
        mat_key = str(material).upper().strip()
        
        if mat_key == "TPU":
            return {
                "optimal_structure": "Gyroid (TPMS)",
                "recommended_density_range": "55% - 80%",
                "rationale": "El patrón Gyroid continuo distribuye las fuerzas de flexión multidireccionales en el TPU elastómero, evitando concentraciones de esfuerzo y permitiendo una amortiguación viscoplástica del 95% sin pandeo lateral catastrófico."
            }
        elif mat_key == "ABS":
            return {
                "optimal_structure": "Honeycomb (Nido de Abeja)",
                "recommended_density_range": "40% - 60%",
                "rationale": "Para ABS, el patrón Honeycomb alineado con el eje vertical (Z) proporciona una rigidez estructural óptima que absorbe esfuerzos de compresión axial moderando la contracción volumétrica."
            }
        else: # PETG / PLA
            return {
                "optimal_structure": "Gyroid o Diamond TPMS",
                "recommended_density_range": "35% - 55%",
                "rationale": "La isotropía y continuidad del Gyroid previene el agrietamiento interlayer a 45 grados por cizalla en termoplásticos semicristalinos."
            }

    def getCompressionBehavior(self, material: str, variant: str, infill: float) -> Dict[str, Any]:
        mat_key = str(material).upper().strip()
        mat_data = self.mgr.get_material_data(mat_key)
        mech_data = mat_data.get("mechanical", {})
        
        elastic_modulus = mech_data.get("young_modulus_nominal_gpa", 1.0)
        rebound = mech_data.get("rebound_resilience_percent", 50.0)
        
        # Scaling modulus by infill relative density approximation
        rel_density = infill / 100.0
        effective_modulus = elastic_modulus * (rel_density ** 1.8)
        
        # Determine hyperelastic parameters if TPU
        hyperelastic = mech_data.get("hyperelastic_model", None)
        
        return {
            "effective_modulus_gpa": round(effective_modulus, 4),
            "rebound_resilience_percent": rebound,
            "hyperelastic_response": hyperelastic,
            "plateau_region_start_strain": 0.05 if mat_key == "TPU" else "N/A",
            "densification_threshold_strain": round(0.85 * (1.0 - rel_density), 2),
            "energy_absorption_efficiency": "Excelente (Viscoelástica)" if mat_key == "TPU" else "Moderada (Deformación Plástica)"
        }

    def getAnisotropyRisk(self, material: str, orientation: str) -> Dict[str, Any]:
        shared_anisotropy = self.mgr.get_shared_data("anisotropy")
        coefs = shared_anisotropy.get("transverse_isotropy_coefficients", {}).get(material, {})
        safety_factors = shared_anisotropy.get("orientation_safety_factors", {})
        
        factor = safety_factors.get(orientation, 1.0)
        z_xy_ratio = coefs.get("z_modulus_gpa", 1.0) / coefs.get("xy_modulus_gpa", 1.0) if coefs else 1.0
        
        risk = "Bajo"
        if factor < 0.6:
            risk = "Alto"
        elif factor < 0.9:
            risk = "Medio"
            
        return {
            "anisotropy_risk_level": risk,
            "strength_reduction_factor": factor,
            "z_to_xy_stiffness_ratio": round(z_xy_ratio, 2),
            "guideline": "Orientar la pieza para que los planos de capas de impresión sean perpendiculares a la fuerza de compresión principal para evitar el cizallamiento intercapa."
        }

    def getThermalRisk(self, material: str, chamber_type: str) -> Dict[str, Any]:
        mat_key = str(material).upper().strip()
        mat_data = self.mgr.get_material_data(mat_key)
        thermal_data = mat_data.get("thermal", {})
        
        cte = thermal_data.get("coefficient_thermal_expansion_e6_k", 80.0)
        tg = thermal_data.get("glass_transition_temperature_c", 60.0)
        
        warping_risk = "Bajo"
        if mat_key == "ABS" and chamber_type != "Cerrada Calefactada":
            warping_risk = "Muy Alto"
        elif mat_key == "PETG" and chamber_type == "Abierta":
            warping_risk = "Medio"
            
        return {
            "warping_risk_level": warping_risk,
            "coefficient_of_thermal_expansion": f"{cte} x 10^-6 / K",
            "glass_transition_temp_c": tg,
            "recommended_chamber_environment": "Cerrada Calefactada (>=80°C)" if mat_key == "ABS" else "Abierta o Cerrada sin calentador"
        }

    def getRecommendedSpeed(self, material: str, printer: str) -> Dict[str, Any]:
        mat_key = str(material).upper().strip()
        is_direct = printer in ["Creality K1 Max", "Ender 3 V3 KE"]
        
        mat_data = self.mgr.get_material_data(mat_key)
        profile = mat_data.get("printer_profiles", {}).get("DirectDrive" if is_direct else "Bowden", {})
        
        return {
            "recommended_print_speed_mm_s": profile.get("max_print_speed_mm_s", 40.0),
            "max_travel_speed_mm_s": 150.0 if is_direct else 80.0,
            "retraction_distance_mm": profile.get("retraction_distance_mm", 1.5)
        }

    def getOptimalLayerHeight(self, material: str, nozzle_diameter: float) -> Dict[str, Any]:
        # Rule of thumb: layer height should be 25% to 75% of nozzle diameter
        min_lh = round(nozzle_diameter * 0.25, 2)
        max_lh = round(nozzle_diameter * 0.75, 2)
        opt_lh = round(nozzle_diameter * 0.50, 2)
        
        return {
            "min_layer_height_mm": min_lh,
            "max_layer_height_mm": max_lh,
            "optimal_layer_height_mm": opt_lh,
            "rationale": f"Para una boquilla de {nozzle_diameter} mm, una altura de capa de {opt_lh} mm proporciona la mejor fusión intercapa sin sacrificar resolución geométrica."
        }

_engine_instance = None

def get_material_intelligence_engine() -> MaterialIntelligenceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MaterialIntelligenceEngine()
    return _engine_instance
