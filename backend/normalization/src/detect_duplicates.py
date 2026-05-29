import hashlib
from src.utils import read_json, save_json
from pathlib import Path

def hash_file(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except:
        return None

def detect_duplicates(registry_path, logger):
    registry = read_json(registry_path)
    logger.info("Detectando duplicados...")
    
    hashes = {}
    duplicates_count = 0
    
    for key, data in registry.items():
        if data.get('is_tabular'):
            filepath = data['path']
            if not Path(filepath).exists():
                continue
                
            f_hash = hash_file(filepath)
            
            if f_hash:
                if f_hash in hashes:
                    registry[key]['is_duplicate_candidate'] = True
                    registry[key]['notes'] = f"Posible duplicado de {hashes[f_hash]}"
                    registry[key]['priority'] = "baja"
                    duplicates_count += 1
                else:
                    hashes[f_hash] = filepath
                    
    save_json(registry, registry_path)
    logger.info(f"Se encontraron {duplicates_count} posibles duplicados.")
