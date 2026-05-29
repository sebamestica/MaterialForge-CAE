import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from src.utils import write_md, write_csv_rows

def analyze_feature_signal(validation_result, review_cfg, logger):
    logger.info("FASE 4: Analisis de senal de features")
    
    # Usamos el master dataset para analisis de senal fisica
    master_path = Path(review_cfg["master_source"])
    if not master_path.exists():
        logger.error("Master source no disponible para analisis de senal")
        return None
        
    df = pd.read_csv(master_path)
    target = 'compressive_strength'
    
    # Analisis de correlacion de Pearson
    numeric_df = df.select_dtypes(include=[np.number])
    corrs = numeric_df.corr()[target].sort_values(ascending=False)
    
    feature_signal_summary = []
    
    # Generar graficos bivariados para top features
    Path("figures/feature_signal").mkdir(parents=True, exist_ok=True)
    
    for feat, corr_val in corrs.items():
        if feat == target: continue
        
        signal_strength = "Fuerte" if abs(corr_val) > 0.7 else "Media" if abs(corr_val) > 0.4 else "Debil"
        feature_signal_summary.append([feat, f"{corr_val:.4f}", signal_strength])
        
        # Grafico
        plt.figure(figsize=(8, 6))
        sns.scatterplot(data=df, x=feat, y=target, hue='structure_type', palette='viridis')
        plt.title(f"Senal: {feat} vs {target}\nPearson: {corr_val:.3f}")
        plt.savefig(f"figures/feature_signal/signal_{feat}.png")
        plt.close()
        
    write_csv_rows("tables/feature_signal_summary.csv", feature_signal_summary, ["Feature", "Correlation", "Strength"])
    
    report = "# Analisis de Senal Fisica de Features\n\n"
    report += "Este analisis evalua si las variables de entrada presentan una relacion monotonica o visible con la resistencia.\n\n"
    report += "| Feature | Correlacion (Pearson) | Fuerza de Senal |\n"
    report += "|---------|------------------------|------------------|\n"
    for row in feature_signal_summary:
        report += f"| {row[0]} | {row[1]} | {row[2]} |\n"
    
    report += "\n## Interpretacion Fisica\n"
    # Analisis conceptual simple
    if 'design_param_numeric' in corrs and corrs['design_param_numeric'] > 0.7:
        report += "- **design_param_numeric**: Presenta una correlacion muy alta con la resistencia. Es una feature determinante y fisicamente coherente (mayor relleno/espesor = mayor resistencia).\n"
    elif 'design_param_numeric' in corrs:
         report += f"- **design_param_numeric**: Presenta una correlacion de {corrs['design_param_numeric']:.3f}. Senal detectable pero no linealmente dominante por si sola.\n"
    
    if 'compressive_strength_mean' in corrs and corrs['compressive_strength_mean'] > 0.9:
        report += "- **compressive_strength_mean**: Feature critica con riesgo de leakage (estadistica agregada del mismo test). Su alta correlacion explica gran parte del R2 del modelo.\n"

    write_md("reports/physical_interpretation.md", report)
    
    return feature_signal_summary
