# Casos No Resueltos

Todos los especímenes fueron clasificados como utilizables (probable_link o weak_link).

Ningún espécimen fue completamente no resuelto.



## Features sistemáticamente faltantes para TODAS las probetas


Las siguientes features no pudieron enlazarse para NINGUNA probeta compresiva 
porque no existen en ningún archivo con un vínculo explícito a specimen_id:

| Feature | Razón |
|---|---|
| `material` | FDM_Dataset no tiene specimen_id. Sin mapeo no se puede asignar. |
| `layer_height` | Ídem. |
| `nozzle_temperature` | Ídem. |
| `print_speed` | Ídem. |
| `bed_temperature` | Ídem. |
| `cell_size_mm` | No aparece en ningún archivo. El número en el ID puede aproximarlo. |
| `wall_thickness_mm` | No aparece en ningún archivo. |
| `strut_thickness_mm` | No aparece en ningún archivo. |
| `print_orientation` | No aparece en ningún archivo. |

**Cómo resolverlo manualmente**: construir una tabla `specimen_id,layer_height,infill_density,...`
con los parámetros reales de cada probeta a partir del protocolo experimental original.
