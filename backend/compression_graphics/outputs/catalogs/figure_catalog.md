# Catálogo de Figuras — compression_graphics

Total generadas: **23** | No generadas: **0**

|Archivo|Categoría|Gráfico|Propósito analítico|
|---|---|---|---|
|Q01_missing_values_heatbar.png|barh_horizontal|barh_horizontal|¿Qué columnas tienen datos faltantes y en qué proporción?|
|Q02_valid_obs_per_column.png|barplot|barplot|¿Cuántas observaciones válidas tiene cada columna?|
|Q03_linkage_confidence_distribution.png|bar+pie|bar+pie|¿Qué porcentaje del dataset tiene enlace probable vs exacto vs no resuelto?|
|Q04_specimens_by_source.png|barh_horizontal|barh_horizontal|¿De qué dataset provienen los especímenes y cuántos hay?|
|Q05_feature_completeness.png|barh_horizontal|barh_horizontal|¿Qué features tienen cobertura completa y cuáles son parciales?|
|T01_target_histogram_kde.png|histogram+kde|histogram+kde|¿Cómo se distribuye el target? ¿Está sesgado? ¿Tiene buena variabilidad?|
|T02_target_boxplot_ranges.png|boxplot+barplot|boxplot+barplot|¿Hay outliers? ¿Están bien cubiertos los rangos de resistencia?|
|T03_target_qqplot.png|qqplot|qqplot|¿El target sigue distribución normal? Relevante para elección de modelo.|
|T04_target_stats_summary.png|text_summary|text_summary|Resumen estadístico completo del target en formato visual.|
|R01_numeric_features_vs_target.png|scatter_grid|scatter_grid|¿Qué features numéricas muestran señal visual frente al target? ¿Hay no linealid|
|R02_correlation_heatmap.png|heatmap_correlation|heatmap_correlation|¿Qué features están correlacionadas entre sí y con el target?|
|R03_design_param_vs_target_by_structure.png|scatter_colored_by_category|scatter_colored_by_category|¿Cómo varía compressive_strength con el parámetro de diseño dentro de cada famil|
|CST_boxplot_mean_by_structure_type.png|boxplot+barplot_mean_std|boxplot+barplot_mean_std|¿Difiere compressive_strength significativamente por structure_type?|
|CIN_boxplot_mean_by_infill_pattern.png|boxplot+barplot_mean_std|boxplot+barplot_mean_std|¿Difiere compressive_strength significativamente por infill_pattern?|
|C03_target_by_structure_and_param.png|boxplot_grouped|boxplot_grouped|¿Cómo interactúan tipo de estructura y parámetro de diseño en la resistencia?|
|C04_replica_variability_cv.png|barplot_cv|barplot_cv|¿Cuánta variabilidad hay entre réplicas de un mismo diseño? ¿Son reproducibles?|
|L01_linkage_confidence_overview.png|bar+pie|bar+pie|¿Qué porcentaje del dataset tiene linkage probable vs exacto vs no resuelto?|
|L02_specimen_feature_completeness_heatmap.png|heatmap_binary|heatmap_binary|¿Qué features están disponibles para cada probeta? ¿Hay probetas con cobertura p|
|L03_feature_availability_status.png|status_barchart|status_barchart|¿Cuáles son las features deseadas disponibles, cuáles están vacías y cuáles falt|
|L04_readings_vs_strength_per_specimen.png|dual_axis_bar_line|dual_axis_bar_line|¿Cuántas lecturas respaldaron el valor de compressive_strength de cada probeta?|
|S01_executive_summary.png|dashboard_static|dashboard_static|Resumen de alto nivel: distribución del target, comparación por estructura, seña|
|S02_feature_signal_summary.png|status_signal_barchart|status_signal_barchart|¿Qué features tienen señal útil? ¿Cuáles faltan? ¿Cuáles son redundantes?|
|S03_dataset_limitations.png|limitations_chart|limitations_chart|¿Qué limitaciones estructurales tiene el dataset? ¿Qué impide un modelo robusto?|