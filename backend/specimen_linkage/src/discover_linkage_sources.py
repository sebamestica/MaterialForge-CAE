import pandas as pd
from pathlib import Path
from src.utils import get_cleaned_dir, get_project_root, write_json


SOURCES = {
    "Compressivedata_cleaned.csv": {
        "type": "timeseries_compressive",
        "potential": ["specimen_ids", "stress_per_reading"],
        "has_explicit_specimen_col": True,
        "notes": "High-frequency sensor log. specimen_id in column 'probeta'. "
                 "No process parameters present.",
    },
    "Propiedades_Extraidas_cleaned.csv": {
        "type": "summary_table",
        "potential": ["specimen_ids", "dim_length", "dim_thickness", "dim_width", "transverse_area"],
        "has_explicit_specimen_col": True,
        "notes": "Lists all compressive specimen IDs via 'sheet' column. "
                 "All numeric property columns (max_force, modulo_young, etc.) are EMPTY for compressive entries. "
                 "Dimension columns (length, thickness, width, transverse_area) are present but also EMPTY.",
    },
    "FDM_Dataset_cleaned.csv": {
        "type": "process_parameters",
        "potential": ["layer_height_mm", "infill_density_%", "infill_pattern", "material",
                      "microstructure", "material_type", "print_speed_mm_s", "melting_temperature_c"],
        "has_explicit_specimen_col": False,
        "notes": "50 rows of FDM print parameters. NO specimen_id column. "
                 "Has 'microstructure' (fine/coarse) and 'material_type' (pure/composite). "
                 "Cannot be joined to specimens — no shared key.",
    },
    "data_cleaned.csv": {
        "type": "process_result_tensile",
        "potential": ["layer_height", "infill_density", "material", "infill_pattern"],
        "has_explicit_specimen_col": False,
        "notes": "50 rows of tensile test results with print parameters. "
                 "No specimen_id column. Tensile data — not compressive. "
                 "Cannot link to compressive specimens.",
    },
    "TensiondataA_cleaned.csv": {
        "type": "timeseries_tension",
        "potential": ["specimen_ids"],
        "has_explicit_specimen_col": True,
        "notes": "Tension test time-series. Specimen IDs are for tension specimens "
                 "(Sol.A, Sol.B, G36A, G55B...) — DIFFERENT experiment from compressive. "
                 "Not linkable to compressive specimens.",
    },
    "TensiondataB_cleaned.csv": {
        "type": "timeseries_tension",
        "potential": ["specimen_ids"],
        "has_explicit_specimen_col": True,
        "notes": "Tension test time-series for a second batch. "
                 "Specimen IDs (10RA, 36RB, 55TA...) use DIFFERENT naming convention. "
                 "Not linkable to compressive specimens.",
    },
}

AUXILIARY_SOURCES = {
    "Normalization/config/column_mappings.json": {
        "type": "metadata",
        "potential": ["column_name_mappings"],
        "notes": "Column rename mappings. Confirms column structure of each file. "
                 "No specimen-level linkage information.",
    },
    "Normalization/config/file_registry.json": {
        "type": "metadata",
        "potential": ["value_score", "reliability_score", "status"],
        "notes": "Dataset registry. No specimen-level data.",
    },
    "model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv": {
        "type": "derived_compressive_dataset",
        "potential": ["specimen_ids", "compressive_strength", "structure_type"],
        "notes": "The 35 valid compressive specimens aggregated. Starting point for linkage.",
    },
    "data/Proyecto_Machine_Learning/printer_dataset.py": {
        "type": "analysis_script",
        "potential": [],
        "notes": "ML script from the original author (AFUMETTO, 2018). "
                 "Works only on data.csv (tensile). "
                 "No references to specimen IDs or compressive data. Not useful for linkage.",
    },
}


def discover_linkage_sources(logger, artifacts_dir):
    logger.info("=== FASE 1: Inventario de fuentes para linkage ===")
    root = get_project_root()
    cleaned_dir = get_cleaned_dir()

    inventory = {}

    for fname, meta in SOURCES.items():
        fpath = cleaned_dir / fname
        if not fpath.exists():
            logger.warning(f"  File not found: {fpath}")
            continue

        try:
            df = pd.read_csv(fpath, nrows=5, low_memory=False)
            n_rows = sum(1 for _ in open(fpath, encoding="utf-8")) - 1
            cols = list(df.columns)
        except Exception as e:
            logger.error(f"  Cannot read {fname}: {e}")
            continue

        inventory[fname] = {
            **meta,
            "path": str(fpath),
            "n_rows_approx": n_rows,
            "columns": cols,
        }
        logger.info(
            f"  {fname}: rows~{n_rows} | has_id={meta['has_explicit_specimen_col']} | "
            f"type={meta['type']}"
        )

    for fname, meta in AUXILIARY_SOURCES.items():
        fpath = root / fname
        if fpath.exists():
            inventory[fname] = {**meta, "path": str(fpath), "n_rows_approx": None, "columns": []}
            logger.info(f"  {fname}: auxiliary source | type={meta['type']}")
        else:
            logger.warning(f"  Auxiliary not found: {fpath}")

    write_json(f"{artifacts_dir}/candidate_sources/source_inventory.json", inventory)
    logger.info(f"Inventario completo: {len(inventory)} fuentes inspeccionadas.")
    return inventory
