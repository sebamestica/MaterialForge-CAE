import json
from pathlib import Path
from src.utils import write_md, write_json, md_table


def export_linkage_outputs(
    source_inventory, registry, parsed_registry, interpretation_notes,
    linked_registry, validated_registry, link_counts,
    dataset_summary, df_hc, df_exp, df_unresolved,
    reports_dir, artifacts_dir, logger
):
    logger.info("=== Exportando reportes y artefactos de linkage ===")

    _write_source_inventory(source_inventory, reports_dir)
    _write_specimen_registry(validated_registry, reports_dir)
    _write_linkage_decisions(interpretation_notes, linked_registry, validated_registry, reports_dir)
    _write_unresolved(df_unresolved, validated_registry, reports_dir)
    _write_final_model_report(dataset_summary, validated_registry, link_counts, reports_dir)

    write_json(
        f"{artifacts_dir}/linkage_tables/full_linkage_table.json",
        {sid: {k: v for k, v in info.items() if k not in ("features_missing", "cannot_infer_reason")}
         for sid, info in validated_registry.items()}
    )

    logger.info("  Todos los reportes exportados.")


def _write_source_inventory(source_inventory, reports_dir):
    lines = ["# Inventario de Fuentes para Linkage\n"]
    lines.append(
        "Este inventario cubre todos los archivos inspeccionados para evaluar si "
        "contienen información que permita vincular probetas compresivas con features.\n"
    )
    headers = ["Archivo", "Tipo", "Tiene ID de probeta", "Filas", "Utilidad para linkage"]
    rows = []
    for name, info in source_inventory.items():
        has_id = "Sí" if info.get("has_explicit_specimen_col") else "No"
        rows.append([
            name,
            info.get("type", "?"),
            has_id,
            info.get("n_rows_approx", "N/A"),
            info.get("notes", "")[:100],
        ])
    lines.append(md_table(headers, rows))

    lines.append("\n\n## Diagnóstico de linkage por archivo\n")
    for name, info in source_inventory.items():
        lines.append(f"\n### `{name}`\n")
        lines.append(f"- **Tipo**: {info.get('type')}")
        lines.append(f"- **Tiene columna de ID de probeta**: {info.get('has_explicit_specimen_col', False)}")
        lines.append(f"- **Notas**: {info.get('notes', '')}")
        if info.get("potential"):
            lines.append(f"- **Features potenciales**: {', '.join(info['potential'])}")

    write_md(f"{reports_dir}/source_inventory.md", "\n".join(lines))


def _write_specimen_registry(validated_registry, reports_dir):
    lines = ["# Registro Maestro de Probetas Compresivas\n"]
    lines.append(f"Total de probetas: **{len(validated_registry)}**\n")

    headers = ["Specimen ID", "Structure", "Param Numérico", "Réplica",
               "Comp. Strength (MPa)", "N Lecturas", "Features Enlazadas", "Confianza"]
    rows = []
    for sid, info in sorted(validated_registry.items()):
        features = info.get("features", {})
        rows.append([
            sid,
            features.get("structure_type", "?"),
            features.get("design_param_numeric", "?"),
            features.get("replica_letter", "?"),
            f"{info.get('compressive_strength_max', float('nan')):.3f}",
            info.get("n_readings", "?"),
            info.get("n_features_total", 0),
            info.get("linkage_confidence", "?"),
        ])
    lines.append(md_table(headers, rows))

    lines.append("\n\n## Distribución por confianza\n")
    from collections import Counter
    dist = Counter(info.get("linkage_confidence") for info in validated_registry.values())
    for k, v in dist.items():
        lines.append(f"- `{k}`: {v} probetas")

    write_md(f"{reports_dir}/specimen_registry.md", "\n".join(lines))


