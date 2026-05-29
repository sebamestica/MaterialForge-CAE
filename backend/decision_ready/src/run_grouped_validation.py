import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error
from src.utils import write_md, write_csv_rows
import matplotlib.pyplot as plt

def run_grouped_validation(validation_result, val_cfg, review_cfg, logger):
    logger.info("FASE 3.1: Validacion agrupada por estructura")
    
    model = validation_result["model"]
    X_test = validation_result["X_test"]
    y_test = validation_result["y_test"]
    
    # Predecir
    preds = model.predict(X_test)
    df_results = X_test.copy()
    df_results['real'] = y_test
    df_results['pred'] = preds
    df_results['abs_error'] = np.abs(y_test - preds)
    
    # Intentar detectar la columna de estructura si no es exacta
    # Los recuperamos del dataset master usando el indice de X_test.
    master_path = Path(review_cfg["master_source"])
    if master_path.exists():
        df_master = pd.read_csv(master_path)
        df_test_orig = df_master.loc[X_test.index]
        df_results['structure_type'] = df_test_orig['structure_type'].values
    else:
        # Fallback si no hay master
        df_results['structure_type'] = 'unknown'

    grouped_stats = []
    groups = df_results.groupby('structure_type')
    
    for name, group in groups:
        if len(group) > 0:
            r2 = r2_score(group['real'], group['pred']) if len(group) > 1 else 0
            mae = mean_absolute_error(group['real'], group['pred'])
            grouped_stats.append([name, len(group), f"{r2:.4f}", f"{mae:.4f}"])
            
    write_csv_rows("tables/grouped_scores.csv", grouped_stats, ["Structure_Type", "Count", "R2", "MAE"])
    
    report = "# Validacion Agrupada por Estructura\n\n"
    report += "| Estructura | Muestras (Test) | R² | MAE |\n"
    report += "|------------|-----------------|-----|-----|\n"
    for row in grouped_stats:
        report += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n"
        
    write_md("reports/stability_validation.md", report) # Append or write? prompt says generate report
    
    # Grafico de barras de error por grupo
    Path("figures/grouped_validation").mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.bar([r[0] for r in grouped_stats], [float(r[3]) for r in grouped_stats], color='skyblue')
    plt.title("MAE por Tipo de Estructura")
    plt.ylabel("MAE (MPa)")
    plt.savefig("figures/grouped_validation/mae_by_structure.png")
    plt.close()

    return grouped_stats
