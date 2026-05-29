# Arquitectura Maestra de Compresión

Este repositorio es una derivación oficial enfocada EXCLUSIVAMENTE en el Modelado Productivo de esfuerzos de test mecánicos a Compresión para prototipos FDM. Corrige el flujo heredado previo y descarta permanentemente cualquier dataset de procedencia "raw" ambiguo, de "tensión" o con leakage experimental.

## Fuente de Verdad Inmutable
Este pipeline se alimenta directamente de la carpeta de Enlaces de Alta Confianza (`specimen_linkage`). El motor descarta automáticamente cualquier registro que no mantenga vínculo probatorio hacia una probeta ensayada, por ende:
1. `data.csv` e inventarios paramétricos están descartados aquí.
2. `Tensiondata...` fue desvinculado logicamente para no ensuciar la inferencia en predicciones físicas que operan elástica/plásticamente distinto a tensión.

## Ejecución Pura
Situáte como usuario en el directorio principal o este folder y ejecuta:
```bash
python run_model_pipeline.py
```
El motor construirá de nuevo, documentando su escasez de filas u objeción real, evaluará Random Forests y Líneas de Inflexión, y depositará un único empaquetado final (`artifacts/best_model`) sin dejar rutas desprotegidas.
