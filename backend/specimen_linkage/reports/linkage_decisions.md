# Decisiones de Linkage

## Reglas de enlace aplicadas


| Feature | Fuente | Método | Confianza |
|---|---|---|---|
| `structure_type` | Specimen ID prefix | Parse directo (G→gyroid, H→honeycomb, T→triply_periodic) | exact_link |
| `infill_pattern` | Structure type | Implicación directa (structure_type → infill_pattern) | exact_link |
| `design_param_numeric` | Specimen ID number | Parse del componente numérico del ID | probable_link |
| `design_param_relative` | design_param_numeric | Normalización min-max dentro del grupo de prefijo | probable_link |
| `replica_letter` | Specimen ID suffix | Parse del sufijo alfabético | exact_link |
| Dimensiones (length, thickness, etc.) | Propiedades_Extraidas | Join por specimen_id | exact_link (si disponible) |

## Interpretación del componente numérico del ID


### Prefijo `G` — gyroid

- Valores únicos encontrados: [29, 42, 62]
- Variantes: 3
- Interpretación: The numeric component ([29, 42, 62]) likely encodes a design parameter such as relative density (%), cell size (mm), or strut thickness index. Values increase monotonically across groups, consistent with a density or size gradient. Exact physical meaning cannot be determined from filenames alone — requires original experimental protocol documentation.

### Prefijo `H` — honeycomb

- Valores únicos encontrados: [36, 44, 67]
- Variantes: 3
- Interpretación: The numeric component ([36, 44, 67]) likely encodes a design parameter such as relative density (%), cell size (mm), or strut thickness index. Values increase monotonically across groups, consistent with a density or size gradient. Exact physical meaning cannot be determined from filenames alone — requires original experimental protocol documentation.

### Prefijo `T` — triply_periodic

- Valores únicos encontrados: [24, 37, 45]
- Variantes: 3
- Interpretación: The numeric component ([24, 37, 45]) likely encodes a design parameter such as relative density (%), cell size (mm), or strut thickness index. Values increase monotonically across groups, consistent with a density or size gradient. Exact physical meaning cannot be determined from filenames alone — requires original experimental protocol documentation.

### Prefijo `TQ` — triply_periodic

- Valores únicos encontrados: [45]
- Variantes: 1
- Interpretación: The numeric component ([45]) likely encodes a design parameter such as relative density (%), cell size (mm), or strut thickness index. Values increase monotonically across groups, consistent with a density or size gradient. Exact physical meaning cannot be determined from filenames alone — requires original experimental protocol documentation.


## Por qué no se puede unir con FDM_Dataset


`FDM_Dataset_cleaned.csv` contiene 50 filas de parámetros de proceso FDM (layer_height, infill_density, 
nozzle_temperature, print_speed, etc.) pero **no tiene columna `specimen_id`**. 

No existe ninguna columna o archivo que mapee explícitamente una fila de `FDM_Dataset` 
a un ID de probeta como `G29A` o `H44B`. El archivo `Propiedades_Extraidas` lista los IDs 
pero todas sus columnas numéricas para las probetas compresivas están vacías.

Sin una tabla de mapeo explícita `specimen_id → FDM_params`, cualquier unión sería especulación.
Esta limitación es definitiva con los datos actualmente disponibles.
