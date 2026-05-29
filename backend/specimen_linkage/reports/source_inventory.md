# Inventario de Fuentes para Linkage

Este inventario cubre todos los archivos inspeccionados para evaluar si contienen información que permita vincular probetas compresivas con features.

|Archivo|Tipo|Tiene ID de probeta|Filas|Utilidad para linkage|
|---|---|---|---|---|
|Compressivedata_cleaned.csv|timeseries_compressive|Sí|169686|High-frequency sensor log. specimen_id in column 'probeta'. No process parameters present.|
|Propiedades_Extraidas_cleaned.csv|summary_table|Sí|100|Lists all compressive specimen IDs via 'sheet' column. All numeric property columns (max_force, modu|
|FDM_Dataset_cleaned.csv|process_parameters|No|50|50 rows of FDM print parameters. NO specimen_id column. Has 'microstructure' (fine/coarse) and 'mate|
|data_cleaned.csv|process_result_tensile|No|50|50 rows of tensile test results with print parameters. No specimen_id column. Tensile data — not com|
|TensiondataA_cleaned.csv|timeseries_tension|Sí|26228|Tension test time-series. Specimen IDs are for tension specimens (Sol.A, Sol.B, G36A, G55B...) — DIF|
|TensiondataB_cleaned.csv|timeseries_tension|Sí|5514|Tension test time-series for a second batch. Specimen IDs (10RA, 36RB, 55TA...) use DIFFERENT naming|
|Normalization/config/column_mappings.json|metadata|No|None|Column rename mappings. Confirms column structure of each file. No specimen-level linkage informatio|
|Normalization/config/file_registry.json|metadata|No|None|Dataset registry. No specimen-level data.|
|model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv|derived_compressive_dataset|No|None|The 35 valid compressive specimens aggregated. Starting point for linkage.|
|data/Proyecto_Machine_Learning/printer_dataset.py|analysis_script|No|None|ML script from the original author (AFUMETTO, 2018). Works only on data.csv (tensile). No references|


## Diagnóstico de linkage por archivo


### `Compressivedata_cleaned.csv`

- **Tipo**: timeseries_compressive
- **Tiene columna de ID de probeta**: True
- **Notas**: High-frequency sensor log. specimen_id in column 'probeta'. No process parameters present.
- **Features potenciales**: specimen_ids, stress_per_reading

### `Propiedades_Extraidas_cleaned.csv`

- **Tipo**: summary_table
- **Tiene columna de ID de probeta**: True
- **Notas**: Lists all compressive specimen IDs via 'sheet' column. All numeric property columns (max_force, modulo_young, etc.) are EMPTY for compressive entries. Dimension columns (length, thickness, width, transverse_area) are present but also EMPTY.
- **Features potenciales**: specimen_ids, dim_length, dim_thickness, dim_width, transverse_area

### `FDM_Dataset_cleaned.csv`

- **Tipo**: process_parameters
- **Tiene columna de ID de probeta**: False
- **Notas**: 50 rows of FDM print parameters. NO specimen_id column. Has 'microstructure' (fine/coarse) and 'material_type' (pure/composite). Cannot be joined to specimens — no shared key.
- **Features potenciales**: layer_height_mm, infill_density_%, infill_pattern, material, microstructure, material_type, print_speed_mm_s, melting_temperature_c

### `data_cleaned.csv`

- **Tipo**: process_result_tensile
- **Tiene columna de ID de probeta**: False
- **Notas**: 50 rows of tensile test results with print parameters. No specimen_id column. Tensile data — not compressive. Cannot link to compressive specimens.
- **Features potenciales**: layer_height, infill_density, material, infill_pattern

### `TensiondataA_cleaned.csv`

- **Tipo**: timeseries_tension
- **Tiene columna de ID de probeta**: True
- **Notas**: Tension test time-series. Specimen IDs are for tension specimens (Sol.A, Sol.B, G36A, G55B...) — DIFFERENT experiment from compressive. Not linkable to compressive specimens.
- **Features potenciales**: specimen_ids

### `TensiondataB_cleaned.csv`

- **Tipo**: timeseries_tension
- **Tiene columna de ID de probeta**: True
- **Notas**: Tension test time-series for a second batch. Specimen IDs (10RA, 36RB, 55TA...) use DIFFERENT naming convention. Not linkable to compressive specimens.
- **Features potenciales**: specimen_ids

### `Normalization/config/column_mappings.json`

- **Tipo**: metadata
- **Tiene columna de ID de probeta**: False
- **Notas**: Column rename mappings. Confirms column structure of each file. No specimen-level linkage information.
- **Features potenciales**: column_name_mappings

### `Normalization/config/file_registry.json`

- **Tipo**: metadata
- **Tiene columna de ID de probeta**: False
- **Notas**: Dataset registry. No specimen-level data.
- **Features potenciales**: value_score, reliability_score, status

### `model_data_audit/artifacts/candidate_targets/candidate_A_compressive_only.csv`

- **Tipo**: derived_compressive_dataset
- **Tiene columna de ID de probeta**: False
- **Notas**: The 35 valid compressive specimens aggregated. Starting point for linkage.
- **Features potenciales**: specimen_ids, compressive_strength, structure_type

### `data/Proyecto_Machine_Learning/printer_dataset.py`

- **Tipo**: analysis_script
- **Tiene columna de ID de probeta**: False
- **Notas**: ML script from the original author (AFUMETTO, 2018). Works only on data.csv (tensile). No references to specimen IDs or compressive data. Not useful for linkage.