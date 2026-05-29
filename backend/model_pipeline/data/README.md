# Módulo de Datos de Entrenamiento

Esta carpeta aloja los datasets estáticos consolidados y fraccionados, producto inmediato del script de ingesta de modelado.

- `model_input/`: Contiene el `raw_model_input.csv`, el cual es la concatenación vertical consolidada de las sábanas de resultados válidos, antes del feature engineering.
- `processed/`: Dataset tras codificación, imputación de nulos y dropping de leakage columns.
- `train/`, `validation/`, `test/`: Subdivisiones estadísticas del dataset procesado, que aíslan el modelo y permiten una evaluación honesta, evitando el data leaking. Conforman el Gold Standard actual.
