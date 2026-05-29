import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from .domain_guard import DomainGuard

MODELS_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/models")

FEATURES_CAT = ["material", "material_family", "manufacturing_process", "test_type", "infill_pattern", "load_orientation", "topology"]
FEATURES_NUM = [
    "layer_height_mm", "wall_thickness_mm", "infill_density_percent", 
    "nozzle_temperature_C", "bed_temperature_C", "print_speed_mm_s",
    "fan_speed_percent", "nozzle_diameter_mm", "print_orientation_deg",
    "cell_size_mm", "strut_diameter_mm", "relative_density_percent",
    "porosity_percent", "hybrid_ratio", "post_curing_time_min",
    "post_curing_temperature_C"
]
ALL_FEATURES = FEATURES_CAT + FEATURES_NUM

# Dictionary of target display names and units
TARGET_METRICS_INFO = {
    "max_stress_MPa": {"name": "Esfuerzo Máximo", "unit": "MPa"},
    "young_modulus_MPa": {"name": "Módulo de Young", "unit": "MPa"},
    "failure_strain": {"name": "Deformación de Rotura", "unit": "mm/mm"},
    "energy_density_MJ_m3": {"name": "Densidad de Energía Absorbida", "unit": "MJ/m³"},
    "specific_energy_absorption_kJ_kg": {"name": "Absorción de Energía Específica (SEA)", "unit": "kJ/kg"},
    "compressive_strength_MPa": {"name": "Resistencia a la Compresión", "unit": "MPa"},
    "ultimate_tensile_strength_MPa": {"name": "Resistencia a la Tracción", "unit": "MPa"},
    "plateau_stress_MPa": {"name": "Esfuerzo Plateau", "unit": "MPa"},
    "crushing_force_efficiency": {"name": "Eficiencia de Fuerza de Aplastamiento (CFE)", "unit": "%"}
}

