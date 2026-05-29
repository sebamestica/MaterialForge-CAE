# Validación de Fuentes de Compresión

## Fuente seleccionada

- **ID**: `specimen_linkage_hc`
- **Label**: specimen_linkage high_confidence
- **Path**: `C:\dev\PLA_3dPrinter_RESISTENCE\specimen_linkage\data\linked_dataset\high_confidence_dataset.csv`
- **Filas**: 35
- **Columnas**: ['specimen_id', 'structure_type', 'infill_pattern', 'design_param_numeric', 'design_param_relative', 'replica_letter', 'length', 'thickness', 'width', 'transverse_area', 'compressive_strength', 'compressive_strength_mean', 'compressive_strength_std', 'n_readings', 'source_dataset', 'linkage_confidence', 'source_trace']
- **Checks**: {'file_exists': True, 'readable': True, 'has_target': True, 'tensile_free': True, 'has_traceability': True, 'target_null_pct': np.float64(0.0), 'target_has_values': True}


## Estado de todas las fuentes candidatas

|Source ID|Válida|Razón de rechazo|
|---|---|---|
|specimen_linkage_hc|✅|None|
|specimen_linkage_exp|✅|None|
|audit_candidate_A|✅|None|


## Fuentes de tracción (no usadas)

Las siguientes fuentes contienen datos de tracción y están explícitamente excluidas:
- `Normalization/cleaned/data_cleaned.csv` — tensile, 50 filas
- `Normalization/cleaned/TensiondataA_cleaned.csv` — tensile time-series
- `Normalization/cleaned/TensiondataB_cleaned.csv` — tensile time-series
- `model_data_audit/artifacts/candidate_targets/candidate_B_data_only.csv` — tensile mislabeled