def _write_linkage_decisions(interpretation_notes, linked_registry, validated_registry, reports_dir):
    lines = ["# Decisiones de Linkage\n"]

    lines.append("## Reglas de enlace aplicadas\n")
    lines.append("""
| Feature | Fuente | Método | Confianza |
|---|---|---|---|
| `structure_type` | Specimen ID prefix | Parse directo (G→gyroid, H→honeycomb, T→triply_periodic) | exact_link |
| `infill_pattern` | Structure type | Implicación directa (structure_type → infill_pattern) | exact_link |
| `design_param_numeric` | Specimen ID number | Parse del componente numérico del ID | probable_link |
| `design_param_relative` | design_param_numeric | Normalización min-max dentro del grupo de prefijo | probable_link |
| `replica_letter` | Specimen ID suffix | Parse del sufijo alfabético | exact_link |
| Dimensiones (length, thickness, etc.) | Propiedades_Extraidas | Join por specimen_id | exact_link (si disponible) |
""")

    lines.append("## Interpretación del componente numérico del ID\n")
    for prefix, interp in interpretation_notes.items():
        lines.append(f"\n### Prefijo `{prefix}` — {interp.get('structure', '?')}\n")
        lines.append(f"- Valores únicos encontrados: {interp.get('unique_numeric_values')}")
        lines.append(f"- Variantes: {interp.get('n_variants')}")
        lines.append(f"- Interpretación: {interp.get('interpretation', '')}")

    lines.append("\n\n## Por qué no se puede unir con FDM_Dataset\n")
    lines.append("""
`FDM_Dataset_cleaned.csv` contiene 50 filas de parámetros de proceso FDM (layer_height, infill_density, 
nozzle_temperature, print_speed, etc.) pero **no tiene columna `specimen_id`**. 

No existe ninguna columna o archivo que mapee explícitamente una fila de `FDM_Dataset` 
a un ID de probeta como `G29A` o `H44B`. El archivo `Propiedades_Extraidas` lista los IDs 
pero todas sus columnas numéricas para las probetas compresivas están vacías.

Sin una tabla de mapeo explícita `specimen_id → FDM_params`, cualquier unión sería especulación.
Esta limitación es definitiva con los datos actualmente disponibles.
""")

    write_md(f"{reports_dir}/linkage_decisions.md", "\n".join(lines))


def _write_unresolved(df_unresolved, validated_registry, reports_dir):
    lines = ["# Casos No Resueltos\n"]

    unresolved = [
        (sid, info) for sid, info in validated_registry.items()
        if not info.get("usable_expanded")
    ]

    if not unresolved:
        lines.append("Todos los especímenes fueron clasificados como utilizables (probable_link o weak_link).\n")
        lines.append("Ningún espécimen fue completamente no resuelto.\n")
    else:
        lines.append(f"**{len(unresolved)}** especímenes no resueltos:\n")
        headers = ["Specimen ID", "Confianza", "Qué faltó", "¿Resoluble manualmente?"]
        rows = []
        for sid, info in unresolved:
            rows.append([
                sid,
                info.get("linkage_confidence", "?"),
                ", ".join(info.get("features_missing", [])[:5]),
                "Sí — requiere tabla manual de mapeo ID→parámetros",
            ])
        lines.append(md_table(headers, rows))

    lines.append("\n\n## Features sistemáticamente faltantes para TODAS las probetas\n")
    lines.append("""
Las siguientes features no pudieron enlazarse para NINGUNA probeta compresiva 
porque no existen en ningún archivo con un vínculo explícito a specimen_id:

| Feature | Razón |
|---|---|
| `material` | FDM_Dataset no tiene specimen_id. Sin mapeo no se puede asignar. |
| `layer_height` | Ídem. |
| `nozzle_temperature` | Ídem. |
| `print_speed` | Ídem. |
| `bed_temperature` | Ídem. |
| `cell_size_mm` | No aparece en ningún archivo. El número en el ID puede aproximarlo. |
| `wall_thickness_mm` | No aparece en ningún archivo. |
| `strut_thickness_mm` | No aparece en ningún archivo. |
| `print_orientation` | No aparece en ningún archivo. |

**Cómo resolverlo manualmente**: construir una tabla `specimen_id,layer_height,infill_density,...`
con los parámetros reales de cada probeta a partir del protocolo experimental original.
""")

    write_md(f"{reports_dir}/unresolved_cases.md", "\n".join(lines))


