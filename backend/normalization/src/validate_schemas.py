import pandas as pd
from pathlib import Path
from src.utils import read_json, save_json

def validate_and_classify(registry_path, logger):
    registry = read_json(registry_path)
    logger.info("Clasificando calidad de datasets limpios...")
    
    for key, data in registry.items():
        if data.get('status') == 'cleaned':
            cleaned_path = data.get('cleaned_path')
            if not cleaned_path or not Path(cleaned_path).exists():
                continue
                
            try:
                df = pd.read_csv(cleaned_path)
                
                val_score = "high_value"
                rel_score = "high_reliability"
                
                if df.empty or len(df.columns) < 3 or len(df) < 50:
                    val_score = "low_value"
                    rel_score = "low_reliability"
                    data['notes'] = "Dataset muy pepueño o columnas insuficientes"
                else:
                    null_pct = df.isnull().sum().sum() / (df.shape[0]*df.shape[1])
                    if null_pct > 0.4:
                        rel_score = "low_reliability"
                        data['notes'] = "Exceso de valores nulos"
                    elif null_pct > 0.1:
                        rel_score = "medium_reliability"
                
                for col in df.columns:
                    if 'error' in col.lower() or 'unnamed' in col.lower():
                        if val_score == "high_value":
                            val_score = "medium_value"
                            
                if df.duplicated().sum() > 0:
                    data['notes'] = "Filas duplicadas detectadas en el crudo"
                    rel_score = "low_reliability" if rel_score == "high_reliability" else rel_score
                
                data['value_score'] = val_score
                data['reliability_score'] = rel_score
                
            except Exception as e:
                logger.error(f"Error comprobando {data['name']}: {str(e)}")
                
    save_json(registry, registry_path)
    logger.info("Validación y clasificación completada.")
