import pandas as pd
from pathlib import Path
from src.utils import load_json, write_md

def aggregate_master(source_path, config, logger):
    logger.info(f"Cargando dataset maestro desde {source_path}")
    df = pd.read_csv(source_path)
    
    # Save input
    Path("data/model_input/").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/model_input/raw_master_input.csv", index=False)
    
    target_config = load_json("config/target_config.json")
    target = target_config.get("canonical_target")
    
    initial_rows = df.shape[0]
    df.dropna(subset=[target], inplace=True)
    dropped_target = initial_rows - df.shape[0]
    
    rows, cols = df.shape
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()
    
    missing = df.isnull().mean().mean() * 100
    
    report = "# Resumen de Dataset Maestro\n\n"
    report += f"- **Fuente Aislada**: `{Path(source_path).name}`\n"
    report += f"- **Filas Validas**: {rows} (Eliminadas {dropped_target} por estar sin target)\n"
    report += f"- **Columnas Totales**: {cols}\n"
    report += f"- **Features Numericas**: {len(num_cols)}\n"
    report += f"- **Features Categoricas**: {len(cat_cols)}\n"
    report += f"- **Porcentaje Global Nulos**: {missing:.2f}%\n\n"
    
    if rows < 100:
        report += "### LIMITACION SEVERA NOTIFICADA\n"
        report += f"Reconociendo oficialmente el dataset como MUY LIMITADO ({rows} filas). La entropia algoritmica sera baja. Etiqueta interna configurada a `best_current_option`.\n"
        
    write_md("reports/dataset_summary.md", report)
    return df
