from src.utils import write_json

MIN_FEATURES_HIGH_CONFIDENCE = 3
MIN_FEATURES_EXPANDED = 2

EXACT_LINK_FEATURES = {"structure_type", "infill_pattern", "replica_letter"}
PROBABLE_LINK_FEATURES = {"design_param_numeric", "design_param_relative"}
ALL_EXPECTED_FEATURES = EXACT_LINK_FEATURES | PROBABLE_LINK_FEATURES


def validate_links(linked_registry, logger, artifacts_dir):
    logger.info("=== FASE 5: Validación y clasificación de enlaces ===")

    validated = {}
    counts = {"exact_link": 0, "probable_link": 0, "weak_link": 0, "unresolved": 0}

    for sid, info in linked_registry.items():
        features = info.get("features", {})
        confidences = info.get("feature_confidences", {})

        n_exact = sum(1 for f, c in confidences.items() if c == "exact_link")
        n_probable = sum(1 for f, c in confidences.items() if c == "probable_link")
        n_total = len(features)

        has_structure = "structure_type" in features
        has_infill = "infill_pattern" in features
        has_numeric_param = "design_param_numeric" in features
        has_dims = any(f in features for f in ["length", "thickness", "width", "transverse_area"])

        missing = info.get("features_missing", [])
        n_missing_critical = sum(1 for f in missing
                                 if f in ("material", "layer_height", "nozzle_temperature",
                                          "print_speed", "cell_size_mm"))

        if has_structure and has_infill and has_numeric_param and n_exact >= 2:
            confidence = "probable_link"
            justification = (
                f"structure_type and infill_pattern derived exactly from specimen ID prefix. "
                f"Numeric parameter ({features.get('design_param_numeric')}) extracted from ID with "
                f"probable physical meaning (density/cell_size index within group). "
                f"Missing critical process params: {n_missing_critical}."
            )
            counts["probable_link"] += 1

        elif has_structure and has_infill and not has_numeric_param:
            confidence = "weak_link"
            justification = (
                f"Only structural type linked (structure_type='{features.get('structure_type')}', "
                f"infill_pattern='{features.get('infill_pattern')}'). "
                f"No numeric design parameter available. "
                f"Insufficient for regression beyond structure-level description."
            )
            counts["weak_link"] += 1

        elif has_structure and has_numeric_param:
            confidence = "probable_link"
            justification = (
                f"structure_type inferred from ID. Numeric param present. "
                f"infill_pattern implied by structure type."
            )
            counts["probable_link"] += 1

        else:
            confidence = "unresolved"
            justification = "Insufficient features could be linked. Cannot use for modeling."
            counts["unresolved"] += 1

        validated[sid] = {
            **info,
            "linkage_confidence": confidence,
            "linkage_justification": justification,
            "n_features_exact": n_exact,
            "n_features_probable": n_probable,
            "n_features_total": n_total,
            "n_critical_missing": n_missing_critical,
            "usable_high_confidence": (confidence == "probable_link" and n_exact >= 2),
            "usable_expanded": (confidence in ("probable_link", "weak_link")),
        }
        logger.info(f"  {sid}: {confidence} | exact={n_exact} | probable={n_probable} | missing_critical={n_missing_critical}")

    logger.info(
        f"  Classification: exact={counts['exact_link']} | probable={counts['probable_link']} | "
        f"weak={counts['weak_link']} | unresolved={counts['unresolved']}"
    )

    write_json(f"{artifacts_dir}/linkage_tables/validated_links.json", validated)
    return validated, counts
