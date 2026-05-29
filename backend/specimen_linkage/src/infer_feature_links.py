import pandas as pd
from pathlib import Path
from src.utils import get_cleaned_dir, write_json


PROPIEDADES_FILE = "Propiedades_Extraidas_cleaned.csv"

PROPIEDADES_DIM_COLS = ["length", "thickness", "width", "transverse_area"]

STRUCTURE_NUMERIC_MEANING = {
    "G":  {"29": 29, "42": 42, "62": 62},
    "H":  {"36": 36, "44": 44, "67": 67},
    "T":  {"24": 24, "37": 37, "45": 45},
    "TQ": {"45": 45},
}

INFILL_PATTERN_BY_STRUCTURE = {
    "gyroid":          "gyroid",
    "honeycomb":       "honeycomb",
    "triply_periodic": "triply_periodic",
    "solid":           "solid",
}


def _load_propiedades_dims(cleaned_dir):
    path = cleaned_dir / PROPIEDADES_FILE
    df = pd.read_csv(path, low_memory=False)
    comp = df[df["file"].str.contains("Compressive", case=False, na=False)].copy()
    comp = comp.rename(columns={"sheet": "specimen_id"})
    dim_available = {}
    for _, row in comp.iterrows():
        sid = str(row["specimen_id"]).strip()
        dims = {}
        for col in PROPIEDADES_DIM_COLS:
            val = row.get(col)
            if pd.notna(val):
                dims[col] = float(val)
        dim_available[sid] = dims
    return dim_available


def infer_feature_links(parsed_registry, interpretation_notes, logger, artifacts_dir):
    logger.info("=== FASE 4: Inferencia de features enlazables por probeta ===")
    cleaned_dir = get_cleaned_dir()

    prop_dims = _load_propiedades_dims(cleaned_dir)

    linked = {}
    for sid, info in parsed_registry.items():
        struct = info.get("structure_type_from_id", "unknown")
        prefix = info.get("id_prefix", "")
        num = info.get("param_numeric")
        replica = info.get("replica_letter", "")

        features = {}
        feature_sources = {}
        feature_confidences = {}

        features["structure_type"] = struct
        feature_sources["structure_type"] = "parsed:specimen_id_prefix"
        feature_confidences["structure_type"] = "exact_link"

        if struct in INFILL_PATTERN_BY_STRUCTURE:
            features["infill_pattern"] = INFILL_PATTERN_BY_STRUCTURE[struct]
            feature_sources["infill_pattern"] = "inferred:structure_type_implies_infill"
            feature_confidences["infill_pattern"] = "exact_link"

        if num is not None:
            features["design_param_numeric"] = num
            feature_sources["design_param_numeric"] = "parsed:specimen_id_number"
            feature_confidences["design_param_numeric"] = "probable_link"

            intp = interpretation_notes.get(prefix, {})
            unique_vals = sorted(intp.get("unique_numeric_values", []))
            if len(unique_vals) >= 2:
                min_v = min(unique_vals)
                max_v = max(unique_vals)
                if max_v > min_v:
                    norm = (num - min_v) / (max_v - min_v)
                    features["design_param_relative"] = round(norm, 4)
                    feature_sources["design_param_relative"] = "computed:min_max_normalization_within_prefix_group"
                    feature_confidences["design_param_relative"] = "probable_link"

        if replica:
            features["replica_letter"] = replica
            feature_sources["replica_letter"] = "parsed:specimen_id_suffix"
            feature_confidences["replica_letter"] = "exact_link"

        dims = prop_dims.get(sid, {})
        for col, val in dims.items():
            features[col] = val
            feature_sources[col] = f"Propiedades_Extraidas_cleaned.csv:sheet={sid}"
            feature_confidences[col] = "exact_link"

        missing = []
        cannot_infer_reason = {}

        for feat in ["material", "nozzle_temperature", "bed_temperature",
                     "print_speed", "layer_height", "fan_speed", "cell_size_mm",
                     "wall_thickness_mm", "strut_thickness_mm", "print_orientation"]:
            if feat not in features:
                missing.append(feat)
                cannot_infer_reason[feat] = (
                    "No source file contains this feature linked to compressive specimen IDs. "
                    "FDM_Dataset has process parameters but no specimen_id column. "
                    "Cannot join without explicit mapping."
                )

        linked[sid] = {
            **info,
            "features": features,
            "feature_sources": feature_sources,
            "feature_confidences": feature_confidences,
            "features_missing": missing,
            "cannot_infer_reason": cannot_infer_reason,
            "n_features_linked": len(features),
            "n_features_missing": len(missing),
        }
        logger.debug(f"  {sid}: {len(features)} features linked, {len(missing)} missing")

    write_json(f"{artifacts_dir}/specimen_feature_registry/linked_features.json", linked)
    logger.info(f"  Feature inference complete: {len(linked)} specimens.")
    return linked
