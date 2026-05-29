from typing import Dict, Any, List

class LiteratureRulesEngine:
    def __init__(self, literature_summary: Dict[str, Any]):
        self.summary = literature_summary

    def evaluate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a print configuration against the rules and heuristics compiled from papers.
        Returns:
            {
                "is_compliant": bool,
                "score_structural_modifier": float, # e.g. positive/negative impact
                "score_printability_modifier": float,
                "warnings": List[str],
                "recommendations": List[str]
            }
        """
        warnings = []
        recommendations = []
        structural_mod = 0.0
        printability_mod = 0.0

        material = str(config.get("material", "PLA")).upper().strip()
        pattern = str(config.get("pattern", config.get("infill_pattern", "gyroid"))).lower().strip()
        infill = float(config.get("infill", config.get("infill_density_percent", 35.0)))
        wall_t = float(config.get("wallThickness", config.get("wall_thickness_mm", 1.2)))
        speed = float(config.get("printSpeed", config.get("print_speed_mm_s", 50.0)))
        nozzle_t = float(config.get("nozzleTemp", config.get("nozzle_temperature_C", 210.0)))
        layer_h = float(config.get("layerHeight", config.get("layer_height_mm", 0.2)))
        orientation = str(config.get("orientation", config.get("print_orientation", "Isotrópica"))).lower()

        # Rules for TPU
        if material == "TPU":
            # 1. Print Speed check
            if speed > 35.0:
                warnings.append(
                    f"Velocidad de impresión ({speed} mm/s) alta para TPU. La literatura indica que velocidades superiores a 35 mm/s "
                    f"aumentan el riesgo de subextrusión, delaminación interlaminar y fallas estructurales."
                )
                printability_mod -= 15.0
                structural_mod -= 10.0
            else:
                recommendations.append("Velocidad de impresión (20-35 mm/s) óptima para TPU, promoviendo buena adherencia y estabilidad elástica.")
                printability_mod += 5.0
                structural_mod += 5.0

            # 2. Nozzle Temperature check
            if nozzle_t < 220.0 or nozzle_t > 235.0:
                warnings.append(
                    f"Temperatura de boquilla ({nozzle_t} °C) fuera del rango óptimo para TPU estructural (220-235 °C). "
                    f"Una temperatura muy baja debilita la adhesión entre capas (interlayer bonding), y muy alta degrada el polímero."
                )
                structural_mod -= 12.0
            else:
                recommendations.append("Temperatura de boquilla en el rango recomendado de 220-235 °C, optimizando la resistencia interlaminar.")
                structural_mod += 8.0

            # 3. Infill Density check for compression
            if infill < 55.0:
                warnings.append(
                    f"Densidad de infill ({infill}%) baja para compresión extrema. La literatura recomienda infill "
                    f"entre 55% y 80% para evitar el colapso prematuro (buckling) del núcleo elástico en TPU."
                )
                structural_mod -= 15.0
            elif infill > 80.0:
                warnings.append(
                    f"Densidad de infill ({infill}%) alta. Exceder el 80% puede saturar la estructura, reduciendo la "
                    f"capacidad de deformación controlada específica y aumentando el riesgo de fallas de sobreextrusión."
                )
                structural_mod += 5.0
                printability_mod -= 10.0
            else:
                recommendations.append(f"Infill ({infill}%) adecuado en rango estructural (55-80%) para compresión y disipación progresiva.")
                structural_mod += 10.0

            # 4. Pattern check
            if pattern == "gyroid":
                recommendations.append("Patrón Gyroid (TPMS continuo) recomendado para TPU. Distribuye esfuerzos de forma isotrópica y disipa impacto eficientemente.")
                structural_mod += 12.0
                printability_mod += 5.0
            elif pattern == "honeycomb":
                warnings.append("Patrón Honeycomb (Nido de Abeja) no recomendado para TPU bajo cargas elásticas cíclicas. Las celdas colapsan por pandeo localizado severo.")
                structural_mod -= 10.0
            elif pattern == "triply_periodic":
                recommendations.append("Estructura Schwarz P (TPMS) apropiada para rigidez a compresión axial, aunque tiene debilidad cortante.")
                structural_mod += 5.0

            # 5. Shell Thickness check
            if wall_t < 1.6:
                warnings.append(
                    f"Espesor de pared ({wall_t} mm) insuficiente. Para compresión estructural extrema en TPU, la literatura "
                    f"recomienda perímetros reforzados de 1.6 mm a 2.4 mm para prevenir el colapso de las caras externas."
                )
                structural_mod -= 10.0
            else:
                recommendations.append(f"Espesor de pared ({wall_t} mm) adecuado para prevenir pandeo lateral periférico.")
                structural_mod += 8.0

            # 6. Orientation check
            if "anisotrópica x" in orientation or "anisotrópica y" in orientation:
                warnings.append("Orientación de impresión anisotrópica seleccionada. Esto debilita la resistencia a la compresión vertical.")
                structural_mod -= 10.0

        # Rules for PLA
        elif material == "PLA":
            if pattern == "honeycomb":
                recommendations.append("Honeycomb seleccionado para PLA. Excelente combinación para máxima resistencia y rigidez a compresión pura en el eje vertical Z.")
                structural_mod += 10.0
            elif pattern == "grid":
                warnings.append("Patrón Grid (rectilíneo) propenso a fallas por cizallamiento a 45 grados bajo compresión en materiales rígidos como el PLA.")
                structural_mod -= 8.0

            if wall_t < 1.6:
                warnings.append(f"Espesor de pared ({wall_t} mm) bajo para PLA estructural. Se sugiere >= 1.6 mm para evitar pandeo local frágil.")
                structural_mod -= 8.0
            else:
                structural_mod += 5.0

            if speed > 60.0:
                warnings.append(f"Velocidad de impresión ({speed} mm/s) elevada para PLA estructural, puede reducir la adhesión de capas.")
                printability_mod -= 8.0
                structural_mod -= 5.0

        is_compliant = len(warnings) == 0
        return {
            "is_compliant": is_compliant,
            "score_structural_modifier": round(structural_mod, 1),
            "score_printability_modifier": round(printability_mod, 1),
            "warnings": warnings,
            "recommendations": recommendations
        }
