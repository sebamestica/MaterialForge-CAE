import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import write_json


FEATURE_COLS_ORDERED = [
    "specimen_id",
    "structure_type",
    "infill_pattern",
    "design_param_numeric",
    "design_param_relative",
    "replica_letter",
    "length",
    "thickness",
    "width",
    "transverse_area",
    "compressive_strength_max",
    "compressive_strength_mean",
    "compressive_strength_std",
    "n_readings",
    "source_dataset",
    "linkage_confidence",
]

POST_ENSAYO_COLS = {
    "compressive_strength_mean",
    "compressive_strength_std",
    "n_readings",
}


def build_final_model_dataset(validated_registry, logger, data_dir):
    logger.info("=== FASE 6: Construcción del dataset final de modelado ===")
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    unresolved_dir = Path(data_dir).parent / "data" / "unresolved"
    unresolved_dir.mkdir(parents=True, exist_ok=True)

    rows_hc = []
    rows_exp = []
    rows_unresolved = []

    for sid, info in validated_registry.items():
        features = info.get("features", {})
        confidence = info.get("linkage_confidence", "unresolved")

        base_row = {"specimen_id": sid}

        for col in ["structure_type", "infill_pattern", "design_param_numeric",
                    "design_param_relative", "replica_letter",
                    "length", "thickness", "width", "transverse_area"]:
            base_row[col] = features.get(col, np.nan)

        base_row["compressive_strength"] = info.get("compressive_strength_max", np.nan)
        base_row["compressive_strength_mean"] = info.get("compressive_strength_mean", np.nan)
        base_row["compressive_strength_std"] = info.get("compressive_strength_std", np.nan)
        base_row["n_readings"] = info.get("n_readings", np.nan)
        base_row["source_dataset"] = info.get("source_dataset", "Compressivedata.csv")
        base_row["linkage_confidence"] = confidence
        base_row["source_trace"] = (
            f"specimen_id:{sid} | "
            f"target:max(stress[mpa]) per probeta | "
            f"structure_type:id_prefix | "
            f"design_param:id_number | "
            f"source:Compressivedata_cleaned.csv"
        )

        if info.get("usable_high_confidence"):
            rows_hc.append(base_row)
        if info.get("usable_expanded"):
            rows_exp.append(base_row)
        if not info.get("usable_expanded"):
            rows_unresolved.append({
                "specimen_id": sid,
                "linkage_confidence": confidence,
                "n_features_linked": info.get("n_features_total", 0),
                "n_features_missing": info.get("n_features_missing", []),
                "missing_critical": info.get("n_critical_missing", 0),
                "reason": info.get("linkage_justification", ""),
            })

    df_hc = pd.DataFrame(rows_hc)
    df_exp = pd.DataFrame(rows_exp)
    df_unresolved = pd.DataFrame(rows_unresolved) if rows_unresolved else pd.DataFrame()

    hc_path = Path(data_dir) / "high_confidence_dataset.csv"
    exp_path = Path(data_dir) / "expanded_with_caution_dataset.csv"
    unresolved_path = unresolved_dir / "unresolved_specimens.csv"

    df_hc.to_csv(hc_path, index=False)
    df_exp.to_csv(exp_path, index=False)
    if not df_unresolved.empty:
        df_unresolved.to_csv(unresolved_path, index=False)

    logger.info(f"  High-confidence dataset: {len(df_hc)} specimens → {hc_path}")
    logger.info(f"  Expanded dataset: {len(df_exp)} specimens → {exp_path}")
    logger.info(f"  Unresolved: {len(df_unresolved)} specimens → {unresolved_path}")

    summary = {
        "high_confidence": {
            "rows": len(df_hc),
            "feature_cols": [c for c in df_hc.columns if c not in ("specimen_id", "source_dataset",
                                                                     "source_trace", "linkage_confidence")
                              and "compressive_strength" not in c
                              and c not in POST_ENSAYO_COLS],
            "target": "compressive_strength (max stress per specimen, MPa)",
            "path": str(hc_path),
        },
        "expanded_with_caution": {
            "rows": len(df_exp),
            "feature_cols": [c for c in df_exp.columns if c not in ("specimen_id", "source_dataset",
                                                                      "source_trace", "linkage_confidence")
                              and "compressive_strength" not in c
                              and c not in POST_ENSAYO_COLS],
            "target": "compressive_strength (max stress per specimen, MPa)",
            "path": str(exp_path),
        },
        "unresolved_count": len(df_unresolved),
    }

    return summary, df_hc, df_exp, df_unresolved
