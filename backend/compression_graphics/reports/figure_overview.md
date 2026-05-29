# Resumen de Figuras Generadas

**Total de figuras generadas**: 23


## Calidad del dataset (5 figuras)

- **Q01_missing_values_heatbar.png**: ¿Qué columnas tienen datos faltantes y en qué proporción?
- **Q02_valid_obs_per_column.png**: ¿Cuántas observaciones válidas tiene cada columna?
- **Q03_linkage_confidence_distribution.png**: ¿Qué porcentaje del dataset tiene enlace probable vs exacto vs no resuelto?
- **Q04_specimens_by_source.png**: ¿De qué dataset provienen los especímenes y cuántos hay?
- **Q05_feature_completeness.png**: ¿Qué features tienen cobertura completa y cuáles son parciales?

## Distribución del target (4 figuras)

- **T01_target_histogram_kde.png**: ¿Cómo se distribuye el target? ¿Está sesgado? ¿Tiene buena variabilidad?
- **T02_target_boxplot_ranges.png**: ¿Hay outliers? ¿Están bien cubiertos los rangos de resistencia?
- **T03_target_qqplot.png**: ¿El target sigue distribución normal? Relevante para elección de modelo.
- **T04_target_stats_summary.png**: Resumen estadístico completo del target en formato visual.

## Relaciones feature-target (3 figuras)

- **R01_numeric_features_vs_target.png**: ¿Qué features numéricas muestran señal visual frente al target? ¿Hay no linealidades?
- **R02_correlation_heatmap.png**: ¿Qué features están correlacionadas entre sí y con el target?
- **R03_design_param_vs_target_by_structure.png**: ¿Cómo varía compressive_strength con el parámetro de diseño dentro de cada familia estructural?

## Comparaciones por grupo (4 figuras)

- **CST_boxplot_mean_by_structure_type.png**: ¿Difiere compressive_strength significativamente por structure_type?
- **CIN_boxplot_mean_by_infill_pattern.png**: ¿Difiere compressive_strength significativamente por infill_pattern?
- **C03_target_by_structure_and_param.png**: ¿Cómo interactúan tipo de estructura y parámetro de diseño en la resistencia?
- **C04_replica_variability_cv.png**: ¿Cuánta variabilidad hay entre réplicas de un mismo diseño? ¿Son reproducibles?

## Linkage y trazabilidad (4 figuras)

- **L01_linkage_confidence_overview.png**: ¿Qué porcentaje del dataset tiene linkage probable vs exacto vs no resuelto?
- **L02_specimen_feature_completeness_heatmap.png**: ¿Qué features están disponibles para cada probeta? ¿Hay probetas con cobertura parcial?
- **L03_feature_availability_status.png**: ¿Cuáles son las features deseadas disponibles, cuáles están vacías y cuáles faltan por completo?
- **L04_readings_vs_strength_per_specimen.png**: ¿Cuántas lecturas respaldaron el valor de compressive_strength de cada probeta?

## Resúmenes ejecutivos (3 figuras)

- **S01_executive_summary.png**: Resumen de alto nivel: distribución del target, comparación por estructura, señal de parámetro de diseño, completitud y readiness del dataset.
- **S02_feature_signal_summary.png**: ¿Qué features tienen señal útil? ¿Cuáles faltan? ¿Cuáles son redundantes?
- **S03_dataset_limitations.png**: ¿Qué limitaciones estructurales tiene el dataset? ¿Qué impide un modelo robusto?