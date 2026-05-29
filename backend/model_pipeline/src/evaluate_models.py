import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.utils import write_md

def evaluate_models(trained_dict, X_test, y_test, logger):
    logger.info("Testeando metricas de todos los pipelines validos...")
    
    results = []
    for nm, pipe in trained_dict.items():
        try:
            pds = pipe.predict(X_test)
            mae = mean_absolute_error(y_test, pds)
            rmse = mean_squared_error(y_test, pds) ** 0.5
            r2 = r2_score(y_test, pds)
            
            err_relativo = (abs(y_test - pds) / (abs(y_test) + 1e-9)).mean() * 100
            
            results.append({
                "Modelo": nm, "MAE": mae, "RMSE": rmse, "R2": r2, "Error_Relativo_%": err_relativo
            })
        except Exception as e:
            logger.error(f"Error evaluando el test de {nm}: {str(e)}")
            
    df_eval = pd.DataFrame(results).sort_values(by="R2", ascending=False)
    
    rep = "# Comparacion Exhaustiva de Rendimientos (Test Data)\n\n"
    rep += df_eval.to_markdown(index=False)
    
    write_md("reports/model_comparison.md", rep)
    df_eval.to_csv("artifacts/metrics/validation_results.csv", index=False)
    return df_eval
