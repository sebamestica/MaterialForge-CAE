# Revision de Validez del Modelo Actual

**Fecha de revision**: 2026-03-29 23:16

## 1. Identidad del Modelo

- **Modelo ganador**: GradientBoostingRegressor
- **Archivo**: `GradientBoostingRegressor_deployment_ready.pkl`
- **Target**: `compressive_strength`
- **Dataset fuente**: `high_confidence_dataset.csv` (35 filas)
- **Split**: Train=24, Val=4, Test=7

## 2. Features Utilizadas

**Features originales de entrada** (7): structure_type, infill_pattern, design_param_numeric, design_param_relative, compressive_strength_mean, compressive_strength_std, n_readings

**Features transformadas post-encoding** (11): num__design_param_numeric, num__design_param_relative, num__compressive_strength_mean, num__compressive_strength_std, num__n_readings, cat__structure_type_gyroid, cat__structure_type_honeycomb, cat__structure_type_triply_periodic, cat__infill_pattern_gyroid, cat__infill_pattern_honeycomb, cat__infill_pattern_triply_periodic

### Features excluidas del master

- `specimen_id` → leakage/traceability
- `replica_letter` → leakage/traceability
- `length` → empty/irrelevant
- `thickness` → empty/irrelevant
- `width` → empty/irrelevant
- `transverse_area` → empty/irrelevant
- `source_dataset` → leakage/traceability
- `linkage_confidence` → leakage/traceability
- `source_trace` → leakage/traceability

## 3. Metricas de Desempeno

| Split | R² | MAE | RMSE | MAPE (%) |
|-------|-----|-----|------|----------|
| Train | 0.9999 | 0.0487 | - | - |
| Test  | 0.9733 | 0.3925 | 0.4953 | 15.4 |

**Brecha de sobreajuste (Train R² - Test R²)**: 0.0266

> Brecha baja. Buena generalizacion relativa al tamano del dataset.

## 4. Analisis de Riesgo de Leakage

### ALERTA: Features con riesgo de leakage detectadas

- **`compressive_strength_mean`**: HIGH - contains aggregated target statistics
- **`compressive_strength_std`**: MODERATE - standard deviation of target readings
- **`n_readings`**: LOW - number of readings, proxy for test duration

> **Interpretacion**: Las features `compressive_strength_mean` y `compressive_strength_std` son estadisticas agregadas de las lecturas del ensayo de compresion de cada probeta. Dado que el target `compressive_strength` es el maximo stress de esos mismos ensayos, estas features estan **estadisticamente correlacionadas con el target por construccion**, no por senal fisica independiente. Esto constituye un **leakage estadistico parcial** que infla el R² reportado. El modelo esta aprendiendo en parte una relacion matematica (max ≈ f(mean, std, n)) en lugar de una relacion fisica pura entre parametros de diseno y resistencia.

> **Impacto estimado**: El R² real sin estas features seria sustancialmente menor. Esto no invalida la utilidad del modelo como prototipo, pero **impide llamarlo predictor independiente**.

## 5. Coherencia Dataset-Desempeno

- **Ratio muestras/features**: 3.4 (train=24, features_raw=7)
- **Ratio muestras/features_transformadas**: 2.2
- **CRITICO**: El ratio muestras/features es demasiado bajo para inferencia confiable.

- **Tamano test set**: 7 muestras. Demasiado pequeno para conclusiones estadisticamente robustas sobre R². Un R² de 0.973 sobre 7 muestras tiene alta varianza.

## 6. Conclusion de Validez

### Por que el modelo es mecanicamente valido

1. Se entreno exclusivamente sobre datos de compresion verificados (high_confidence_dataset)
2. No contiene datos tensiles
3. El pipeline aplica correctamente exclusion de columnas de trazabilidad
4. La estructura train/val/test fue aplicada con random split (seed=42)
5. El modelo supera significativamente al baseline DummyRegressor

### Por que NO debe llamarse solucion definitiva

1. **Dataset de 35 filas**: insuficiente para validacion estadistica robusta
2. **Leakage estadistico parcial**: `compressive_strength_mean` y `compressive_strength_std` son derivadas del mismo ensayo que produce el target
3. **Test set de 7 muestras**: el R² reportado tiene alta varianza por particion
4. **Sin parametros de proceso**: el modelo no puede predecir el efecto de cambios en impresion (layer_height, temperature, speed)
5. **Solo 3 tipos de estructura y ~3 niveles de design_param por tipo**: el espacio de diseno explorado es muy estrecho

### Nivel de confianza actual: **moderada-baja (inflada por leakage parcial)**

El modelo es un **prototipo valido** para analisis direccional. Captura tendencias generales entre tipo de estructura, parametro de diseno y resistencia compresiva. No es adecuado para prediccion industrial ni para decisiones de garantia estructural.
