# Analisis de Senal Fisica de Features

Este analisis evalua si las variables de entrada presentan una relacion monotonica o visible con la resistencia.

| Feature | Correlacion (Pearson) | Fuerza de Senal |
|---------|------------------------|------------------|
| compressive_strength_std | 0.9872 | Fuerte |
| compressive_strength_mean | 0.9306 | Fuerte |
| design_param_relative | 0.7338 | Fuerte |
| design_param_numeric | 0.6794 | Media |
| n_readings | -0.3534 | Debil |
| length | nan | Debil |
| thickness | nan | Debil |
| width | nan | Debil |
| transverse_area | nan | Debil |

## Interpretacion Fisica
- **design_param_numeric**: Presenta una correlacion de 0.679. Senal detectable pero no linealmente dominante por si sola.
- **compressive_strength_mean**: Feature critica con riesgo de leakage (estadistica agregada del mismo test). Su alta correlacion explica gran parte del R2 del modelo.
