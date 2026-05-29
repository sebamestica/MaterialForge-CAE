import os
from pathlib import Path
from src.utils import load_json, write_md, write_csv_rows, timestamp


def discover_outputs(review_cfg, logger):
    logger.info("FASE 1: Inventario del estado actual del proyecto")

    base = Path(review_cfg["model_pipeline_dir"])
    linkage_dir = Path(review_cfg["specimen_linkage_dir"])
    cg_dir = Path(review_cfg["compression_graphics_dir"])
    audit_dir = Path(review_cfg["model_data_audit_dir"])
    master_src = Path(review_cfg["master_source"])

    inventory = {}

    inventory["master_source"] = {
        "path": str(master_src.resolve()) if master_src.exists() else str(master_src),
        "exists": master_src.exists(),
        "status": "official" if master_src.exists() else "MISSING",
    }

    if master_src.exists():
        import pandas as pd
        df = pd.read_csv(master_src)
        inventory["master_source"]["rows"] = len(df)
        inventory["master_source"]["columns"] = list(df.columns)
        inventory["master_source"]["target_present"] = review_cfg["canonical_target"] in df.columns

    artifacts_base = base / "artifacts"
    model_files = {}
    for pkl in (artifacts_base / "trained_models").glob("*.pkl"):
        model_files[pkl.stem] = {"path": str(pkl), "size_kb": round(pkl.stat().st_size / 1024, 1)}
    inventory["trained_models"] = model_files

    metrics_files = {}
    for mf in (artifacts_base / "metrics").glob("*.csv"):
        metrics_files[mf.name] = str(mf)
    inventory["metrics_files"] = metrics_files

    prediction_files = {}
    for pf in (artifacts_base / "predictions").glob("*.csv"):
        prediction_files[pf.name] = str(pf)
    inventory["prediction_files"] = prediction_files

    pipeline_reports = {}
    reports_dir = base / "reports"
    if reports_dir.exists():
        for rpt in reports_dir.glob("*.md"):
            pipeline_reports[rpt.name] = str(rpt)
    inventory["pipeline_reports"] = pipeline_reports

    linkage_reports = {}
    lr_dir = linkage_dir / "reports"
    if lr_dir.exists():
        for rpt in lr_dir.glob("*.md"):
            linkage_reports[rpt.name] = str(rpt)
    inventory["linkage_reports"] = linkage_reports

    audit_reports = {}
    ar_dir = audit_dir / "reports"
    if ar_dir.exists():
        for rpt in ar_dir.glob("*.md"):
            audit_reports[rpt.name] = str(rpt)
    inventory["audit_reports"] = audit_reports

    cg_reports = {}
    cr_dir = cg_dir / "reports"
    if cr_dir.exists():
        for rpt in cr_dir.glob("*.md"):
            cg_reports[rpt.name] = str(rpt)
    inventory["compression_graphics_reports"] = cg_reports

    cg_outputs = {}
    co_dir = cg_dir / "outputs"
    if co_dir.exists():
        for img in co_dir.rglob("*.png"):
            cg_outputs[img.name] = str(img)
    inventory["compression_graphics_figures"] = cg_outputs

    pipeline_configs = {}
    cfg_dir = base / "config"
    if cfg_dir.exists():
        for cfg in cfg_dir.glob("*.json"):
            pipeline_configs[cfg.name] = load_json(cfg)
    inventory["pipeline_configs"] = pipeline_configs

    data_splits = {}
    for split_name in ["train", "validation", "test"]:
        sp = base / "data" / split_name / f"{split_name}.csv"
        if sp.exists():
            import pandas as pd
            df_s = pd.read_csv(sp)
            data_splits[split_name] = {"rows": len(df_s), "cols": len(df_s.columns)}
    inventory["data_splits"] = data_splits

    discarded = [
        {"item": "TensiondataA.csv", "reason": "Tensile time-series, incompatible with compressive_strength"},
        {"item": "TensiondataB.csv", "reason": "Tensile time-series, incompatible with compressive_strength"},
        {"item": "data.csv (as source)", "reason": "Contains tension_strength, not compressive_strength"},
        {"item": "candidate_B_data_only", "reason": "Target is tensile, explicitly INVALID for compression"},
        {"item": "Propiedades_Extraidas.csv", "reason": "Low reliability, excluded by audit"},
        {"item": "FDM_Dataset.csv", "reason": "No target column found"},
    ]
    inventory["discarded_sources"] = discarded

    checklist_rows = []
    checklist_rows.append(["Master source available", "Yes" if inventory["master_source"]["exists"] else "No", "official"])
    checklist_rows.append(["Master source rows", str(inventory["master_source"].get("rows", "?")), "35 expected"])
    checklist_rows.append(["Target column present", str(inventory["master_source"].get("target_present", "?")), "compressive_strength"])
    checklist_rows.append(["Trained models exported", str(len(model_files)), "7 expected"])
    checklist_rows.append(["Deployment model exists", "Yes" if "GradientBoostingRegressor_deployment_ready" in model_files else "No", "GBR pkl"])
    checklist_rows.append(["Metrics files", str(len(metrics_files)), "4 expected"])
    checklist_rows.append(["Pipeline reports", str(len(pipeline_reports)), "12 expected"])
    checklist_rows.append(["Linkage reports", str(len(linkage_reports)), "5 expected"])
    checklist_rows.append(["Audit reports", str(len(audit_reports)), "5 expected"])
    checklist_rows.append(["Compression graphics reports", str(len(cg_reports)), "6 expected"])
    checklist_rows.append(["Train split rows", str(data_splits.get("train", {}).get("rows", "?")), "~24"])
    checklist_rows.append(["Validation split rows", str(data_splits.get("validation", {}).get("rows", "?")), "~4"])
    checklist_rows.append(["Test split rows", str(data_splits.get("test", {}).get("rows", "?")), "~7"])
    checklist_rows.append(["Tensile data excluded", "Yes", "Enforced by pipeline"])

    write_csv_rows(
        "tables/decision_checklist.csv",
        checklist_rows,
        ["Check", "Value", "Expected/Note"]
    )

    logger.info(f"Inventario completado: {len(model_files)} modelos, {len(pipeline_reports)} reportes pipeline")
    return inventory
