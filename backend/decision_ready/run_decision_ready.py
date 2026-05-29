import os
import sys
from pathlib import Path

# Configurar rutas para que podamos importar src/
os.chdir(Path(__file__).parent)
sys.path.append(str(Path(__file__).parent))

from src.utils import setup_logger, load_json, ensure_dirs
from src.discover_current_outputs import discover_outputs
from src.validate_current_model import validate_current_model
from src.run_stability_checks import run_stability_checks
from src.run_grouped_validation import run_grouped_validation
from src.analyze_feature_signal import analyze_feature_signal
from src.analyze_error_structure import analyze_error_structure
from src.compare_with_references import compare_with_references
from src.build_decision_matrix import build_decision_matrix
from src.export_final_snapshot import export_final_snapshot

def run_decision_ready_pipeline():
    logger = setup_logger("logs/decision_ready.log")
    logger.info("INICIANDO FASE FINAL DE CONSOLIDACION Y MATRIZ DE DECISION")
    
    try:
        # Cargar configuraciones
        review_cfg = load_json("config/review_config.json")
        val_cfg = load_json("config/validation_config.json")
        rpt_cfg = load_json("config/report_config.json")
        
        # Preparar directorios
        ensure_dirs(".", ["reports", "tables", "figures", "figures/metrics", "figures/residuals", "figures/grouped_validation", "figures/feature_signal", "figures/decision", "artifacts", "artifacts/final_snapshot", "artifacts/exported_predictions", "artifacts/validation_outputs"])
        
        # 1. Inventario (Fase 1)
        inventory = discover_outputs(review_cfg, logger)
        
        # 2. Validacion rigurosa (Fase 2)
        val_results = validate_current_model(inventory, review_cfg, logger)
        
        # 3. Estabilidad (Fase 3)
        stability_results = run_stability_checks(val_results, val_cfg, logger)
        
        # 3.1 Validacion Agrupada
        grouped_results = run_grouped_validation(val_results, val_cfg, review_cfg, logger)
        
        # 4. Señal de Features (Fase 4)
        signal_results = analyze_feature_signal(val_results, review_cfg, logger)
        
        # 5. Estructura del Error (Fase 5)
        error_results = analyze_error_structure(val_results, review_cfg, logger)
        
        # 6. Referencias (Fase 6)
        reference_results = compare_with_references(logger)
        
        # 7. Matriz de Decision (Fase 7)
        decision_results = build_decision_matrix(val_results, stability_results, logger)
        
        # 8. Snapshot y Reportes Ejecutivo (Fase 8)
        snapshot = export_final_snapshot(val_results, logger)
        
        logger.info("CONSOLIDACION FINAL COMPLETADA EXITOSAMENTE. REVISAR DIRECTORIO reports/ PARA TOMA DE DECISIONES.")
        
    except Exception as e:
        logger.error(f"Error critico en la fase decision_ready: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    run_decision_ready_pipeline()
