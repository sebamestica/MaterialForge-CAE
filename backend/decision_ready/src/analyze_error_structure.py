import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import max_error, mean_absolute_error, r2_score
from src.utils import write_md, write_csv_rows

def analyze_error_structure(validation_result, review_cfg, logger):
    logger.info("FASE 5: Analisis de la estructura del error")
    
    # Extraemos info necesaria
    model = validation_result["model"]
    X_test = validation_result["X_test"]
    y_test = validation_result["y_test"]
    
    # Predecir
    preds = model.predict(X_test)
    df_eval = X_test.copy()
    df_eval['real'] = y_test
    df_eval['pred'] = preds
    df_eval['residual'] = y_test - preds
    df_eval['abs_error'] = np.abs(df_eval['residual'])
    df_eval['error_relativo'] = df_eval['abs_error'] / (np.abs(y_test) + 1e-9)
    
    # Recuperamos structure_type
    master_path = Path(review_cfg["master_source"])
    if master_path.exists():
        df_master = pd.read_csv(master_path)
        df_eval['structure_type'] = df_master.loc[X_test.index]['structure_type'].values
    else:
        df_eval['structure_type'] = 'unknown'

    # Error por grupo
    error_summary = []
    groups = df_eval.groupby('structure_type')
    
    Path("figures/residuals").mkdir(parents=True, exist_ok=True)
    
    for name, group in groups:
        mae = mean_absolute_error(group['real'], group['pred'])
        mare = group['error_relativo'].mean() * 100
        max_err = max_error(group['real'], group['pred'])
        error_summary.append([name, len(group), f"{mae:.4f}", f"{mare:.2f}%", f"{max_err:.4f}"])
        
        # Histograme de residuos por grupo
        plt.figure(figsize=(8, 6))
        sns.histplot(group['residual'], kde=True, color='salmon')
        plt.title(f"Residuos: {name}\nMAE: {mae:.3f}")
        plt.axvline(0, color='black', linestyle='--')
        plt.savefig(f"figures/residuals/residuals_{name}.png")
        plt.close()
        
    write_csv_rows("tables/error_by_group.csv", error_summary, ["Structure_Type", "Count", "MAE", "MARE (%)", "Max_Error"])
    
    # Grafico global real vs predicho
    plt.figure(figsize=(8, 8))
    sns.scatterplot(data=df_eval, x='real', y='pred', hue='structure_type')
    lims = [min(min(df_eval['real']), min(df_eval['pred'])) - 1, max(max(df_eval['real']), max(df_eval['pred'])) + 1]
    plt.plot(lims, lims, '--k', alpha=0.5)
    plt.title(f"Inferencia Global (Test Set)\nMAE Total: {mean_absolute_error(y_test, preds):.3f}")
    plt.savefig("figures/residuals/global_real_vs_pred.png")
    plt.close()

    return error_summary
