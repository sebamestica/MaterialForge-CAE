import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import read_json, save_json

def clean_dataset_values(registry_path, output_dir, logger):
    registry = read_json(registry_path)
    logger.info("Limpiando valores en los datasets no duplicados...")
    
    for key, data in registry.items():
        if data.get('is_tabular') and not data.get('is_duplicate_candidate'):
            interim_path = data.get('interim_path')
            
            if not interim_path or not Path(interim_path).exists():
                continue
                
            filename = data['name']
            logger.info(f"Limpiando {filename}")
            
            try:
                df = pd.read_csv(interim_path)
                
                df.replace(['-', 'NA', 'None', '', ' '], np.nan, inplace=True)
                
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].astype(str).str.strip()
                        
                        try:
                            df[col] = pd.to_numeric(df[col])
                        except ValueError:
                            pass
                            
                out_path = Path(output_dir) / f"{Path(filename).stem}_cleaned.csv"
                df.to_csv(out_path, index=False)
                
                registry[key]['cleaned_path'] = str(out_path)
                registry[key]['status'] = 'cleaned'
                
            except Exception as e:
                logger.error(f"Error limpiando {filename}: {str(e)}")
                
    save_json(registry, registry_path)
    logger.info("Limpieza de valores completada.")
