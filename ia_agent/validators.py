from typing import Dict, Any, List, Tuple
from .tools.physics_calculator import PhysicsCalculator

def validate_config_patch(current_config: Dict[str, Any], config_patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates a config patch against strict physical and slicer boundaries.
    Applies constraints, corrects parameter values if possible, and returns a validation report.
    Returns a dict conforming to the ValidationReport structure:
    {
      "is_valid": bool,
      "errors": List[str],
      "warnings": List[str],
      "estimated_volume_cm3": float,
      "estimated_mass_g": float,
      "limit_report": dict,
      "corrected_patch": dict
    }
    """
    errors = []
    warnings = []
    
    # 1. Merge patch onto a copy of current config
    merged = current_config.copy()
    corrected_patch = {}
    
    for k, v in config_patch.items():
        if v is not None:
            merged[k] = v
            corrected_patch[k] = v

    # 2. Check and enforce hard bounding limits
    dim_keys = ["dimX", "dimY", "dimZ"]
    for key in dim_keys:
        val = merged.get(key)
        if val is not None:
            try:
                val = float(val)
                # Correct if dimensions are out of 1.0 to 5.0 range
                if val > 5.0:
                    corrected_patch[key] = 5.0
                    merged[key] = 5.0
                    warnings.append(f"Se corrigió el límite de '{key}' a 5.0 cm (máximo permitido).")
                elif val < 1.0:
                    corrected_patch[key] = 1.0
                    merged[key] = 1.0
                    warnings.append(f"Se corrigió el límite de '{key}' a 1.0 cm (mínimo permitido).")
            except ValueError:
                errors.append(f"El valor de '{key}' no es un número válido.")

    # 3. Infill density limits [10.0, 100.0]
    infill = merged.get("infill")
    if infill is not None:
        try:
            infill = float(infill)
            if infill > 100.0:
                corrected_patch["infill"] = 100.0
                merged["infill"] = 100.0
                warnings.append("Se redujo el infill a 100% (máximo permitido).")
            elif infill < 10.0:
                corrected_patch["infill"] = 10.0
                merged["infill"] = 10.0
                warnings.append("Se incrementó el infill a 10% (mínimo para prevenir colapso de capa superior).")
        except ValueError:
            errors.append("El valor de 'infill' no es válido.")

    # 4. Print speed [10.0, 150.0]
    print_speed = merged.get("printSpeed")
    if print_speed is not None:
        try:
            print_speed = float(print_speed)
            if print_speed > 150.0:
                corrected_patch["printSpeed"] = 150.0
                merged["printSpeed"] = 150.0
                warnings.append("Se limitó la velocidad a 150 mm/s.")
            elif print_speed < 10.0:
                corrected_patch["printSpeed"] = 10.0
                merged["printSpeed"] = 10.0
                warnings.append("Se incrementó la velocidad a 10 mm/s.")
        except ValueError:
            errors.append("Velocidad de impresión no es válida.")

    # 5. Layer height [0.05, 0.40]
    layer_h = merged.get("layerHeight")
    if layer_h is not None:
        try:
            layer_h = float(layer_h)
            if layer_h > 0.40:
                corrected_patch["layerHeight"] = 0.40
                merged["layerHeight"] = 0.40
                warnings.append("Se limitó la altura de capa a 0.40 mm.")
            elif layer_h < 0.05:
                corrected_patch["layerHeight"] = 0.05
                merged["layerHeight"] = 0.05
                warnings.append("Se incrementó la altura de capa a 0.05 mm.")
        except ValueError:
            errors.append("Altura de capa no es válida.")

    # 6. Wall thickness [0.4, 4.0]
    wall_t = merged.get("wallThickness")
    if wall_t is not None:
        try:
            wall_t = float(wall_t)
            if wall_t > 4.0:
                corrected_patch["wallThickness"] = 4.0
                merged["wallThickness"] = 4.0
                warnings.append("Se limitó el grosor de pared a 4.0 mm.")
            elif wall_t < 0.4:
                corrected_patch["wallThickness"] = 0.4
                merged["wallThickness"] = 0.4
                warnings.append("Se incrementó el grosor de pared a 0.4 mm.")
        except ValueError:
            errors.append("Grosor de pared no es válido.")

    # 7. Cell size [1.0, 10.0]
    cell_size = merged.get("cellSize")
    if cell_size is not None:
        try:
            cell_size = float(cell_size)
            if cell_size > 10.0:
                corrected_patch["cellSize"] = 10.0
                merged["cellSize"] = 10.0
                warnings.append("Se limitó el tamaño de celda a 10.0 mm.")
            elif cell_size < 1.0:
                corrected_patch["cellSize"] = 1.0
                merged["cellSize"] = 1.0
                warnings.append("Se incrementó el tamaño de celda a 1.0 mm.")
        except ValueError:
            errors.append("Tamaño de celda no es válido.")

    # 8. Cell thickness [0.1, 2.0]
    cell_t = merged.get("cellThickness")
    if cell_t is not None:
        try:
            cell_t = float(cell_t)
            if cell_t > 2.0:
                corrected_patch["cellThickness"] = 2.0
                merged["cellThickness"] = 2.0
                warnings.append("Se limitó el espesor de celda a 2.0 mm.")
            elif cell_t < 0.1:
                corrected_patch["cellThickness"] = 0.1
                merged["cellThickness"] = 0.1
                warnings.append("Se incrementó el espesor de celda a 0.1 mm.")
        except ValueError:
            errors.append("Espesor de celda no es válido.")

    # 9. Allowed Materials validation
    material = merged.get("material")
    if material is not None:
        mat_lower = str(material).lower().strip()
        allowed_mats = ["pla", "tpu", "abs", "petg", "carbon-pla"]
        if mat_lower not in allowed_mats:
            errors.append(f"El material '{material}' no está soportado. Use uno de: {', '.join(allowed_mats).upper()}.")

    # 10. Allowed Infill Patterns
    pattern = merged.get("pattern")
    if pattern is not None:
        pat_lower = str(pattern).lower().strip()
        allowed_pats = ["gyroid", "honeycomb", "triply_periodic", "grid"]
        if pat_lower not in allowed_pats:
            errors.append(f"El patrón '{pattern}' no está soportado. Use uno de: {', '.join(allowed_pats)}.")

    # 11. Compute final physical properties
    shape = merged.get("shapeType", "Cubo")
    dim_x = float(merged.get("dimX", 5.0))
    dim_y = float(merged.get("dimY", 5.0))
    dim_z = float(merged.get("dimZ", 5.0))
    infill_val = float(merged.get("infill", 35.0))
    mat_val = str(merged.get("material", "PLA")).lower()
    wall_t_val = float(merged.get("wallThickness", 1.2))
    
    volume_cm3 = PhysicsCalculator.calculate_volume(shape, dim_x, dim_y, dim_z)
    estimated_mass_g = PhysicsCalculator.estimate_mass(volume_cm3, infill_val, mat_val, wall_t_val)
    
    # 12. Volume and Mass validation checks
    if volume_cm3 > 125.0:
        errors.append(f"El volumen de la pieza ({volume_cm3:.1f} cm³) supera el límite de 125.0 cm³ (5x5x5 cm).")
        
    if estimated_mass_g > 100.0:
        errors.append(f"El peso estimado de la pieza ({estimated_mass_g:.1f} g) supera el límite máximo de 100.0 g.")

    # Limit report
    limit_report = {
        "max_dim_cm": 5.0,
        "max_mass_g": 100.0,
        "max_volume_cm3": 125.0,
        "actual_volume_cm3": round(volume_cm3, 2),
        "actual_mass_g": round(estimated_mass_g, 2)
    }

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "estimated_volume_cm3": round(volume_cm3, 2),
        "estimated_mass_g": round(estimated_mass_g, 2),
        "limit_report": limit_report,
        "corrected_patch": corrected_patch
    }
