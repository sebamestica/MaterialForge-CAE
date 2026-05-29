import pandas as pd
from src.utils import load_json

def validate_master_dataset(path, logger):
    logger.info("Validando integridad estructural de la fuente maestra...")
    target_config = load_json("config/target_config.json")
    target = target_config.get("canonical_target")
    
    df = pd.read_csv(path, nrows=100)
    
    if target not in df.columns:
        logger.error(f"Target '{target}' no se encuentra en {path}.")
        raise ValueError(f"Target {target} no existe en master dataset.")
        
    cols_lower = [c.lower() for c in df.columns]
    tensile_flags = ["tension_strenght", "tensile"]
    if any(any(flag in c for flag in tensile_flags) for c in cols_lower):
        logger.error(f"Se detectaron columnas de traccion en la fuente supuestamente compresiva: {path}")
        raise ValueError("Source file contains tensile features. Contamination detected.")
        
    logger.info("Validacion exitosa: dataset compresivo confirmado.")
    return True
