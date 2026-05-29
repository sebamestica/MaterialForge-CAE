# specimen_linkage/

## Por qué esta fase era necesaria

La auditoría previa (`model_data_audit/`) confirmó que las 35 probetas compresivas de
`Compressivedata.csv` son el único dataset mecánicamente válido para modelar `compressive_strength`.
Sin embargo, esas probetas estaban **aisladas**: solo tenían su target (stress máximo por probeta)
pero ningún feature de proceso o geometría vinculado.

Sin features, no hay modelo. Esta fase resuelve eso.

---

## Qué problema corrige

La pipeline previa ignoró `Compressivedata.csv` por un fallo de detección de encabezado CSV.
Al rescatar las 35 probetas, el problema quedó desplazado: ahora existe un target válido pero
no hay features de proceso vinculadas porque **ningún archivo del proyecto mapea explícitamente
`specimen_id → parámetros FDM`**.

Esta fase hace un inventario honesto de qué puede enlazarse y qué no.

---

## Qué consume

| Fuente | Descripción |
|---|---|
| `model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv` | 35 probetas con target compresivo |
| `Normalization/cleaned/Propiedades_Extraidas_cleaned.csv` | IDs de probeta confirmados (dimensiones vacías) |
| `Normalization/cleaned/FDM_Dataset_cleaned.csv` | Parámetros FDM (sin specimen_id — no enlazable) |
| `Normalization/cleaned/Compressivedata_cleaned.csv` | Datos originales del ensayo |

No modifica ninguno de estos archivos.

---

## Qué produce

### Datasets (`data/linked_dataset/`)

| Dataset | Descripción |
|---|---|
| `high_confidence_dataset.csv` | Especímenes con links exactos o probables (estructura + param numérico) |
| `expanded_with_caution_dataset.csv` | Todos los especímenes enlazables (incluye weak_link) |
| `data/unresolved/unresolved_specimens.csv` | Especímenes sin suficientes features para modelo |

### Reportes (`reports/`)

| Reporte | Contenido |
|---|---|
| `source_inventory.md` | Archivos inspeccionados y utilidad de cada uno para linkage |
| `specimen_registry.md` | Tabla de todas las probetas con status de enlace |
| `linkage_decisions.md` | Reglas aplicadas, criterios, por qué FDM_Dataset no puede unirse |
| `unresolved_cases.md` | Features sistemáticamente faltantes y cómo resolverlas |
| `final_model_dataset_report.md` | Estado del dataset, qué puede y no puede modelar, condición de desbloqueo |

---

## Cómo se ejecuta

```bash
python specimen_linkage/run_specimen_linkage.py
```

Requiere haber ejecutado `model_data_audit/run_model_data_audit.py` primero (genera candidate_A).

---

## Cómo interpretar la confianza de los enlaces

| Nivel | Significado |
|---|---|
| `exact_link` | Feature extraída directamente de un archivo con key compartida (specimen_id) |
| `probable_link` | Feature inferida del ID del espécimen con lógica verificable (prefix→structure) |
| `weak_link` | Feature inferida pero con menor certeza (solo estructura tipo, sin param numérico) |
| `unresolved` | No se pudo enlazar ninguna feature útil |

---

## Qué features están disponibles vs faltantes

### Disponibles (para todos los especímenes):
- `structure_type` — del prefijo del ID (G→gyroid, H→honeycomb, T→triply_periodic) — **exact**
- `infill_pattern` — implicado por structure_type — **exact**
- `design_param_numeric` — del número del ID (probablemente densidad o tamaño de celda) — **probable**
- `design_param_relative` — normalización del anterior dentro del grupo — **probable**
- `replica_letter` — del sufijo del ID — **exact**

### No disponibles sin datos adicionales:
- `material`, `layer_height`, `nozzle_temperature`, `print_speed`, `bed_temperature`
- `cell_size_mm`, `wall_thickness_mm`, `strut_thickness_mm`, `print_orientation`

Razón: `FDM_Dataset_cleaned.csv` tiene estos parámetros pero **no tiene columna specimen_id**.
Sin una tabla de mapeo explícita, no se puede asignar parámetros de proceso a probetas específicas.

---

## Cuándo ya se puede pasar de nuevo a modelado

### Desbloqueo parcial (ya alcanzado):
El dataset `high_confidence_dataset.csv` tiene ~35 especímenes con 4–5 features.
Es suficiente para un **modelo exploratorio** que analice cómo el tipo de estructura y el parámetro
de diseño numérico afectan `compressive_strength`. Útil para análisis comparativo.

### Desbloqueo total (pendiente):
Construir manualmente (o encontrar en el repositorio original) una tabla:
```
specimen_id, material, layer_height, infill_density, nozzle_temp, print_speed, ...
G29A, PLA, 0.2, 29, 210, 40, ...
H44B, PLA, 0.2, 44, 210, 40, ...
...
```
Con esa tabla el dataset puede expandirse a 10+ features de proceso y convertirse en un predictor
industrial real que responda: *¿qué parámetros de impresión maximizan la resistencia compresiva?*
