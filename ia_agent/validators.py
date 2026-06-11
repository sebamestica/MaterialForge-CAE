import re
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
        if pat_lower.endswith("_tpms"):
            pat_lower = pat_lower[:-5]
            merged["pattern"] = pat_lower
            if "pattern" in config_patch:
                corrected_patch["pattern"] = pat_lower
        allowed_pats = ["gyroid", "honeycomb", "triply_periodic", "grid", "diamond", "lidinoid", "split_p", "neovius", "iwp"]
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
    
    # Enforce weight limit of 100g by automatically scaling down infill and wall thickness
    original_mass = estimated_mass_g
    if estimated_mass_g > 100.0:
        corrected_infill = infill_val
        corrected_wall = wall_t_val
        
        # 1. Reduce infill first (down to a minimum of 10.0%)
        while corrected_infill > 10.0 and estimated_mass_g > 100.0:
            corrected_infill = max(10.0, corrected_infill - 1.0)
            estimated_mass_g = PhysicsCalculator.estimate_mass(volume_cm3, corrected_infill, mat_val, corrected_wall)
            
        # 2. If still > 100.0g, reduce wall thickness (down to a minimum of 1.2mm)
        while corrected_wall > 1.2 and estimated_mass_g > 100.0:
            corrected_wall = max(1.2, corrected_wall - 0.1)
            estimated_mass_g = PhysicsCalculator.estimate_mass(volume_cm3, corrected_infill, mat_val, corrected_wall)
            
        # 3. If still > 100.0g, reduce infill down to 5.0%
        while corrected_infill > 5.0 and estimated_mass_g > 100.0:
            corrected_infill = max(5.0, corrected_infill - 1.0)
            estimated_mass_g = PhysicsCalculator.estimate_mass(volume_cm3, corrected_infill, mat_val, corrected_wall)
            
        # 4. If still > 100.0g, reduce wall thickness down to 0.8mm
        while corrected_wall > 0.8 and estimated_mass_g > 100.0:
            corrected_wall = max(0.8, corrected_wall - 0.1)
            estimated_mass_g = PhysicsCalculator.estimate_mass(volume_cm3, corrected_infill, mat_val, corrected_wall)

        # Update the patch and merged config
        corrected_patch["infill"] = round(corrected_infill, 1)
        corrected_patch["wallThickness"] = round(corrected_wall, 2)
        merged["infill"] = round(corrected_infill, 1)
        merged["wallThickness"] = round(corrected_wall, 2)
        
        warnings.append(
            f"El peso estimado original ({original_mass:.1f} g) superaba el límite de 100.0 g. "
            f"Se ajustaron los parámetros a Infill: {corrected_infill:.1f}%, Pared: {corrected_wall:.2f} mm para cumplir con la restricción."
        )

    # 12. Volume and Mass validation checks
    if volume_cm3 > 125.0:
        errors.append(f"El volumen de la pieza ({volume_cm3:.1f} cm³) supera el límite de 125.0 cm³ (5x5x5 cm).")
        
    if estimated_mass_g > 100.0:
        errors.append(f"El peso estimado de la pieza ({estimated_mass_g:.1f} g) supera el límite máximo de 100.0 g incluso tras la optimización.")

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

def sanitize_input_text(text: str) -> str:
    """
    Sanitizes user input text by removing/escaping dangerous characters and limiting length.
    """
    if not text:
        return ""
    
    # 1. Truncate length to avoid context overflow / DOS (max 1000 characters)
    text = text[:1000]
    
    # 2. Strip basic HTML tags (like <script>, <iframe>, <style>, etc.)
    text = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", text, flags=re.IGNORECASE)
    
    # Strip any general HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # 3. Escape potential control characters
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    return text.strip()

def detect_malicious_input(text: str) -> Tuple[bool, str]:
    """
    Scans the text for potential prompt injection, command injection, or executable scripts.
    Returns (is_malicious, warning_message).
    """
    if not text:
        return False, ""
        
    t = text.lower()
    
    # 1. System Prompt Injection / Jailbreak signatures
    injection_patterns = [
        "ignore previous instructions",
        "ignore all prior instructions",
        "olvida las instrucciones anteriores",
        "ignora las instrucciones anteriores",
        "reveal system prompt",
        "revelar prompt de sistema",
        "revelar instrucciones",
        "show system prompt",
        "system prompt bypass",
        "forget your rules",
        "olvida tus reglas",
        "act as a developer mode",
        "jailbreak",
        "system prompt:"
    ]
    
    for pat in injection_patterns:
        if pat in t:
            return True, "Intento de elusión de directivas del sistema detectado (Prompt Injection)."
            
    # 2. Executable code/scripts signatures
    os_commands = [
        "rm -rf", "format c:", "del /s", "mkfs", "chown", "chmod", "shutdown",
        "subprocess.run", "subprocess.call", "os.system", "shutil.rmtree",
        "popen", "pty.spawn", "/bin/sh", "/bin/bash", "cmd.exe", "powershell.exe"
    ]
    for cmd in os_commands:
        if cmd in t:
            return True, f"Intento de ejecución de comando del sistema detectado ({cmd})."
            
    # Check for script injection patterns (Python, JavaScript, etc.)
    script_patterns = [
        r"import\s+(os|sys|subprocess|shutil|socket|urllib|requests|builtins)",
        r"from\s+(os|sys|subprocess|shutil|socket|urllib|requests)\s+import",
        r"eval\s*\(", r"exec\s*\(", r"__import__", r"getattr\s*\(", r"open\s*\(",
        r"eval\(\s*__import__",
        r"javascript\s*:", r"onload\s*=", r"onerror\s*=", r"onclick\s*="
    ]
    for pattern in script_patterns:
        if re.search(pattern, t):
            return True, "Intento de inyección de script o código ejecutable detectado."
            
    return False, ""
