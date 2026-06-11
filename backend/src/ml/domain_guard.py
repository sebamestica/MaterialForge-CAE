import os
import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

class DomainGuard:
    def __init__(self):
        self.bounds = {}
        self.known_categorical = {}
        self._loaded = False

    def load_training_bounds(self):
        """Loads bounds and unique values from training_table.parquet."""
        if self._loaded:
            return
        self._loaded = True
        training_table_path = PROCESSED_DIR / "training_table.parquet"
        if not training_table_path.exists():
            print("DomainGuard: training table not found. Using default bounds.")
            # Set generic default bounds as fallback
            self.bounds = {
                "layer_height_mm": (0.02, 0.4),
                "infill_density_percent": (5.0, 100.0),
                "nozzle_temperature_C": (190.0, 260.0),
                "print_speed_mm_s": (30.0, 150.0),
                "wall_thickness_mm": (0.4, 10.0),
                "cell_size_mm": (1.0, 15.0),
                "print_orientation_deg": (0.0, 90.0),
                "post_curing_time_min": (0.0, 120.0)
            }
            self.known_categorical = {
                "material": ["pla", "carbon-pla", "abs", "fluoroelastomer", "tpu"],
                "infill_pattern": ["gyroid", "honeycomb", "triply_periodic", "grid", "triangular", "solid", "tpms_graded"]
            }
            return

        try:
            df = pd.read_parquet(training_table_path)
            
            # Numeric bounds
            numeric_cols = [
                "layer_height_mm", "wall_thickness_mm", "infill_density_percent", 
                "nozzle_temperature_C", "bed_temperature_C", "print_speed_mm_s",
                "fan_speed_percent", "nozzle_diameter_mm", "print_orientation_deg",
                "cell_size_mm", "strut_diameter_mm", "relative_density_percent",
                "porosity_percent", "hybrid_ratio", "post_curing_time_min",
                "post_curing_temperature_C"
            ]
            for col in numeric_cols:
                if col in df.columns:
                    valid_vals = df[col].dropna()
                    if not valid_vals.empty:
                        self.bounds[col] = (float(valid_vals.min()), float(valid_vals.max()))

            # Categorical unique values
            cat_cols = ["material", "infill_pattern", "topology", "test_type"]
            for col in cat_cols:
                if col in df.columns:
                    self.known_categorical[col] = [str(x).lower().strip() for x in df[col].dropna().unique()]

            # Ensure TPU and tpms_graded are registered as valid categories
            if "material" in self.known_categorical:
                if "tpu" not in self.known_categorical["material"]:
                    self.known_categorical["material"].append("tpu")
            else:
                self.known_categorical["material"] = ["pla", "carbon-pla", "abs", "fluoroelastomer", "tpu"]

            if "infill_pattern" in self.known_categorical:
                if "tpms_graded" not in self.known_categorical["infill_pattern"]:
                    self.known_categorical["infill_pattern"].append("tpms_graded")
            else:
                self.known_categorical["infill_pattern"] = ["gyroid", "honeycomb", "triply_periodic", "grid", "triangular", "solid", "tpms_graded"]

        except Exception as e:
            print(f"DomainGuard: error loading bounds: {e}")

    def validate_parameters(self, payload: dict) -> tuple:
        """
        Validates payload parameters.
        Returns (warnings_list, confidence_level).
        """
        self.load_training_bounds()
        warnings = []
        is_extrapolating = False

        # Check numeric parameters
        numeric_checks = {
            "layer_height_mm": payload.get("layer_height_mm"),
            "wall_thickness_mm": payload.get("wall_thickness_mm"),
            "infill_density_percent": payload.get("infill_density_percent"),
            "nozzle_temperature_C": payload.get("nozzle_temperature_C"),
            "print_speed_mm_s": payload.get("print_speed_mm_s"),
            "cell_size_mm": payload.get("cell_size_mm"),
            "print_orientation_deg": payload.get("print_orientation_deg"),
            "post_curing_time_min": payload.get("post_curing_time_min")
        }

        for param, val in numeric_checks.items():
            if val is not None and param in self.bounds:
                min_v, max_v = self.bounds[param]
                # Allow a tiny tolerance
                if val < min_v - 1e-5 or val > max_v + 1e-5:
                    is_extrapolating = True
                    warnings.append({
                        "code": f"W_EXTRAPOLATION_{param.upper()}",
                        "severity": "high",
                        "text": f"El parámetro '{param}' ({val}) está fuera del dominio experimental de entrenamiento [{min_v:.2f}, {max_v:.2f}]."
                    })

        # Check categorical parameters
        material = str(payload.get("material", "")).lower().strip()
        if material and "material" in self.known_categorical:
            known_mats = self.known_categorical["material"]
            if material not in known_mats:
                is_extrapolating = True
                warnings.append({
                    "code": "W_UNKNOWN_MATERIAL",
                    "severity": "high",
                    "text": f"Material '{material}' desconocido. Los materiales conocidos son: {', '.join(known_mats)}."
                })

        pattern = str(payload.get("infill_pattern", payload.get("topology", ""))).lower().strip()
        if pattern and "infill_pattern" in self.known_categorical:
            known_patterns = self.known_categorical["infill_pattern"]
            if pattern not in known_patterns:
                is_extrapolating = True
                warnings.append({
                    "code": "W_UNKNOWN_PATTERN",
                    "severity": "high",
                    "text": f"Patrón de infill '{pattern}' desconocido. Los patrones conocidos son: {', '.join(known_patterns)}."
                })

        confidence = "HIGH" if not is_extrapolating else "LOW"
        return warnings, confidence
