import sys
from pathlib import Path
from typing import Dict, Any

# Add workspace to path
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

try:
    from backend.src.ml.predict import run_unified_prediction_service
    PREDICTOR_AVAILABLE = True
except ImportError:
    PREDICTOR_AVAILABLE = False

class PredictionTool:
    def predict_mechanical_response(self, config: Dict[str, Any], target_objective: str = "balance") -> Dict[str, Any]:
        """
        Runs the predictive model for the input config parameters using the unified backend service.
        Returns a dictionary conforming to the PredictionReport schema structure.
        """
        if not PREDICTOR_AVAILABLE:
            return {
                "predicted_max_stress_MPa": 15.0,
                "predicted_young_modulus_MPa": 800.0,
                "predicted_energy_density_MJ_m3": 0.5,
                "predicted_specific_energy_absorption_kJ_kg": 2.0,
                "predicted_mass_g": 35.0,
                "confidence": 0.3,
                "confidence_level": "LOW",
                "warnings": ["Prediction tool heuristic fallback"],
                "model_used": "Heuristic Rule Fallback"
            }

        from backend.src.ml.predict import run_unified_prediction_service
        
        # Invoke the single source of truth
        data = run_unified_prediction_service(config)
        
        return {
            "predicted_max_stress_MPa": data["strength_MPa"],
            "predicted_young_modulus_MPa": data["modulus_MPa"],
            "predicted_energy_density_MJ_m3": data["energy_density_MJ_m3"],
            "predicted_specific_energy_absorption_kJ_kg": data["sea_kJ_kg"],
            "predicted_mass_g": data["mass_g"],
            "confidence": data["confidence"],
            "confidence_level": "HIGH" if data["confidence"] > 0.70 else "LOW",
            "warnings": [w.get("text", w) if isinstance(w, dict) else str(w) for w in data["warnings"]],
            "model_used": data["model_used"]
        }
