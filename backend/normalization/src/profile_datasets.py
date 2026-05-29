import pandas as pd
from pathlib import Path
from src.utils import read_json, save_json

def profile_datasets(registry_path, output_dir, logger):
    registry = read_json(registry_path)
    logger.info("Iniciando perfilado de datasets...")
    
    reports = {}
    
    for key, data in registry.items():
        if data.get('is_tabular'):
            filepath = data['path']
            filename = data['name']
            logger.info(f"Perfilando {filename}...")
            
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath, nrows=1000)
                else:
                    df = pd.read_excel(filepath, nrows=1000)
                    
                report = {
                    "file_path": filepath,
                    "rows": int(len(df)) if not df.empty else 0,
                    "columns_count": int(len(df.columns)),
                    "columns": list(df.columns),
                    "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
                    "null_percentages": {str(k): round(float(v), 2) for k, v in (df.isnull().sum() / len(df) * 100).items()} if not df.empty else {},
                    "unique_values_count": {str(k): int(v) for k, v in df.nunique().items()},
                    "is_suspicious": df.empty or len(df.columns) < 2
                }
                
                reports[filename] = report
                
                out_path = Path(output_dir) / f"{Path(filename).stem}_profile.json"
                save_json(report, out_path)
                
            except Exception as e:
                logger.error(f"Error perfilando {filename}: {str(e)}")
                registry[key]['status'] = 'error_profiling'
                registry[key]['notes'] = str(e)
                
    save_json(registry, registry_path)
    logger.info("Perfilado completado.")
    return reports
