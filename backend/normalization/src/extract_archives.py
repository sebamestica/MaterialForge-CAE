import zipfile
from pathlib import Path
from src.utils import save_json, read_json

def extract_all_archives(registry_path, output_dir, logger):
    registry = read_json(registry_path)
    logger.info(f"Buscando archivos ZIP en el registro...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    new_files_added = False
    
    for key, data in list(registry.items()):
        if data.get('extension') == '.zip':
            zip_path = Path(data['path'])
            logger.info(f"Descomprimiendo: {zip_path.name}")
            dest_dir = output_path / zip_path.stem
            dest_dir.mkdir(exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
                    
                for p in dest_dir.rglob('*'):
                    if p.is_file() and p.suffix.lower() in ['.csv', '.xlsx']:
                        rel_path = f"raw_unpacked/{zip_path.stem}/{p.name}"
                        registry[rel_path] = {
                            "name": p.name,
                            "path": str(p.absolute()),
                            "extension": p.suffix.lower(),
                            "size_bytes": p.stat().st_size,
                            "is_duplicate_candidate": False,
                            "is_tabular": True,
                            "priority": "media",
                            "status": "unpacked",
                            "notes": "Extraido de ZIP"
                        }
                        new_files_added = True
            except Exception as e:
                logger.error(f"Error extrayendo {zip_path}: {str(e)}")
                
    if new_files_added:
        save_json(registry, registry_path)
        logger.info("Nuevos archivos extraídos añadidos")
