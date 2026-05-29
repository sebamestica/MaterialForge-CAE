import pandas as pd
from src.utils import read_json, save_json
from pathlib import Path

def to_snake_case(s):
    t = str(s).lower().strip().replace(' ', '_').replace('-', '_').replace('__', '_')
    for c in 'áéíóúÁÉÍÓÚñÑ':
        t = t.replace(c, 'aeiouAEIOUnN'['áéíóúÁÉÍÓÚñÑ'.index(c)])
    return t

def standardize_columns(registry_path, input_dir, output_dir, dict_path, logger):
    registry = read_json(registry_path)
    logger.info("Estandarizando columnas a snake_case...")
    col_mapping = {}
    
    for key, data in registry.items():
        if data.get('is_tabular') and not data.get('is_duplicate_candidate'):
            filepath = data['path']
            filename = data['name']
            
            if not Path(filepath).exists():
                continue
                
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath, low_memory=False)
                else:
                    df = pd.read_excel(filepath)
                
                original_cols = df.columns.tolist()
                new_cols = [to_snake_case(c) for c in original_cols]
                
                mapping = dict(zip(original_cols, new_cols))
                col_mapping[filename] = mapping
                
                df.rename(columns=mapping, inplace=True)
                
                out_path = Path(output_dir) / f"{Path(filename).stem}_std.csv"
                df.to_csv(out_path, index=False)
                
                registry[key]['interim_path'] = str(out_path)
                
            except Exception as e:
                logger.error(f"Error estandarizando {filename}: {str(e)}")
                
    save_json(col_mapping, dict_path)
    save_json(registry, registry_path)
    logger.info("Columnas estandarizadas.")
