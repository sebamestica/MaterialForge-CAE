from typing import Dict, Any, List, Optional
from ..data_access.tabular_store import TabularStore

class ConfigRecommenderTool:
    def __init__(self, store: Optional[TabularStore] = None):
        self.store = store or TabularStore()

    def recommend_optimal_patch(
        self, 
        objective: str, 
        material: Optional[str] = None, 
        test_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Recommends parameter updates (a config patch) to optimize the design 
        towards the specified target objective based on experimental data.
        """
        target = "max_stress_MPa"
        obj = objective.lower().strip()
        
        if "energy" in obj or "absorption" in obj:
            target = "energy_density_MJ_m3"
        elif "stiffness" in obj or "modulus" in obj or "young" in obj:
            target = "young_modulus_MPa"
        elif "sea" in obj:
            target = "specific_energy_absorption_kJ_kg"

        # Query best configurations
        best_configs = self.store.get_best_configs_for_target(
            target=target,
            material=material,
            test_type=test_type,
            limit=1
        )

        if not best_configs:
            # Simple rule-based fallbacks if no database data is found
            if "energy" in obj:
                return {
                    "material": "TPU",
                    "infill": 45.0,
                    "pattern": "gyroid",
                    "cellThickness": 1.2
                }
            elif "stiffness" in obj or "strength" in obj:
                return {
                    "material": "PLA",
                    "infill": 50.0,
                    "pattern": "honeycomb",
                    "cellThickness": 0.8
                }
            return {
                "infill": 35.0,
                "pattern": "gyroid"
            }

        rec = best_configs[0]
        
        # Translate to standard camelCase config patch names
        patch = {
            "material": str(rec.get("material", "PLA")).upper(),
            "infill": float(rec.get("infill_density_percent", 35.0)),
            "pattern": str(rec.get("infill_pattern", "gyroid")).lower(),
            "layerHeight": float(rec.get("layer_height_mm", 0.20)),
            "wallThickness": float(rec.get("wall_thickness_mm", 1.20))
        }

        # Clean None values
        return {k: v for k, v in patch.items() if v is not None}
