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

