# Reporte de Feature Engineering

## Features de Entrada (17)
- specimen_id, structure_type, infill_pattern, design_param_numeric, design_param_relative, replica_letter, length, thickness, width, transverse_area, compressive_strength, compressive_strength_mean, compressive_strength_std, n_readings, source_dataset, linkage_confidence, source_trace

## Features Derivadas
- Ninguna

## Features Excluidas
- `specimen_id` -> Razon: Leakage
- `replica_letter` -> Razon: Leakage
- `source_dataset` -> Razon: Leakage
- `linkage_confidence` -> Razon: Leakage
- `source_trace` -> Razon: Leakage
- `length` -> Razon: Columna Vacia
- `thickness` -> Razon: Columna Vacia
- `width` -> Razon: Columna Vacia
- `transverse_area` -> Razon: Columna Vacia

## Features Finales (8)
- structure_type, infill_pattern, design_param_numeric, design_param_relative, compressive_strength, compressive_strength_mean, compressive_strength_std, n_readings