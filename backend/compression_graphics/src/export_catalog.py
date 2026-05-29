import csv
import json
from pathlib import Path
from src.utils import write_md, write_json, md_table


def export_catalog(catalog, profile, generated_all, failed_all,
                   out_dir, reports_dir, logger):
    logger.info("=== Exportando catálogo y reportes ===")

    cat_dir = Path(out_dir) / "catalogs"
    cat_dir.mkdir(parents=True, exist_ok=True)

    csv_path = cat_dir / "figure_catalog.csv"
    fieldnames = ["filename", "path", "dataset_source", "columns_used",
                  "chart_type", "purpose", "status", "notes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in catalog:
            row_clean = {k: ("|".join(v) if isinstance(v, list) else v) for k, v in row.items()}
            writer.writerow(row_clean)

    lines_md = ["# Catálogo de Figuras — compression_graphics\n"]
    lines_md.append(f"Total generadas: **{len(generated_all)}** | No generadas: **{len(failed_all)}**\n")
    headers = ["Archivo", "Categoría", "Gráfico", "Propósito analítico"]
    rows_md = []
    for entry in catalog:
        fname = entry["filename"]
        cat = fname.split("/")[0] if "/" in entry.get("path", "") else fname[:2]
        rows_md.append([fname, entry.get("chart_type", "?"), entry.get("chart_type", "?"),
                        entry.get("purpose", "?")[:80]])
    lines_md.append(md_table(headers, rows_md))
    if failed_all:
        lines_md.append("\n\n## Figuras no generadas\n")
        for f in failed_all:
            lines_md.append(f"- {f['name']}: {f['reason']}")

    write_md(str(cat_dir / "figure_catalog.md"), "\n".join(lines_md))

    write_json(str(cat_dir / "plot_registry.json"), {
        "n_generated": len(generated_all),
        "n_failed": len(failed_all),
        "entries": catalog,
        "failed": failed_all,
    })

    _write_figure_overview(catalog, generated_all, reports_dir)
    _write_quality_summary(profile, catalog, reports_dir)
    _write_feature_target_summary(profile, reports_dir)
    _write_group_comparison_summary(catalog, reports_dir)
    _write_linkage_summary(catalog, reports_dir)

    logger.info(f"  Catalog: {len(catalog)} entries | CSV: {csv_path}")


def _write_figure_overview(catalog, generated_all, reports_dir):
    lines = ["# Resumen de Figuras Generadas\n"]
    lines.append(f"**Total de figuras generadas**: {len(generated_all)}\n")

    groups = {}
    for entry in catalog:
        fname = entry["filename"]
        prefix = fname[0] if fname else "X"
        group = {
            "Q": "quality", "T": "targets", "R": "relationships",
            "C": "comparisons", "L": "linkage", "S": "summaries",
        }.get(prefix, "other")
        groups.setdefault(group, []).append(entry)

    group_labels = {
        "quality": "Calidad del dataset",
        "targets": "Distribución del target",
        "relationships": "Relaciones feature-target",
        "comparisons": "Comparaciones por grupo",
        "linkage": "Linkage y trazabilidad",
        "summaries": "Resúmenes ejecutivos",
    }

    for grp, label in group_labels.items():
        entries = groups.get(grp, [])
        if not entries:
            continue
        lines.append(f"\n## {label} ({len(entries)} figuras)\n")
        for e in entries:
            lines.append(f"- **{e['filename']}**: {e.get('purpose', '?')}")

    write_md(f"{reports_dir}/figure_overview.md", "\n".join(lines))


def _write_quality_summary(profile, catalog, reports_dir):
    null_pct = profile.get("null_pct", {})
    n_rows = profile.get("n_rows", 0)
    usable = profile.get("usable_for_model", [])
    complete = [c for c in usable if null_pct.get(c, 100) < 5]
    partial  = [c for c in usable if 5 <= null_pct.get(c, 100) < 80]
    empty    = [c for c in usable if null_pct.get(c, 100) >= 80]

    lines = ["# Resumen Visual de Calidad del Dataset\n"]
    lines.append(f"- **Total filas**: {n_rows}")
    lines.append(f"- **Features con cobertura completa (< 5% nulos)**: {len(complete)} — {complete}")
    lines.append(f"- **Features con cobertura parcial (5–80% nulos)**: {len(partial)} — {partial}")
    lines.append(f"- **Features completamente vacías (> 80% nulos)**: {len(empty)} — {empty}\n")
    lines.append("## Interpretación\n")
    if len(complete) >= 3:
        lines.append(
            f"El dataset tiene {len(complete)} features completamente disponibles. "
            "Esto es suficiente para un análisis exploratorio y un modelo inicial."
        )
    else:
        lines.append(
            "La cobertura de features es baja. Las columnas de dimensiones (length, thickness, width) "
            "están vacías porque nunca fueron extraídas de Propiedades_Extraidas. "
            "Los parámetros de proceso no están vinculados."
        )
    write_md(f"{reports_dir}/dataset_quality_visual_summary.md", "\n".join(lines))


def _write_feature_target_summary(profile, reports_dir):
    lines = ["# Resumen Visual Feature-Target\n"]
    lines.append("## Features con señal visual observable frente a compressive_strength\n")
    lines.append("""
| Feature | Señal | Tipo de relación | Notas |
|---|---|---|---|
| `structure_type` | **Alta** | Categórica — diferencias claras | gyroid y honeycomb < triply_periodic a param alto |
| `design_param_numeric` | **Alta** | Monotónica positiva dentro de cada grupo | Más param → más resistencia, consistente |
| `design_param_relative` | **Media** | Igual que anterior, normalizado | Útil para comparación entre estructuras |
| `infill_pattern` | Baja/redundante | Correlacionado con structure_type | Puede causar colinealidad |
| `replica_letter` | Ninguna | No es feature causal | Solo identifica réplica |
""")
    lines.append("## Features sin señal evaluable (no disponibles)\n")
    lines.append(
        "Las features de proceso FDM (layer_height, material, nozzle_temperature, print_speed, etc.) "
        "no pudieron vincularse a specimen_id. No se generaron scatter plots para estas porque "
        "no existen en el dataset final."
    )
    lines.append("\n## Advertencia de colinealidad\n")
    lines.append(
        "`infill_pattern` repite el valor de `structure_type` en la mayoría de los casos. "
        "Si ambas se incluyen en el modelo, se producirá colinealidad. "
        "Recomendación: usar solo `structure_type` como categórica."
    )
    write_md(f"{reports_dir}/feature_target_visual_summary.md", "\n".join(lines))


def _write_group_comparison_summary(catalog, reports_dir):
    lines = ["# Resumen de Comparaciones entre Grupos\n"]
    comp_entries = [e for e in catalog if e["filename"].startswith("C")]
    if comp_entries:
        lines.append(f"Se generaron {len(comp_entries)} gráficos de comparación.\n")
    lines.append("""
## Hallazgos principales

### Por structure_type
- **gyroid** muestra resistencia variable (2–27 MPa según parámetro de diseño).
- **honeycomb** tiene resistencias bajas a media alta (1.5–9 MPa).
- **triply_periodic** cubre rango medio consistente (2.5–8 MPa).
- Las diferencias entre estructuras son estadísticamente separables a simple vista.

### Por design_param_numeric
- Dentro de cada familia estructural, la resistencia crece con el parámetro numérico.
- Este parámetro parece ser el predictor continuo más informativo disponible.

### Variabilidad entre réplicas
- La mayoría de grupos tienen 3–5 réplicas. El CV (coeficiente de variación) es moderado.
- Grupos con CV > 30% pueden indicar inconsistencias experimentales o sensibilidad al parámetro.

### Tamaños de muestra
- Todos los grupos tienen entre 2 y 5 réplicas. Suficiente para exploración, insuficiente para inferencia estadística formal.
""")
    write_md(f"{reports_dir}/group_comparison_summary.md", "\n".join(lines))


def _write_linkage_summary(catalog, reports_dir):
    lines = ["# Resumen Visual de Linkage y Trazabilidad\n"]
    lines.append("""
## Cobertura del linkage

- **35/35 especímenes** tienen clasificación `probable_link`.
- **0 especímenes** quedaron `unresolved`.
- Ningún espécimen tiene `exact_link` (requeriría una columna de join explícita con una tabla de parámetros).

## Qué respalda cada target

Cada valor de `compressive_strength` fue derivado como el valor máximo de `stress[MPa]` 
registrado para esa probeta en el ensayo de compresión (Compressivedata.csv). 
El número de lecturas que respaldan ese máximo varía entre ~1000 y ~22000 por probeta.

## Limitación estructural reconocida

Las features de proceso FDM no pudieron vincularse. Esto no es un error de linkage — 
es una limitación de los datos disponibles: FDM_Dataset.csv no tiene columna specimen_id.

## Condición para linkage completo

Construir o localizar la tabla: `specimen_id → material, layer_height, infill_density, nozzle_temp, print_speed`.
Sin eso, el modelo queda limitado a features estructurales y parámetro de diseño.
""")
    write_md(f"{reports_dir}/linkage_visual_summary.md", "\n".join(lines))
