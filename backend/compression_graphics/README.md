# compression_graphics/

## Propósito exacto

Esta carpeta es la **capa visual especializada para el análisis de `compressive_strength`** en el proyecto PLA_3dPrinter_RESISTENCE.

Existe específicamente para soportar el proceso de decisión sobre si el dataset final de compresión está listo para volver a modelar, qué features tienen señal útil, qué grupos están subrepresentados, y dónde persisten limitaciones estructurales irresolubles con los datos actuales.

---

## Por qué existe además de `graphics/`

`graphics/` genera visualizaciones generales de todo el proyecto: parámetros FDM, ensayos de tracción, exploración de todas las variables. Es útil para análisis exploratorio amplio.

`compression_graphics/` existe porque:
1. **El objetivo del proyecto es modelar `compressive_strength`**, no tensile strength.
2. La auditoría (`model_data_audit/`) descartó todos los datasets de tracción como inválidos para el target real.
3. El linkage de probetas (`specimen_linkage/`) produjo un dataset final con 35 especímenes compresivos y features específicas.
4. Visualizar ese dataset con las herramientas generales de `graphics/` mezclaría contextos y ofuscaría el análisis.

Esta carpeta garantiza que **cada figura responde una pregunta específica sobre el dataset correcto de compresión**.

---

## Qué problema corrige

`graphics/` incluía gráficos de tracción, de FDM_Dataset sin target válido, y de variables como `tension_strenght` y `elongation` que la auditoría marcó como **mecánicamente incorrectos** para el target actual.

`compression_graphics/` solo lee desde `specimen_linkage/data/linked_dataset/`, valida que la fuente sea compresiva, rechaza explícitamente datasets tensiles, y genera figuras únicamente para variables que existen y son útiles.

---

## Qué consume

| Fuente (prioridad) | Descripción |
|---|---|
| `specimen_linkage/data/linked_dataset/high_confidence_dataset.csv` | **Fuente principal** — 35 probetas, target compresivo, features enlazadas |
| `specimen_linkage/data/linked_dataset/expanded_with_caution_dataset.csv` | Fallback — mismos especímenes, clasificación expandida |
| `model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv` | Fallback — versión previa al linkage |

**Explícitamente rechazadas** (logged como `FORBIDDEN`):
- `Normalization/cleaned/data_cleaned.csv` — tensile
- `Normalization/cleaned/TensiondataA_cleaned.csv` — tensile time-series
- `Normalization/cleaned/TensiondataB_cleaned.csv` — tensile time-series
- `model_data_audit/artifacts/candidate_targets/candidate_B_data_only.csv` — tensile mislabeled

No modifica ningún archivo de otras carpetas.

---

## Qué produce

### Figuras (`outputs/`)

| Carpeta | Figuras | Propósito analítico |
|---|---|---|
| `quality/` | Q01–Q05 (5 figuras) | Completitud, missing, linkage, fuente, feature coverage |
| `targets/` | T01–T04 (4 figuras) | Distribución, KDE, boxplot, Q-Q, estadísticas del target |
| `relationships/` | R01–R03 (3 figuras) | Feature vs target scatter, correlación, param vs target por estructura |
| `comparisons/` | C01–C04 (4+ figuras) | Boxplot y media por estructura, infill, param×estructura, variabilidad réplicas |
| `linkage/` | L01–L04 (4 figuras) | Confianza de enlace, heatmap probeta×feature, disponibilidad, lecturas vs resistencia |
| `summaries/` | S01–S03 (3 figuras) | Dashboard ejecutivo, señal de features, limitaciones del dataset |
| `catalogs/` | CSV + MD | Catálogo completo de figuras con metadata |

### Reportes (`reports/`)

| Reporte | Contenido |
|---|---|
| `source_validation.md` | Fuente elegida, razón, fuentes rechazadas |
| `figure_overview.md` | Listado por categoría de todas las figuras y qué responden |
| `dataset_quality_visual_summary.md` | Hallazgos sobre completitud y gaps |
| `feature_target_visual_summary.md` | Qué features tienen señal útil, cuáles son redundantes |
| `group_comparison_summary.md` | Hallazgos por estructura, param, variabilidad entre réplicas |
| `linkage_visual_summary.md` | Evaluación visual de la confianza de enlace |

---

## Cómo ejecutar

```bash
python compression_graphics/run_compression_graphics.py
```

Requiere haber ejecutado previamente:
1. `model_data_audit/run_model_data_audit.py`
2. `specimen_linkage/run_specimen_linkage.py`

Dependencias: `matplotlib`, `pandas`, `numpy`, `scipy` (para KDE y Q-Q).

---

## Cómo interpretar las salidas

### Figuras de calidad (`Q*`)
- `Q01`: columnas rojas = deben ser ignoradas para modelado.
- `Q05`: solo features en verde tienen cobertura suficiente.

### Figuras del target (`T*`)
- `T01`: histograma + KDE — evalúa si el target está sesgado (asimetría positiva = sí).
- `T02`: boxplot + rangos — detecta outliers y cobertura de rango.
- `T03`: Q-Q plot — si los puntos se alejan de la línea, el target no es normal.
- `T04`: estadísticas en texto — referencia rápida para documentación técnica.

### Figuras de relaciones (`R*`)
- `R01`: scatter grid — una pendiente positiva visible = señal útil para el modelo.
- `R03`: el gráfico clave — `design_param_numeric` vs `compressive_strength` por estructura.

### Figuras de comparación (`C*`)
- `C03`: el más importante — interacción estructura × parámetro de diseño.
- `C04`: CV > 30% = variabilidad alta entre réplicas = posibles inconsistencias.

### Figuras de linkage (`L*`)
- `L02`: heatmap verde = dato disponible, rojo = nulo. Columnas rojas = features vacías.
- `L03`: verde = usable, rojo = ni siquiera en el dataset.

### Figuras resumen (`S*`)
- `S01`: dashboard 6-paneles — primera figura a leer para visión global.
- `S02`: qué features vale la pena incluir en el modelo y cuáles faltan.
- `S03`: limitaciones irresolubles — para comunicar honestamente el estado del proyecto.

---

## Qué límites tiene esta capa visual

1. **Solo 35 especímenes** — suficiente para exploración visual, insuficiente para inferencia estadística formal.
2. **Sin parámetros de proceso FDM** — layer_height, material, nozzle_temp no están en el dataset porque FDM_Dataset no tiene specimen_id.
3. **`design_param_numeric` en unidades desconocidas** — el valor numérico del ID es un índice, no una unidad física confirmada.
4. **Sin dimensiones físicas** — length, thickness, width están en el CSV pero vacías (Propiedades_Extraidas nunca fue extraída para las probetas compresivas).

---

## Por qué no debe usarse con datasets no validados

La validación (`validate_compression_sources.py`) verifica explícitamente:
- Que el CSV contenga `compressive_strength` como columna.
- Que no contenga `tension_strenght` ni `elongation`.
- Que el target no sea nulo.
- Que exista al menos traza de origen (`source_dataset` o `source_trace`).

Si el dataset no pasa esta validación, el sistema se detiene con un error claro y no genera ninguna figura. Esto evita que un dataset de tracción mislabeled contamine el análisis visual.
