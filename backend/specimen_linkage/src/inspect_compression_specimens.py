import pandas as pd
import re
from pathlib import Path
from src.utils import get_project_root, write_json


CANDIDATE_A_REL = "model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv"


def inspect_compression_specimens(logger, artifacts_dir):
    logger.info("=== FASE 2: Registro maestro de probetas compresivas ===")
    root = get_project_root()
    path = root / CANDIDATE_A_REL

    if not path.exists():
        logger.error(f"  Candidate A not found at {path}. Run model_data_audit first.")
        return {}

    df = pd.read_csv(path)
    logger.info(f"  Loaded {len(df)} specimens from candidate_A.")

    registry = {}
    for _, row in df.iterrows():
        sid = str(row["specimen_id"]).strip()
        registry[sid] = {
            "specimen_id": sid,
            "source_dataset": row.get("source_dataset", "Compressivedata.csv"),
            "compressive_strength_max": float(row.get("compressive_strength", float("nan"))),
            "compressive_strength_mean": float(row.get("compressive_strength_mean", float("nan"))),
            "compressive_strength_std": float(row.get("compressive_strength_std", float("nan"))),
            "n_readings": int(row.get("n_readings", 0)),
            "structure_type_inferred": str(row.get("structure_type", "unknown")),
            "target_col_origin": "max(stress[mpa]) per specimen from Compressivedata time-series",
            "linkage_status": "pending",
            "features_linked": [],
            "features_missing": [],
            "linkage_confidence": "unresolved",
        }

    write_json(f"{artifacts_dir}/specimen_feature_registry/specimen_master.json", registry)
    logger.info(f"  Master registry created: {len(registry)} specimens.")
    return registry
