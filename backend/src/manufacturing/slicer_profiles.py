import json

def generate_orca_profile(settings: dict, printer_name: str, material: str) -> dict:
    return {
        "type": "orca_slicer_profile",
        "name": f"MaterialForge_{material.upper()}_{printer_name.replace(' ', '_')}",
        "inherits": printer_name,
        "settings": {
            "default_print_speed": settings["recommended_speed_mms"],
            "inner_wall_speed": max(15.0, settings["recommended_speed_mms"] * 0.9),
            "outer_wall_speed": max(15.0, settings["recommended_speed_mms"] * 0.7),
            "layer_height": settings["recommended_layer_height_mm"],
            "wall_generator": "classic",
            "wall_sequence": "inner_outer" if settings["wall_ordering_strategy"] == "Inner-Outer" else "outer_inner",
            "enable_cooling": settings["cooling_fan_percentage"] > 0,
            "fan_cooling_percent": settings["cooling_fan_percentage"],
            "flow_ratio": settings["flow_multiplier"],
            "retraction_length": settings["retraction_distance_mm"],
            "retraction_speed": settings["retraction_speed_mms"]
        }
    }

def generate_cura_profile(settings: dict, printer_name: str, material: str) -> dict:
    return {
        "type": "cura_profile",
        "metadata": {
            "name": f"MaterialForge {material.upper()} ({printer_name})",
            "printer": printer_name,
            "quality": "custom"
        },
        "properties": {
            "speed_print": settings["recommended_speed_mms"],
            "speed_wall_0": max(15.0, settings["recommended_speed_mms"] * 0.7),
            "speed_wall_x": max(15.0, settings["recommended_speed_mms"] * 0.9),
            "layer_height": settings["recommended_layer_height_mm"],
            "outer_before_inner": settings["wall_ordering_strategy"] == "Outer-Inner",
            "cool_fan_enabled": settings["cooling_fan_percentage"] > 0,
            "cool_fan_speed": settings["cooling_fan_percentage"],
            "material_flow": settings["flow_multiplier"] * 100.0,
            "retraction_amount": settings["retraction_distance_mm"],
            "retraction_speed": settings["retraction_speed_mms"]
        }
    }

def generate_prusa_profile(settings: dict, printer_name: str, material: str) -> dict:
    return {
        "type": "prusa_slicer_profile",
        "name": f"MaterialForge {material.upper()} - {printer_name}",
        "config": {
            "perimeter_speed": settings["recommended_speed_mms"],
            "external_perimeter_speed": max(15.0, settings["recommended_speed_mms"] * 0.7),
            "layer_height": settings["recommended_layer_height_mm"],
            "fill_density": f"{settings.get('infill_density', 30)}%",
            "fan_always_on": 1 if settings["cooling_fan_percentage"] > 0 else 0,
            "max_fan_speed": settings["cooling_fan_percentage"],
            "extrusion_multiplier": settings["flow_multiplier"],
            "retract_length": settings["retraction_distance_mm"],
            "retract_speed": settings["retraction_speed_mms"]
        }
    }
