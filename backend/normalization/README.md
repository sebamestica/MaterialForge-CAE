# Pipeline de Normalización
Pipeline modular y reproducible para el descubrimiento, perfilado, limpieza y clasificación de datasets.

## Estructura de Ejecución
- raw_unpacked: Archivos extraídos de ZIPs o copias crudas descubiertas.
- interim: Archivos intermedios tras la normalización de columnas (snake_case).
- cleaned: Datasets listos para ML, tras corrección de nulls y trimming.
- reports: JSONs de perfilado y summary Markdown de viabilidad.

## Uso
Ejecutar desde el directorio normalization:
```
python run_pipeline.py
```

## Logs y Configuración
Los logs se almacenan en `logs/pipeline.log`. El inventario en `config/file_registry.json`.
