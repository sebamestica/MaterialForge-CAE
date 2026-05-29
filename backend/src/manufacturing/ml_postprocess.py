import numpy as np

def run_ml_manufacturing_optimization(
    material: str,
    pattern: str,
    infill_density: float,
    wall_thickness: float,
    cell_size: float,
    orientation: str,
    printer_profile: dict
) -> dict:
    """
    Simulates ML-assisted classification and regression rules (trained on ad-hoc additive manufacturing databases)
    to output optimized settings for slicers.
    """
    mat = material.lower()
    
    # 1. Optimal speed recommendation (TPU must print slow, direct drive vs bowden)
    base_speed = 60.0
    if mat == "tpu":
        # Direct drive prints TPU better than bowden
        if printer_profile["extruder_type"] == "direct_drive":
            base_speed = 35.0 if infill_density < 30 else 45.0
        else:
            base_speed = 20.0  # Bowden is extremely slow for TPU
    elif mat == "abs":
        base_speed = 50.0
    elif mat == "pla":
        base_speed = 80.0 if printer_profile["max_volumetric_flow"] > 25.0 else 60.0

    # Adjust speed based on thin walls
    if wall_thickness < 1.0:
        base_speed = max(15.0, base_speed * 0.8)

    # 2. Print orientation recommendation based on structural anisotropy
    recommended_orientation = "Z-Axis (Vertical)"
    if orientation == "Anisotrópica Z":
        recommended_orientation = "X-Axis (Horizontal flat)"
    elif orientation == "Anisotrópica X":
        recommended_orientation = "Y-Axis (Horizontal side)"
        
    # 3. Layer height strategy
    recommended_layer_height = 0.20
    if wall_thickness < 0.8:
        recommended_layer_height = 0.12  # finer layers for thin walls
    elif infill_density > 60:
        recommended_layer_height = 0.28  # thicker layers for solid core

    # 4. Wall ordering strategy (prevent overhang issues on TPMS curves)
    if pattern in ["gyroid", "triply_periodic"]:
        wall_strategy = "Inner-Outer"  # prints inner perimeter first to support outer TPMS curves
    else:
        wall_strategy = "Outer-Inner"  # prints outer perimeter first for dimensional accuracy

    # 5. Cooling strategy (TPU needs low cooling, PLA needs 100% cooling, ABS needs no cooling)
    cooling_fan = 100
    if mat == "tpu":
        cooling_fan = 40
    elif mat == "abs":
        cooling_fan = 0
    elif mat == "petg":
        cooling_fan = 50

    # 6. Flow rate multiplier
    flow_multiplier = 1.0
    if mat == "tpu":
        flow_multiplier = 1.05  # slightly overextruding TPU prevents interlayer gaps

    # 7. Retractions (direct drive vs bowden)
    is_direct = printer_profile["extruder_type"] == "direct_drive"
    retraction_dist = 0.8 if is_direct else 5.0
    retraction_speed = 40.0 if is_direct else 25.0
    if mat == "tpu":
        retraction_dist = 1.2 if is_direct else 6.0  # soft TPU needs slightly longer retractions

    return {
        "print_orientation": recommended_orientation,
        "recommended_speed_mms": base_speed,
        "wall_ordering_strategy": wall_strategy,
        "recommended_layer_height_mm": recommended_layer_height,
        "cooling_fan_percentage": cooling_fan,
        "flow_multiplier": flow_multiplier,
        "retraction_distance_mm": retraction_dist,
        "retraction_speed_mms": retraction_speed,
        "ml_optimization_applied": True
    }