class Predictor:
    def __init__(self):
        self.domain_guard = DomainGuard()

    @property
    def models(self):
        from .model_manager import get_model_manager
        return get_model_manager().get_model()

    def load_models(self):
        """Lazy loader fallback."""
        return self.models

    def reload(self):
        from .model_manager import get_model_manager
        get_model_manager().reload_model()
        self.domain_guard.load_training_bounds()

    def predict_mechanical_properties(self, payload: dict) -> dict:
        """
        Predicts mechanical properties with confidence intervals based on input print/lattice parameters.
        """
        # 1. Domain Guard Check
        warnings, confidence_level = self.domain_guard.validate_parameters(payload)

        # 2. Heuristic fallback if models not loaded
        if not self.models:
            print("Predictor: running with heuristic fallbacks.")
            infill = float(payload.get("infill_density_percent", 35.0))
            mat = str(payload.get("material", "pla")).lower()
            test_t = str(payload.get("test_type", "tensile")).lower()

            # Mock predictions
            predictions_out = {}
            for target, info in TARGET_METRICS_INFO.items():
                if "stress" in target or "strength" in target:
                    val = 25.4 + (infill * 0.3)
                    if "compressive" in target and test_t != "compression":
                        val = 0.0
                    elif "tensile" in target and test_t != "tensile":
                        val = 0.0
                elif "modulus" in target:
                    val = 1500.0 if mat == "pla" else 80.0
                    val += infill * 5.0
                elif "strain" in target:
                    val = 0.05 + (infill * 0.001)
                elif "energy" in target or "sea" in target:
                    val = 5.0 + (infill * 0.1)
                elif "efficiency" in target:
                    val = 0.65 if test_t == "compression" else 0.0
                else:
                    val = 10.0

                predictions_out[target] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "value": float(val),
                    "interval": [float(val * 0.85), float(val * 1.15)]
                }

            return {
                "predictions": predictions_out,
                "confidenceScore": 0.50 if confidence_level == "HIGH" else 0.20,
                "confidenceLevel": confidence_level,
                "modelUsed": "Python_Heuristic_Fallback",
                "warnings": warnings
            }

        # 3. Model predictions
        # Format payload into DataFrame
        df_in = pd.DataFrame([{
            "material": str(payload.get("material", "pla")).lower(),
            "material_family": str(payload.get("material_family", "pla")).lower(),
            "manufacturing_process": str(payload.get("manufacturing_process", "fdm")).lower(),
            "test_type": str(payload.get("test_type", "tensile")).lower(),
            "layer_height_mm": float(payload.get("layer_height_mm", 0.2)),
            "wall_thickness_mm": float(payload.get("wall_thickness_mm", 1.2)),
            "infill_density_percent": float(payload.get("infill_density_percent", 35.0)),
            "infill_pattern": str(payload.get("infill_pattern", "gyroid")).lower(),
            "nozzle_temperature_C": float(payload.get("nozzle_temperature_C", 210.0)),
            "bed_temperature_C": float(payload.get("bed_temperature_C", 60.0)),
            "print_speed_mm_s": float(payload.get("print_speed_mm_s", 50.0)),
            "fan_speed_percent": float(payload.get("fan_speed_percent", 100.0)),
            "nozzle_diameter_mm": float(payload.get("nozzle_diameter_mm", 0.4)),
            "print_orientation_deg": float(payload.get("print_orientation_deg", 0.0)),
            "load_orientation": str(payload.get("load_orientation", "flat")).lower(),
            "topology": str(payload.get("topology", "gyroid")).lower(),
            "cell_size_mm": float(payload.get("cell_size_mm", 8.0)),
            "strut_diameter_mm": float(payload.get("strut_diameter_mm", 0.0)),
            "relative_density_percent": float(payload.get("relative_density_percent", 35.0)),
            "porosity_percent": float(payload.get("porosity_percent", 65.0)),
            "hybrid_ratio": float(payload.get("hybrid_ratio", 0.0)),
            "post_curing_time_min": float(payload.get("post_curing_time_min", 0.0)),
            "post_curing_temperature_C": float(payload.get("post_curing_temperature_C", 0.0))
        }])

        predictions_out = {}
        confidence_score = 0.92 if confidence_level == "HIGH" else 0.45

        for target, info in TARGET_METRICS_INFO.items():
            if target not in self.models:
                # Target not trained (e.g. not enough data)
                predictions_out[target] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "value": None,
                    "interval": [None, None]
                }
                continue

            try:
                pipe = self.models[target]
                preprocessor = pipe["preprocessor"]
                ensemble = pipe["ensemble"]

                # Run preprocessor
                X_trans = preprocessor.transform(df_in)

                # Predict
                mean_pred, p10, p90 = ensemble.predict(X_trans)
                
                # Check for physical consistency (e.g. force/stress cannot be negative)
                val = max(0.0, float(mean_pred[0]))
                val_p10 = max(0.0, float(p10[0]))
                val_p90 = max(0.0, float(p90[0]))

                # Adjust for target specific test_type conditions (e.g. compressive strength is 0 in tensile test)
                test_type = str(payload.get("test_type", "tensile")).lower()
                if "compressive" in target and test_type != "compression":
                    val, val_p10, val_p90 = 0.0, 0.0, 0.0
                elif "tensile" in target and test_type != "tensile":
                    val, val_p10, val_p90 = 0.0, 0.0, 0.0
                elif "efficiency" in target and test_type != "compression":
                    val, val_p10, val_p90 = 0.0, 0.0, 0.0

                # Formulate percentage unit display
                if info["unit"] == "%" and val <= 1.0:
                    val *= 100.0
                    val_p10 *= 100.0
                    val_p90 *= 100.0

                predictions_out[target] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "value": val,
                    "interval": [val_p10, val_p90]
                }
            except Exception as e:
                print(f"Predictor: error predicting {target}: {e}")
                predictions_out[target] = {
                    "name": info["name"],
                    "unit": info["unit"],
                    "value": None,
                    "interval": [None, None]
                }

        return {
            "predictions": predictions_out,
            "confidenceScore": confidence_score,
            "confidenceLevel": confidence_level,
            "modelUsed": "XGBoost_Bootstrap_Ensemble",
            "warnings": warnings
        }
