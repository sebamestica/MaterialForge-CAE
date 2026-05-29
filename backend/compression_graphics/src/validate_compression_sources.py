import pandas as pd
from src.utils import write_json, write_md, md_table


REQUIRED_TARGET = "compressive_strength"
POST_ENSAYO_COLS = {"compressive_strength_mean", "compressive_strength_std", "n_readings"}
TENSILE_MARKERS = {"tension_strenght", "elongation", "strainext", "tensile_strength"}


def validate_compression_sources(discovered, logger, reports_dir, out_dir):
    logger.info("=== Validación de fuentes de compresión ===")
    validation = {}
    chosen = None

    for src in discovered:
        sid = src["id"]
        path = src["path"]
        result = {
            "source_id": sid,
            "label": src["label"],
            "path": path,
            "checks": {},
            "valid": False,
            "rejection_reason": None,
        }

        if not src.get("exists"):
            result["rejection_reason"] = "File does not exist on disk"
            result["checks"]["file_exists"] = False
            validation[sid] = result
            logger.warning(f"  {sid}: REJECTED — file not found")
            continue

        result["checks"]["file_exists"] = True

        try:
            df = pd.read_csv(path)
        except Exception as e:
            result["rejection_reason"] = f"Cannot read CSV: {e}"
            validation[sid] = result
            logger.warning(f"  {sid}: REJECTED — read error")
            continue

        result["checks"]["readable"] = True
        result["n_rows"] = len(df)
        result["columns"] = list(df.columns)

        if REQUIRED_TARGET not in df.columns:
            result["rejection_reason"] = f"Missing required target column '{REQUIRED_TARGET}'"
            result["checks"]["has_target"] = False
            validation[sid] = result
            logger.warning(f"  {sid}: REJECTED — no target column")
            continue

        result["checks"]["has_target"] = True

        tensile_found = [c for c in df.columns if c in TENSILE_MARKERS]
        if tensile_found:
            result["rejection_reason"] = f"Contains tensile markers: {tensile_found}"
            result["checks"]["tensile_free"] = False
            validation[sid] = result
            logger.warning(f"  {sid}: REJECTED — tensile columns found: {tensile_found}")
            continue

        result["checks"]["tensile_free"] = True

        has_trace = "source_trace" in df.columns or "source_dataset" in df.columns
        result["checks"]["has_traceability"] = has_trace

        target_nulls = df[REQUIRED_TARGET].isnull().sum()
        result["checks"]["target_null_pct"] = round(target_nulls / len(df) * 100, 1)

        if df[REQUIRED_TARGET].isnull().all():
            result["rejection_reason"] = "Target column is entirely null"
            result["checks"]["target_has_values"] = False
            validation[sid] = result
            logger.warning(f"  {sid}: REJECTED — target all null")
            continue

        result["checks"]["target_has_values"] = True
        result["valid"] = True

        if chosen is None:
            chosen = sid
            src["chosen"] = True
            logger.info(f"  {sid}: VALID — selected as primary source")
        else:
            logger.info(f"  {sid}: VALID — available as fallback")

        validation[sid] = result

    write_json(f"{out_dir}/source_validation.json", validation)

    lines = ["# Validación de Fuentes de Compresión\n"]
    lines.append("## Fuente seleccionada\n")
    if chosen:
        v = validation[chosen]
        lines.append(f"- **ID**: `{chosen}`")
        lines.append(f"- **Label**: {v['label']}")
        lines.append(f"- **Path**: `{v['path']}`")
        lines.append(f"- **Filas**: {v.get('n_rows', '?')}")
        lines.append(f"- **Columnas**: {v.get('columns', [])}")
        lines.append(f"- **Checks**: {v['checks']}\n")
    else:
        lines.append("**NINGUNA FUENTE VÁLIDA ENCONTRADA.**\n")

    lines.append("\n## Estado de todas las fuentes candidatas\n")
    headers = ["Source ID", "Válida", "Razón de rechazo"]
    rows = []
    for sid, v in validation.items():
        rows.append([sid, "✅" if v["valid"] else "❌", v.get("rejection_reason", "—")])
    lines.append(md_table(headers, rows))

    lines.append("\n\n## Fuentes de tracción (no usadas)\n")
    lines.append("Las siguientes fuentes contienen datos de tracción y están explícitamente excluidas:")
    lines.append("- `Normalization/cleaned/data_cleaned.csv` — tensile, 50 filas")
    lines.append("- `Normalization/cleaned/TensiondataA_cleaned.csv` — tensile time-series")
    lines.append("- `Normalization/cleaned/TensiondataB_cleaned.csv` — tensile time-series")
    lines.append("- `model_data_audit/artifacts/candidate_targets/candidate_B_data_only.csv` — tensile mislabeled")

    write_md(f"{reports_dir}/source_validation.md", "\n".join(lines))
    logger.info(f"  Source validation complete. Chosen: {chosen}")
    return validation, chosen
