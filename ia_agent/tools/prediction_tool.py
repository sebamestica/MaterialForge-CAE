import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add workspace to path
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from backend.src.ml.predict import Predictor
    PREDICTOR_AVAILABLE = True
except ImportError as e:
    print(f"PredictionTool: failed to import backend Predictor: {e}")
    PREDICTOR_AVAILABLE = False

from .physics_calculator import PhysicsCalculator

class PredictionTool:
    def __init__(self):
        self.predictor = Predictor() if PREDICTOR_AVAILABLE else None

    def predict_mechanical_response(self, config: Dict[str, Any], target_objective: str = "balance") -> Dict[str, Any]:
        """
        Runs the predictive model for the input config parameters.
        Returns a dictionary conforming to the PredictionReport schema structure.
        """
        material = str(config.get("material", "pla")).lower()
        test_type = str(config.get("testType", config.get("test_type", "compression"))).lower()
        infill = float(config.get("infill", config.get("infill_density_percent", 35.0)))
        pattern = str(config.get("pattern", config.get("infill_pattern", "gyroid"))).lower()
        cell_size = float(config.get("cellSize", config.get("cell_size_mm", 8.0)))
        wall_t = float(config.get("wallThickness", config.get("wall_thickness_mm", 1.2)))
        layer_h = float(config.get("layerHeight", config.get("layer_height_mm", 0.2)))
        speed = float(config.get("printSpeed", config.get("print_speed_mm_s", 50.0)))
        
        # Calculate volume
        dim_x = float(config.get("dimX", 5.0))
        dim_y = float(config.get("dimY", 5.0))
        dim_z = float(config.get("dimZ", 5.0))
        shape_type = str(config.get("shapeType", "Cubo"))
        
        volume = PhysicsCalculator.calculate_volume(shape_type, dim_x, dim_y, dim_z)
        estimated_mass = PhysicsCalculator.estimate_mass(volume, infill, material, wall_t)

        if not self.predictor or not self.predictor.models:
            # Fallback heuristic prediction if model files are missing
            print("PredictionTool: predictor not available. Using rule-based fallback.")
            
            # Simple heuristic calculations
            young_modulus = 1500.0 if material == "pla" else 80.0
            young_modulus += infill * 5.0
            
            max_stress = 20.0 + (infill * 0.3)
            energy_dens = 4.0 + (infill * 0.08)
            sea = energy_dens / 1.24
            
            return {
                "predicted_max_stress_MPa": round(max_stress, 2),
                "predicted_young_modulus_MPa": round(young_modulus, 2),
                "predicted_energy_density_MJ_m3": round(energy_dens, 2),
                "predicted_specific_energy_absorption_kJ_kg": round(sea, 2),
                "predicted_mass_g": estimated_mass,
                "confidence": 0.50,
                "confidence_level": "LOW",
                "warnings": ["Predicciones basadas en reglas heurísticas. Modelos ML no disponibles."],
                "model_used": "Heuristic_Fallback_Proxy"
            }

        # Build payload matching the ML predictor fields
        pred_payload = {
            "material": material,
            "test_type": test_type,
            "layer_height_mm": layer_h,
            "wall_thickness_mm": wall_t,
            "infill_density_percent": infill,
            "infill_pattern": pattern,
            "nozzle_temperature_C": 210.0 if material == "pla" else 230.0,
            "bed_temperature_C": 60.0,
            "print_speed_mm_s": speed,
            "print_orientation_deg": 0.0,
            "cell_size_mm": cell_size
        }

        try:
            res = self.predictor.predict_mechanical_properties(pred_payload)
            preds = res.get("predictions", {})
            
            # Helper to extract dict values safely
            def get_val(target_key):
                if target_key in preds:
                    return preds[target_key].get("value")
                return None
                
            return {
                "predicted_max_stress_MPa": get_val("max_stress_MPa"),
                "predicted_young_modulus_MPa": get_val("young_modulus_MPa"),
                "predicted_energy_density_MJ_m3": get_val("energy_density_MJ_m3"),
                "predicted_specific_energy_absorption_kJ_kg": get_val("specific_energy_absorption_kJ_kg"),
                "predicted_mass_g": estimated_mass,
                "confidence": res.get("confidenceScore", 0.90),
                "confidence_level": res.get("confidenceLevel", "HIGH"),
                "warnings": [w.get("text", w) if isinstance(w, dict) else w for w in res.get("warnings", [])],
                "model_used": res.get("modelUsed", "XGBoost_Bootstrap_Ensemble")
            }
        except Exception as e:
            print(f"PredictionTool: prediction runtime error: {e}")
            return {
                "predicted_max_stress_MPa": None,
                "predicted_young_modulus_MPa": None,
                "predicted_energy_density_MJ_m3": None,
                "predicted_specific_energy_absorption_kJ_kg": None,
                "predicted_mass_g": estimated_mass,
                "confidence": 0.10,
                "confidence_level": "LOW",
                "warnings": [f"Error de inferencia: {str(e)}"],
                "model_used": "Error_Fallback"
            }
