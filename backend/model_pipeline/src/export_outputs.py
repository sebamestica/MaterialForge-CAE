import joblib
import pandas as pd
from pathlib import Path
from src.utils import write_md, load_json
from datetime import datetime

def export_framework(best_name, pipelines, df_eval, X_test, y_test, logger):
    logger.info("Empacando modelo triunfador en sistema de archivos artifacts/...")
    
    base = Path("artifacts/")
    for d in ["trained_models", "scalers", "encoders", "feature_lists", "predictions", "metrics"]:
        (base / d).mkdir(parents=True, exist_ok=True)
        
    winner = pipelines[best_name]
    
    # 1. Modelo Final
    joblib.dump(winner, base / f"trained_models/{best_name}_deployment_ready.pkl")
    
    # 2. Transformadores (Extraccion del preprocessor de la pipeline)
    preproc = winner.named_steps["preprocessor"]
    joblib.dump(preproc, base / "scalers/final_preprocessor.pkl")
    
    # 3. Metricas
    df_eval.to_csv(base / "metrics/deployment_run_results.csv", index=False)
    
    # 4. Predicciones en Test
    preds = winner.predict(X_test)
    df_res = X_test.copy()
    df_res["target_real"] = y_test
    df_res["target_predicted"] = preds
    df_res.to_csv(base / "predictions/final_test_predictions.csv", index=False)
    
    # 5. Lista de Features
    with open(base / "feature_lists/model_features_list.txt", "w") as f:
        f.write("\n".join(preproc.get_feature_names_out()))
        
    # 6. Copia de configuraciones usadas
    for cfg in ["model_config.json", "feature_config.json", "target_config.json"]:
        p_cfg = Path("config") / cfg
        if p_cfg.exists():
            with open(base / f"feature_lists/{cfg}", "w") as f_out:
                import json
                json.dump(load_json(p_cfg), f_out, indent=4)
    
    logger.info(f"Modelo final listado y exportado exitosamente. FIN DE INFERENCIA {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
