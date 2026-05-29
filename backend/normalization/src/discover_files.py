from pathlib import Path
from src.utils import save_json

def discover_all_files(base_dir, registry_path, logger):
    logger.info(f"Escaneando directorio base: {base_dir}")
    registry = {}
    valid_extensions = ['.csv', '.xlsx', '.zip', '.pdf', '.ipynb', '.py', '.txt']
    
    for p in Path(base_dir).rglob('*'):
        if 'normalization' in p.parts or not p.is_file():
            continue
            
        ext = p.suffix.lower()
        if ext in valid_extensions:
            rel_path = p.relative_to(base_dir).as_posix()
            is_tabular = ext in ['.csv', '.xlsx']
            
            registry[rel_path] = {
                "name": p.name,
                "path": str(p.absolute()),
                "extension": ext,
                "size_bytes": p.stat().st_size,
                "is_duplicate_candidate": False,
                "is_tabular": is_tabular,
                "priority": "alta" if is_tabular else "baja",
                "status": "raw",
                "notes": f"Tipo {ext}"
            }
    
    logger.info(f"Se encontraron {len(registry)} archivos relevantes.")
    save_json(registry, registry_path)
    return registry
