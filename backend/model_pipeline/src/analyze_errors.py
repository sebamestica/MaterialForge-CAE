from src.utils import write_md
import pandas as pd

def analyze_best_errors(winner_model, winner_name, X_test, y_test, logger):
    logger.info("Realizando analisis dimensional del error...")
    
    pds = winner_model.predict(X_test)
    err_abs = abs(y_test - pds)
    diffs = pds - y_test
    
    # Crear copy
    df_err = X_test.copy()
    df_err["Real_Target"] = y_test
    df_err["Predicted"] = pds
    df_err["Error_Bruto"] = diffs
    df_err["Error_Absoluto"] = err_abs
    
    df_err.to_csv("artifacts/predictions/test_errors.csv", index=False)
    
    mae = err_abs.mean()
    sobre = (diffs > 0).sum()
    subes = (diffs < 0).sum()
    max_err = err_abs.max()
    
    rep = f"# Análisis Profundo de Error - {winner_name}\n\n"
    rep += f"- **Maximo Error Cometido**: {max_err:.4f}\n"
    rep += f"- **Media del Error**: {mae:.4f}\n"
    rep += f"- **Subestimaciones**: {subes} casos frente a **sobrestimaciones**: {sobre} casos.\n\n"
    
    if "material" in df_err.columns:
        g = df_err.groupby("material")["Error_Absoluto"].mean().reset_index()
        rep += "### Errores Segmentados por Categoria de Material\n\n"
        rep += g.to_markdown(index=False)
        rep += "\n\n"
        
    rep += "\n*Se incluyen estos datos para juzgar si los modelos tienden a penalizar ciertos dominios plasticos en la inferencia real.*"
    
    write_md("reports/error_analysis.md", rep)
    
    return True
