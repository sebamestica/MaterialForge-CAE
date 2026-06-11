import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add workspace to path
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from backend.src.ml.domain_guard import DomainGuard as BackendDomainGuard
    GUARD_AVAILABLE = True
except ImportError as e:
    print(f"DomainGuardTool: failed to import backend DomainGuard: {e}")
    GUARD_AVAILABLE = False

class DomainGuardTool:
    def __init__(self):
        self.guard = BackendDomainGuard() if GUARD_AVAILABLE else None

    def validate_config(self, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
        """
        Validates parameters against training dataset boundaries.
        Returns (warnings_list, confidence_level).
        """
        # Format input config keys to match DomainGuard expected names
        infill = float(config.get("infill", config.get("infill_density_percent", 35.0)))
        # Handle material dict or string
        m = config.get("material", "pla")
        if isinstance(m, dict):
            material = str(m.get("type", "pla")).lower().strip()
        else:
            material = str(m).lower().strip()
            
        # Handle pattern dict or string
        p = config.get("pattern", config.get("infill_pattern", "gyroid"))
        if isinstance(p, dict):
            pattern = str(p.get("type", "gyroid")).lower().strip()
        else:
            pattern = str(p).lower().strip()
            
        if pattern.endswith("_tpms"):
            pattern = pattern[:-5]
        wall_t = float(config.get("wallThickness", config.get("wall_thickness_mm", 1.2)))
        layer_h = float(config.get("layerHeight", config.get("layer_height_mm", 0.2)))
        speed = float(config.get("printSpeed", config.get("print_speed_mm_s", 50.0)))
        cell_size = float(config.get("cellSize", config.get("cell_size_mm", 8.0)))
        
        payload = {
            "material": material,
            "infill_pattern": pattern,
            "infill_density_percent": infill,
            "layer_height_mm": layer_h,
            "wall_thickness_mm": wall_t,
            "print_speed_mm_s": speed,
            "cell_size_mm": cell_size,
            "print_orientation_deg": 0.0,
            "post_curing_time_min": 0.0
        }

        if not self.guard:
            # Fallback checks if the backend guard is missing
            warnings = []
            is_extrapolating = False
            
            # Rough training boundaries
            if infill < 10.0 or infill > 100.0:
                is_extrapolating = True
                warnings.append({
                    "code": "W_EXTRAPOLATION_INFILL",
                    "severity": "high",
                    "text": f"El infill ({infill}%) está fuera del dominio experimental de entrenamiento [10.0, 100.0]."
                })
            
            known_materials = ["pla", "tpu", "abs", "petg", "carbon-pla"]
            if material not in known_materials:
                is_extrapolating = True
                warnings.append({
                    "code": "W_UNKNOWN_MATERIAL",
                    "severity": "high",
                    "text": f"Material '{material}' desconocido. Los materiales entrenados son: {', '.join(known_materials)}."
                })

            confidence = "LOW" if is_extrapolating else "HIGH"
            return warnings, confidence

        try:
            return self.guard.validate_parameters(payload)
        except Exception as e:
            print(f"DomainGuardTool: validation runtime error: {e}")
            return [{"code": "W_GUARD_ERROR", "severity": "medium", "text": str(e)}], "LOW"
