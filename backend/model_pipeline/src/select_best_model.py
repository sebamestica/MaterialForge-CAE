from src.utils import write_md
import pandas as pd

def select_winner(df_eval, X_train, logger):
    logger.info("Tomando decision sobre modelo productivo para serializacion...")
    
    if df_eval.empty:
        raise ValueError("No hay algoritmos en la tabla de testing.")
        
    first = df_eval.iloc[0]
    best_name = first["Modelo"]
    best_r2 = first["R2"]
    
    rep = "# Conclusion de Modelado Predictivo\n\n"
    rep += f"## Ganador Oficial: **{best_name}**\n\n- **R2 Final**: {best_r2:.3f}\n\n"
    
    size = X_train.shape[0]
    
    estado = "validated_current_model"
    if size < 80:
        estado = "best_current_option"
        rep += "### ADVERTENCIA SEVERA DE SUBREPRESENTACION\n"
        rep += "A pesar del rigor experimental de aislar `compressive_strength`, el modulo oficial dictamina que el dataset correcto extraido carece de volumen masivo.\n"
        rep += "Este clasificador debe rotularse como un prototipo academico prometedor."
    elif best_r2 < 0.6:
        estado = "promising_benchmark"
        rep += "### ADVERTENCIA DE SIGNAL BAJO\nEl algoritmo no ha capturado correctamente todos los factores determinantes para deducir el target con presicion superior algodonada."
    else:
        rep += "El modelo exhibe viabilidad para ser promovido a API o microservicio oficial en el framework de experimentación."
        
    rep += f"\n\n**ESTATUS FINAL DEL ARBOL**: `{estado}`"
    
    write_md("reports/final_model_report.md", rep)
    return best_name
