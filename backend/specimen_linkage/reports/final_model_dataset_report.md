# Reporte Final del Dataset de Modelado

> [!NOTE]
> El dataset high_confidence (35 especímenes) está **listo para modelado inicial**.
> Las limitaciones deben leerse antes de entrenar.


## Resumen

- Total probetas auditadas: **35**
- Probetas en dataset high_confidence: **35**
- Probetas en dataset expanded_with_caution: **35**
- Probetas no resueltas: **0**

## Dataset high_confidence

- **Filas**: 35
- **Features disponibles**: ['structure_type', 'infill_pattern', 'design_param_numeric', 'design_param_relative', 'replica_letter', 'length', 'thickness', 'width', 'transverse_area']
- **Target**: compressive_strength (max stress per specimen, MPa)
- **Path**: `data\linked_dataset\high_confidence_dataset.csv`

## Dataset expanded_with_caution

- **Filas**: 35
- **Features disponibles**: ['structure_type', 'infill_pattern', 'design_param_numeric', 'design_param_relative', 'replica_letter', 'length', 'thickness', 'width', 'transverse_area']
- **Target**: compressive_strength (max stress per specimen, MPa)
- **Path**: `data\linked_dataset\expanded_with_caution_dataset.csv`

## Qué puede y qué no puede modelar este dataset


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
