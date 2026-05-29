# Resumen Visual de Linkage y Trazabilidad


## Cobertura del linkage

- **35/35 especímenes** tienen clasificación `probable_link`.
- **0 especímenes** quedaron `unresolved`.
- Ningún espécimen tiene `exact_link` (requeriría una columna de join explícita con una tabla de parámetros).

## Qué respalda cada target

Cada valor de `compressive_strength` fue derivado como el valor máximo de `stress[MPa]` 
registrado para esa probeta en el ensayo de compresión (Compressivedata.csv). 
El número de lecturas que respaldan ese máximo varía entre ~1000 y ~22000 por probeta.

## Limitación estructural reconocida

Las features de proceso FDM no pudieron vincularse. Esto no es un error de linkage — 
es una limitación de los datos disponibles: FDM_Dataset.csv no tiene columna specimen_id.

## Condición para linkage completo

Construir o localizar la tabla: `specimen_id → material, layer_height, infill_density, nozzle_temp, print_speed`.
Sin eso, el modelo queda limitado a features estructurales y parámetro de diseño.
