# Artefactos Entrenados

Este subdirectorio funciona como la "nevera" de producción.

- `trained_models/`: Recibe archivos serializados (generalmente joblib / pickle) con los pipelines de scikit-learn empacados. Incluye tanto el procesador ColumnTransformer como el estimador en sí.
- `metrics/`: Contiene outputs en CSV sobre el desempeño. Permite trazabilidad, facilitando contrastar la métrica de un Random Forest hoy, contra un algoritmo modificado mañana.
- Funciona estrictamente de append o de sobreeescritura controlada y es la carpeta que será consumida si construyéramos una API que despliegue el modelo.
