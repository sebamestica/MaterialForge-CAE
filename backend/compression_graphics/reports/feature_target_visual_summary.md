# Resumen Visual Feature-Target

## Features con señal visual observable frente a compressive_strength


| Feature | Señal | Tipo de relación | Notas |
|---|---|---|---|
| `structure_type` | **Alta** | Categórica — diferencias claras | gyroid y honeycomb < triply_periodic a param alto |
| `design_param_numeric` | **Alta** | Monotónica positiva dentro de cada grupo | Más param → más resistencia, consistente |
| `design_param_relative` | **Media** | Igual que anterior, normalizado | Útil para comparación entre estructuras |
| `infill_pattern` | Baja/redundante | Correlacionado con structure_type | Puede causar colinealidad |
| `replica_letter` | Ninguna | No es feature causal | Solo identifica réplica |

## Features sin señal evaluable (no disponibles)

Las features de proceso FDM (layer_height, material, nozzle_temperature, print_speed, etc.) no pudieron vincularse a specimen_id. No se generaron scatter plots para estas porque no existen en el dataset final.

## Advertencia de colinealidad

`infill_pattern` repite el valor de `structure_type` en la mayoría de los casos. Si ambas se incluyen en el modelo, se producirá colinealidad. Recomendación: usar solo `structure_type` como categórica.