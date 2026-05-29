import pandas as pd
from pathlib import Path
from src.utils import get_project_root, write_json


SOURCE_PRIORITY = [
    {
        "id": "specimen_linkage_hc",
        "label": "specimen_linkage high_confidence",
        "rel_path": "specimen_linkage/data/linked_dataset/high_confidence_dataset.csv",
        "requires_col": "compressive_strength",
        "forbidden_cols": ["tension_strenght", "elongation"],
        "description": "35 compressive specimens aggregated from Compressivedata.csv with structure linkage.",
    },
    {
        "id": "specimen_linkage_exp",
        "label": "specimen_linkage expanded_with_caution",
        "rel_path": "specimen_linkage/data/linked_dataset/expanded_with_caution_dataset.csv",
        "requires_col": "compressive_strength",
        "forbidden_cols": ["tension_strenght", "elongation"],
        "description": "Same specimens as HC — expanded classification includes weak_link.",
    },
    {
        "id": "audit_candidate_A",
        "label": "model_data_audit candidate_A",
        "rel_path": "model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv",
        "requires_col": "compressive_strength",
        "forbidden_cols": ["tension_strenght"],
        "description": "Aggregated compressive specimens before linkage enrichment.",
    },
]

FORBIDDEN_SOURCES = [
    "model_pipeline/data/model_input/raw_model_input.csv",
    "model_data_audit/artifacts/candidate_targets/candidate_B_data_only.csv",
    "Normalization/cleaned/data_cleaned.csv",
    "Normalization/cleaned/TensiondataA_cleaned.csv",
    "Normalization/cleaned/TensiondataB_cleaned.csv",
]


def discover_sources(logger, out_dir):
    logger.info("=== Descubrimiento de fuentes de compresión ===")
    root = get_project_root()
    discovered = []

    for src in SOURCE_PRIORITY:
        path = root / src["rel_path"]
        entry = {**src, "path": str(path), "exists": path.exists(), "chosen": False}
        if path.exists():
            try:
                df = pd.read_csv(path, nrows=3)
                entry["columns_sample"] = list(df.columns)
                entry["has_required_col"] = src["requires_col"] in df.columns
                entry["has_forbidden_col"] = any(f in df.columns for f in src["forbidden_cols"])
            except Exception as e:
                entry["read_error"] = str(e)
                entry["has_required_col"] = False
                entry["has_forbidden_col"] = False
        else:
            entry["has_required_col"] = False
            entry["has_forbidden_col"] = False
        discovered.append(entry)
        logger.info(
            f"  {src['label']}: exists={entry['exists']} | "
            f"has_target={entry.get('has_required_col')} | "
            f"has_forbidden={entry.get('has_forbidden_col')}"
        )

    forbidden_found = []
    for fb in FORBIDDEN_SOURCES:
        p = root / fb
        if p.exists():
            forbidden_found.append(str(p))
            logger.warning(f"  FORBIDDEN source exists (will not be used): {fb}")

    write_json(f"{out_dir}/source_discovery.json",
               {"candidates": discovered, "forbidden_found": forbidden_found})
    return discovered, forbidden_found