def _write_final_model_report(dataset_summary, validated_registry, link_counts, reports_dir):
    hc = dataset_summary.get("high_confidence", {})
    exp = dataset_summary.get("expanded_with_caution", {})
    unresolved_n = dataset_summary.get("unresolved_count", 0)

    total = len(validated_registry)
    usable_hc = hc.get("rows", 0)
    usable_exp = exp.get("rows", 0)

    lines = ["# Reporte Final del Dataset de Modelado\n"]

    model_ready = usable_hc >= 20 and len(hc.get("feature_cols", [])) >= 3

    if model_ready:
        lines.append("> [!NOTE]")
        lines.append(f"> El dataset high_confidence ({usable_hc} especímenes) está **listo para modelado inicial**.")
        lines.append("> Las limitaciones deben leerse antes de entrenar.\n")
    else:
        lines.append("> [!CAUTION]")
        lines.append(
            f"> El dataset resultante tiene features limitadas (solo estructura e índice de diseño). "
            f"Es válido para modelado exploratorio pero no para predicción industrial robusta. "
            f"El bloqueo se levanta parcialmente — se puede entrenar con conciencia de las limitaciones.\n"
        )

    lines.append("\n## Resumen\n")
    lines.append(f"- Total probetas auditadas: **{total}**")
    lines.append(f"- Probetas en dataset high_confidence: **{usable_hc}**")
    lines.append(f"- Probetas en dataset expanded_with_caution: **{usable_exp}**")
    lines.append(f"- Probetas no resueltas: **{unresolved_n}**")

    lines.append(f"\n## Dataset high_confidence\n")
    lines.append(f"- **Filas**: {hc.get('rows', 0)}")
    lines.append(f"- **Features disponibles**: {hc.get('feature_cols', [])}")
    lines.append(f"- **Target**: {hc.get('target', '?')}")
    lines.append(f"- **Path**: `{hc.get('path', '?')}`")

    lines.append(f"\n## Dataset expanded_with_caution\n")
    lines.append(f"- **Filas**: {exp.get('rows', 0)}")
    lines.append(f"- **Features disponibles**: {exp.get('feature_cols', [])}")
    lines.append(f"- **Target**: {exp.get('target', '?')}")
    lines.append(f"- **Path**: `{exp.get('path', '?')}`")

    lines.append(f"\n## Qué puede y qué no puede modelar este dataset\n")
    lines.append("""
### Puede modelar:
- Efecto del **tipo de estructura** (gyroid, honeycomb, triply_periodic) sobre `compressive_strength`.
- Efecto del **parámetro de diseño numérico** (relativo: densidad relativa o índice de celda) sobre `compressive_strength`.
- Variabilidad entre réplicas del mismo diseño (letra de réplica).

### No puede modelar (sin datos adicionales):
- Efecto de parámetros de impresión FDM (layer_height, temperature, speed) — no vinculados.
- Efecto del material — desconocido por probeta.
- Efecto de la orientación de impresión.
- Comparación entre familias de material (PLA vs PETG vs ABS para estas probetas).

### Limitaciones abiertas:
1. `design_param_numeric` es un índice extraído del ID. Su unidad física real (mm, %, etc.) es desconocida sin el protocolo experimental.
2. `design_param_relative` normaliza el índice dentro del grupo de estructura — útil para comparación relativa, no absoluta.
3. Sin parámetros de proceso, el modelo no puede usarse para optimizar parámetros de fabricación.

### Condición de desbloqueo total:
Construir manualmente (o encontrar en el repositorio original) la tabla de mapeo:
`specimen_id → layer_height, material, infill_density, nozzle_temp, print_speed, ...`

Con esa tabla, el dataset puede expandirse a 10+ features de proceso y convertirse en un predictor industrial real.
""")

    write_md(f"{reports_dir}/final_model_dataset_report.md", "\n".join(lines))
