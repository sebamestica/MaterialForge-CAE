import pandas as pd
import numpy as np
from src.utils import write_json

TARGET_COL = "compressive_strength"
POST_ENSAYO = {"compressive_strength_mean", "compressive_strength_std", "n_readings", "source_trace"}

FEATURE_CATEGORIES = {
    "geometry": ["structure_type", "infill_pattern", "design_param_numeric",
                 "design_param_relative", "cell_size", "cell_size_mm",
                 "wall_thickness", "wall_thickness_mm", "strut_thickness", "strut_thickness_mm",
                 "length", "thickness", "width", "transverse_area"],
    "process":  ["layer_height", "layer_thickness", "nozzle_temperature",
                 "bed_temperature", "print_speed", "print_speed_mm_s",
                 "fan_speed", "infill_density", "material"],
    "metadata": ["specimen_id", "replica_letter", "source_dataset",
                 "linkage_confidence", "experimental_group", "family"],
}


def load_final_dataset(validation, chosen_id, logger):
    logger.info(f"=== Cargando dataset final: {chosen_id} ===")
    info = validation.get(chosen_id, {})
    path = info.get("path")
    if not path:
        raise ValueError(f"No path for chosen source: {chosen_id}")

    df = pd.read_csv(path)
    logger.info(f"  Loaded: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def inspect_columns(df, logger, out_dir):
    logger.info("=== Inspección de columnas del dataset ===")

    all_cols = list(df.columns)
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    null_pct = (df.isnull().mean() * 100).round(1).to_dict()
    non_null_counts = df.count().to_dict()

    feature_map = {
        "target": [TARGET_COL] if TARGET_COL in all_cols else [],
        "geometry_present": [],
        "process_present": [],
        "metadata_present": [],
        "post_ensayo_present": [],
        "unknown": [],
    }

    col_roles = {}
    for col in all_cols:
        if col == TARGET_COL:
            role = "target"
        elif col in POST_ENSAYO:
            role = "post_ensayo"
        elif col in FEATURE_CATEGORIES["geometry"]:
            role = "geometry"
        elif col in FEATURE_CATEGORIES["process"]:
            role = "process"
        elif col in FEATURE_CATEGORIES["metadata"]:
            role = "metadata"
        else:
            role = "unknown"
        col_roles[col] = role

    available_num_features = [
        c for c in num_cols
        if c != TARGET_COL
        and c not in POST_ENSAYO
        and null_pct.get(c, 100) < 90
    ]
    available_cat_features = [
        c for c in cat_cols
        if c not in POST_ENSAYO
        and null_pct.get(c, 100) < 90
        and c not in ("source_trace",)
    ]
    usable_for_model = available_num_features + available_cat_features

    profile = {
        "n_rows": len(df),
        "n_cols": len(all_cols),
        "all_columns": all_cols,
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "null_pct": null_pct,
        "non_null_counts": non_null_counts,
        "column_roles": col_roles,
        "available_num_features": available_num_features,
        "available_cat_features": available_cat_features,
        "usable_for_model": usable_for_model,
        "target_col": TARGET_COL,
        "target_null_pct": null_pct.get(TARGET_COL, 100),
        "target_describe": df[TARGET_COL].describe().round(4).to_dict() if TARGET_COL in df.columns else {},
    }

    write_json(f"{out_dir}/column_profile.json", profile)
    logger.info(
        f"  Target col: '{TARGET_COL}' | null%={null_pct.get(TARGET_COL, 100)} | "
        f"avail_num_feat={len(available_num_features)} | avail_cat_feat={len(available_cat_features)}"
    )
    logger.info(f"  Usable features for model: {usable_for_model}")
    return profile
