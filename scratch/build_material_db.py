import os
import json
from pathlib import Path

BASE_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/materials")

def create_db():
    # 1. Define shared data
    shared_data = {
        "anisotropy": {
            "title": "Anisotropía en Fabricación FDM",
            "description": "Reducción de propiedades mecánicas por efecto de laminación y orientación de capa.",
            "transverse_isotropy_coefficients": {
                "PLA": {"xy_modulus_gpa": 3.2, "z_modulus_gpa": 1.62, "shear_modulus_gpa": 0.8, "tensile_xy_mpa": 60, "tensile_z_mpa": 25},
                "TPU": {"xy_modulus_gpa": 0.08, "z_modulus_gpa": 0.05, "shear_modulus_gpa": 0.02, "tensile_xy_mpa": 30, "tensile_z_mpa": 18},
                "ABS": {"xy_modulus_gpa": 2.3, "z_modulus_gpa": 1.5, "shear_modulus_gpa": 0.6, "tensile_xy_mpa": 40, "tensile_z_mpa": 20},
                "PETG": {"xy_modulus_gpa": 2.1, "z_modulus_gpa": 1.7, "shear_modulus_gpa": 0.55, "tensile_xy_mpa": 50, "tensile_z_mpa": 32}
            },
            "orientation_safety_factors": {
                "Isotrópica": 1.0,
                "Anisotrópica X": 0.7,
                "Anisotrópica Y": 0.7,
                "Anisotrópica Z": 0.45
            },
            "gyroid_continuity_gain": "El patrón gyroid continuo 3D reduce la concentración de esfuerzos de cizalla delaminadora en un 35% en comparación con patrones ortogonales como Grid."
        },
        "environmental_effects": {
            "title": "Efectos Ambientales y Degradación",
            "moisture_absorption": {
                "PLA": {"rate_percent_24h": 0.15, "saturation_limit_percent": 0.8, "tensile_loss_saturated": 0.15, "description": "Bajo, pero causa hidrólisis a temperaturas de fusión, produciendo burbujas y fragilidad excesiva."},
                "TPU": {"rate_percent_24h": 0.65, "saturation_limit_percent": 1.8, "tensile_loss_saturated": 0.25, "description": "Alto. Al ser hidrofílico, requiere secado previo estricto (4h a 65°C). Provoca defectos por burbujas de vapor en boquilla."},
                "ABS": {"rate_percent_24h": 0.25, "saturation_limit_percent": 1.1, "tensile_loss_saturated": 0.10, "description": "Moderado. Causa defectos estéticos y porosidad intercapa."},
                "PETG": {"rate_percent_24h": 0.35, "saturation_limit_percent": 1.3, "tensile_loss_saturated": 0.20, "description": "Alto. La humedad causa hidrólisis y debilita severamente la adherencia entre capas (hasta un 40% de pérdida de adhesión)."}
            },
            "uv_resistance": {
                "PLA": {"index_1_10": 3, "rating": "Pobre", "degradation_mechanism": "Fotomordentado por rayos UV, causa decoloración, amarillamiento y fragilidad extrema."},
                "TPU": {"index_1_10": 7, "rating": "Bueno", "degradation_mechanism": "Sufre ligera decoloración superficial, pero mantiene resiliencia mecánica elástica."},
                "ABS": {"index_1_10": 2, "rating": "Muy Pobre", "degradation_mechanism": "Degradación por fotooxidación rápida. El butadieno se oxida, haciendo que el material se fragilice y agriete."},
                "PETG": {"index_1_10": 6, "rating": "Moderado", "degradation_mechanism": "Estable ante UV moderado, apto para aplicaciones exteriores semi-protegidas."}
            },
            "long_term_creep": {
                "PLA": {"relaxation_modulus_ratio_1000h": 0.40, "warping_risk": "Alto bajo carga estática permanente a >45°C."},
                "TPU": {"relaxation_modulus_ratio_1000h": 0.85, "warping_risk": "Excelente resistencia a la deformación plástica permanente (creep) a temperatura ambiente."},
                "ABS": {"relaxation_modulus_ratio_1000h": 0.70, "warping_risk": "Moderado. Estable a temperaturas <75°C."},
                "PETG": {"relaxation_modulus_ratio_1000h": 0.55, "warping_risk": "Sensible a cargas estáticas continuas de tracción a largo plazo."}
            }
        },
        "print_failure_modes": {
            "title": "Modos de Fallo de Impresión y Prevención",
            "failures": [
                {
                    "name": "Pandeo Localizado del Contorno (Shell Buckling)",
                    "description": "Las paredes exteriores del cubo colapsan lateralmente bajo cargas de compresión axial.",
                    "preventions": "Aumentar el grosor de la pared (wallThickness >= 1.6 mm) o habilitar relleno continuo."
                },
                {
                    "name": "Delaminación Intercapa (Interlayer Delamination)",
                    "description": "Separación de las capas de impresión debido a fuerzas de cizallamiento o gradientes de contracción térmica.",
                    "preventions": "Aumentar la temperatura de extrusión, apagar ventilador de capa, o reducir velocidad."
                },
                {
                    "name": "Deformación por Contracción Térmica (Warping)",
                    "description": "Las esquinas inferiores se despegan de la base de impresión debido a tensiones internas de enfriamiento rápido.",
                    "preventions": "Utilizar cámara de impresión calefactada, cama a >=90°C (para ABS), o mejorar adherencia con adhesivo."
                },
                {
                    "name": "Instabilidad de Pandeo por TPU flexible (Extrusion Buckling)",
                    "description": "El filamento elástico de TPU se dobla en el extrusor antes de entrar en la zona caliente de la boquilla.",
                    "preventions": "Usar extrusor Direct Drive con guías de filamento ajustadas, y restringir velocidades de impresión."
                }
            ]
        },
        "manufacturing_rules": {
            "title": "Reglas de Diseño y Manufactura Sostenible",
            "material_rules": {
                "TPU": [
                    {"condition": "printSpeed > 35", "action": "WARNING", "text": "Velocidad excesiva para elastómeros. TPU requiere velocidades bajas (20-35 mm/s) para evitar atascamientos."},
                    {"condition": "infillDensity < 35 and cellSize > 6.0", "action": "CRITICAL", "text": "Celdas demasiado grandes en TPU provocan fallos de puente y deformación inestable."},
                    {"condition": "wallThickness < 0.8", "action": "CRITICAL", "text": "El espesor mínimo en TPU debe ser >= 0.8mm (2 perímetros) para evitar desgarros."}
                ],
                "ABS": [
                    {"condition": "enclosure_enabled == False", "action": "CRITICAL", "text": "ABS requiere cámara calefactada o cerrada para evitar fisuras por gradientes de temperatura."},
                    {"condition": "fan_speed > 20", "action": "WARNING", "text": "Exceso de ventilación en ABS induce delaminación interlayer y warping catastrófico."}
                ],
                "PETG": [
                    {"condition": "layer_cooling < 30", "action": "WARNING", "text": "Bajo enfriamiento en PETG causa excesivos hilos (stringing) y goteos térmicos."}
                ]
            }
        }
    }

    # 2. Define TPU details
    tpu_data = {
        "mechanical": {
            "young_modulus_nominal_gpa": 0.08,
            "tensile_strength_nominal_mpa": 30.0,
            "shear_modulus_gpa": 0.025,
            "poisson_ratio": 0.48,
            "shore_hardness_variants": {
                "85A": {"modulus_mpa": 15.0, "yield_strength_mpa": 2.5, "elongation_break_percent": 600.0},
                "90A": {"modulus_mpa": 45.0, "yield_strength_mpa": 4.5, "elongation_break_percent": 500.0},
                "95A": {"modulus_mpa": 80.0, "yield_strength_mpa": 8.0, "elongation_break_percent": 450.0}
            },
            "hyperelastic_model": {
                "model_type": "Mooney-Rivlin 2-Parameter",
                "C10": 3.82,
                "C01": 0.94,
                "stress_strain_characteristic": "Altamente no lineal, con alargamiento por fluencia continua y alta ductilidad elástica."
            },
            "damping_coefficient": 0.35,
            "rebound_resilience_percent": 65.0,
            "compression_behavior": "Pandeo progresivo continuo y elástico de las celdas unitarias. Absorbe energía de forma constante en la región de plateau, con densificación en deformaciones elevadas (>65%)."
        },
        "thermal": {
            "melting_temperature_c": 225.0,
            "glass_transition_temperature_c": -40.0,
            "thermal_conductivity_w_mk": 0.19,
            "specific_heat_j_kg_k": 1800,
            "coefficient_thermal_expansion_e6_k": 150.0,
            "heat_deflection_temperature_045mpa_c": 60.0,
            "thermal_accumulation_sensitivity": "Alta. La falta de enfriamiento local y la baja conductividad pueden provocar flacidez plástica y goteo de filamento."
        },
        "rheology": {
            "melt_flow_index_g_10min": 15.0,
            "viscosity_profile": "No-Newtoniana (adgazamiento por cizallamiento). La viscosidad disminuye significativamente al aumentar la tasa de cizallamiento en el extrusor.",
            "recommended_extrusion_temperature_range": [220, 240]
        },
        "fatigue": {
            "cyclic_fatigue_limit_cycles_to_failure": 1e6,
            "stress_amplitude_limit_mpa": 12.0,
            "hysteresis_energy_loss_j_cycle": 1.25
        },
        "fdm_behavior": {
            "layer_adhesion_strength_factor_0_to_1": 0.85,
            "bridging_limit_mm": 5.0,
            "overhang_angle_limit_deg": 45.0,
            "stringing_index_1_to_10": 9,
            "pressure_advance_sensitivity": "Extremadamente alta (requiere valores de 0.4 a 1.2 s para compensar la elasticidad en el tubo)."
        },
        "printer_profiles": {
            "DirectDrive": {
                "max_print_speed_mm_s": 35.0,
                "retraction_distance_mm": 1.5,
                "retraction_speed_mm_s": 25.0,
                "extrusion_multiplier": 1.05
            },
            "Bowden": {
                "max_print_speed_mm_s": 15.0,
                "retraction_distance_mm": 5.0,
                "retraction_speed_mm_s": 15.0,
                "extrusion_multiplier": 1.10
            }
        },
        "manufacturer_variants": [
            {"brand": "NinjaTek", "name": "NinjaFlex", "shore_hardness": "85A", "specialty": "Flexibilidad extrema, tacto de goma."},
            {"brand": "SainSmart", "name": "TPU Filament", "shore_hardness": "95A", "specialty": "Excelente imprimibilidad, equilibrio mecánico."},
            {"brand": "BASF", "name": "Ultrafuse TPU 95A", "shore_hardness": "95A", "specialty": "Grado industrial, resistente a la abrasión."},
            {"brand": "eSUN", "name": "eTPU-95A", "shore_hardness": "95A", "specialty": "Alta rentabilidad y ductilidad elástica."}
        ],
        "ml_features": {
            "norm_modulus": 0.025,
            "norm_hardness": 0.35,
            "norm_adhesion": 0.90,
            "warping_factor": 0.05,
            "elasticity_index": 0.95
        }
    }

    # 3. Define ABS details
    abs_data = {
        "mechanical": {
            "young_modulus_nominal_gpa": 2.30,
            "tensile_strength_nominal_mpa": 40.0,
            "shear_modulus_gpa": 0.85,
            "poisson_ratio": 0.35,
            "impact_strength_izod_j_m": 200.0,
            "yield_strength_mpa": 38.0,
            "elongation_break_percent": 30.0,
            "compression_behavior": "Rígido con fluencia definida, seguido de deformación plástica progresiva antes del agrietamiento por cizalladura."
        },
        "thermal": {
            "melting_temperature_c": 240.0,
            "glass_transition_temperature_c": 105.0,
            "thermal_conductivity_w_mk": 0.17,
            "specific_heat_j_kg_k": 1400,
            "coefficient_thermal_expansion_e6_k": 90.0,
            "heat_deflection_temperature_045mpa_c": 85.0,
            "thermal_accumulation_sensitivity": "Baja. Sin embargo, sufre tensiones residuales por gradientes térmicos elevados."
        },
        "rheology": {
            "melt_flow_index_g_10min": 19.0,
            "viscosity_profile": "Newtoniana moderada en rangos normales de impresión.",
            "recommended_extrusion_temperature_range": [230, 255]
        },
        "fatigue": {
            "cyclic_fatigue_limit_cycles_to_failure": 1e5,
            "stress_amplitude_limit_mpa": 18.0,
            "hysteresis_energy_loss_j_cycle": 0.45
        },
        "fdm_behavior": {
            "layer_adhesion_strength_factor_0_to_1": 0.55,
            "bridging_limit_mm": 15.0,
            "overhang_angle_limit_deg": 50.0,
            "stringing_index_1_to_10": 4,
            "pressure_advance_sensitivity": "Moderada (rango 0.05 a 0.15)."
        },
        "printer_profiles": {
            "DirectDrive": {
                "max_print_speed_mm_s": 60.0,
                "retraction_distance_mm": 0.8,
                "retraction_speed_mm_s": 35.0,
                "extrusion_multiplier": 1.0
            },
            "Bowden": {
                "max_print_speed_mm_s": 50.0,
                "retraction_distance_mm": 4.5,
                "retraction_speed_mm_s": 30.0,
                "extrusion_multiplier": 1.02
            }
        },
        "manufacturer_variants": [
            {"brand": "Prusament", "name": "ABS", "shore_hardness": "78D", "specialty": "Excelente tolerancia dimensional."},
            {"brand": "eSUN", "name": "ABS+", "shore_hardness": "75D", "specialty": "Fórmula modificada con baja contracción térmica."},
            {"brand": "Polymaker", "name": "PolyLite ABS", "shore_hardness": "76D", "specialty": "Alta resistencia al impacto y estabilidad."}
        ],
        "ml_features": {
            "norm_modulus": 0.72,
            "norm_hardness": 0.80,
            "norm_adhesion": 0.45,
            "warping_factor": 0.90,
            "elasticity_index": 0.15
        }
    }

    # 4. Define PETG details
    petg_data = {
        "mechanical": {
            "young_modulus_nominal_gpa": 2.10,
            "tensile_strength_nominal_mpa": 50.0,
            "shear_modulus_gpa": 0.78,
            "poisson_ratio": 0.37,
            "impact_strength_izod_j_m": 120.0,
            "yield_strength_mpa": 45.0,
            "elongation_break_percent": 50.0,
            "compression_behavior": "Comportamiento tenaz con alta ductilidad, combinando rigidez intermedia con deformación plástica y alta resistencia al cizallamiento interlaminar."
        },
        "thermal": {
            "melting_temperature_c": 235.0,
            "glass_transition_temperature_c": 80.0,
            "thermal_conductivity_w_mk": 0.21,
            "specific_heat_j_kg_k": 1200,
            "coefficient_thermal_expansion_e6_k": 70.0,
            "heat_deflection_temperature_045mpa_c": 70.0,
            "thermal_accumulation_sensitivity": "Moderada. Requiere enfriamiento adecuado para evitar deformaciones locales."
        },
        "rheology": {
            "melt_flow_index_g_10min": 22.0,
            "viscosity_profile": "Alta viscosidad y comportamiento pegajoso en fusión.",
            "recommended_extrusion_temperature_range": [220, 245]
        },
        "fatigue": {
            "cyclic_fatigue_limit_cycles_to_failure": 3e5,
            "stress_amplitude_limit_mpa": 22.0,
            "hysteresis_energy_loss_j_cycle": 0.60
        },
        "fdm_behavior": {
            "layer_adhesion_strength_factor_0_to_1": 0.92,
            "bridging_limit_mm": 10.0,
            "overhang_angle_limit_deg": 45.0,
            "stringing_index_1_to_10": 8,
            "pressure_advance_sensitivity": "Alta (rango 0.12 a 0.25, gotea si no está calibrado)."
        },
        "printer_profiles": {
            "DirectDrive": {
                "max_print_speed_mm_s": 50.0,
                "retraction_distance_mm": 1.2,
                "retraction_speed_mm_s": 30.0,
                "extrusion_multiplier": 0.98
            },
            "Bowden": {
                "max_print_speed_mm_s": 40.0,
                "retraction_distance_mm": 5.5,
                "retraction_speed_mm_s": 25.0,
                "extrusion_multiplier": 1.0
            }
        },
        "manufacturer_variants": [
            {"brand": "Overture", "name": "PETG", "shore_hardness": "72D", "specialty": "Facilidad de extrusión, excelente adhesión intercapa."},
            {"brand": "ESUN", "name": "PETG-CF", "shore_hardness": "76D", "specialty": "Reforzado con fibra de carbono para máxima rigidez."},
            {"brand": "Prusament", "name": "PETG", "shore_hardness": "74D", "specialty": "Alta tenacidad, grado industrial."}
        ],
        "ml_features": {
            "norm_modulus": 0.65,
            "norm_hardness": 0.72,
            "norm_adhesion": 0.95,
            "warping_factor": 0.25,
            "elasticity_index": 0.20
        }
    }

    # Write files
    def write_json(directory, filename, data):
        dir_path = BASE_DIR / directory
        os.makedirs(dir_path, exist_ok=True)
        file_path = dir_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Created file: {file_path}")

    # Shared properties
    for k, v in shared_data.items():
        if k == "manufacturing_rules":
            write_json("shared/manufacturing_rules", "rules.json", v)
        else:
            write_json(f"shared/{k}", "properties.json", v)

    # Material properties
    mats = {"TPU": tpu_data, "ABS": abs_data, "PETG": petg_data}
    for mat_name, data in mats.items():
        for category, cat_data in data.items():
            if category == "printer_profiles":
                write_json(f"{mat_name}/{category}", "profiles.json", cat_data)
            elif category == "manufacturer_variants":
                write_json(f"{mat_name}/{category}", "variants.json", cat_data)
            else:
                write_json(f"{mat_name}/{category}", "properties.json", cat_data)

if __name__ == '__main__':
    create_db()
