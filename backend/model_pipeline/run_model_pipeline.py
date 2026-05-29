import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.append(str(Path(__file__).parent))

from src.utils import setup_logger, load_json
from src.discover_source import find_master_source
from src.validate_source import validate_master_dataset
from src.build_dataset import aggregate_master
from src.engineer_features import engineer_features
from src.split_data import split_and_segment
from src.train_models import build_fitted_models
from src.evaluate_models import evaluate_models
from src.analyze_errors import analyze_best_errors
from src.select_best_model import select_winner
from src.export_outputs import export_framework

def run_pipeline():
    logger = setup_logger("logs/pipeline.log")
    logger.info("INICIANDO RECONSTRUCCION PIPELINE DE COMPRESION")
    
    try:
        f_config = load_json("config/feature_config.json")
        s_config = load_json("config/split_config.json")
        m_config = load_json("config/model_config.json")
        
        # 1. Discover and Validate Master Source (Exclusive high-confidence compression)
        master_path = find_master_source(logger)
        validate_master_dataset(master_path, logger)
        
        # 2. Dataset Construction and Engineering
        df_raw = aggregate_master(master_path, None, logger)
        df_feats = engineer_features(df_raw, f_config, logger)
        
        # 3. Data Splitting (Proved high quality via specimen_id grouping)
        X_train, X_val, X_test, y_train, y_val, y_test = split_and_segment(df_feats, s_config, logger)
        
        # 4. Model Training and Selection
        trained = build_fitted_models(X_train, y_train, m_config, logger)
        df_eval = evaluate_models(trained, X_test, y_test, logger)
        
        if df_eval.empty:
            raise ValueError("Evaluacion fracasada; ninguna inferencia pudo realizarse.")
            
        best = select_winner(df_eval, X_train, logger)
        
        # 5. Advanced Analysis and Export
        analyze_best_errors(trained[best], best, X_test, y_test, logger)
        export_framework(best, trained, df_eval, X_test, y_test, logger)
        
        logger.info("RECONSTRUCCION DE PIPELINE COMPLETADA EXITOSAMENTE")
        
    except Exception as e:
        logger.error(f"Falla crítica en reconstrucción de pipeline: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
