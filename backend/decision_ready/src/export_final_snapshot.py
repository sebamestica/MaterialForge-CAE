import json
from pathlib import Path
from src.utils import write_md, load_json

def export_final_snapshot(validation_result, logger):
    logger.info("FASE 8: Snapshot final del proyecto")
    
    snapshot = {
        "status": "Final de la iteracion (Consolidacion)",
        "decision": "Prototipo Valido",
        "dataset_oficial": "high_confidence_dataset.csv",
        "n_samples": validation_result["n_total"],
        "modelo_ganador": validation_result["winner"],
        "precision_test_R2": f"{validation_result['r2_test']:.4f}",
        "precision_test_MAE": f"{validation_result['mae_test']:.4f}",
        "precision_train_R2": f"{validation_result['r2_train']:.4f}",
        "gap_sobreajuste": f"{validation_result['overfit_gap']:.4f}",
        "features_finales": validation_result["features_used"],
        "timestamp": pd.Timestamp.now().isoformat() if 'pd' in globals() else "2026-03-30T02:00:00"
    }
    
    # Intentar importar pandas si fallo antes
    import pandas as pd
    snapshot["timestamp"] = pd.Timestamp.now().isoformat()
    
    snapshot_path = Path("artifacts/final_snapshot/snapshot.json")
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=4)
        
    # Siguientes acciones
    actions = "# Recomendaciones de Siguientes Acciones\n\n"
    actions += "1. **Prioridad 1**: Vincular `specimen_id` con el `FDM_Dataset` para obtener parametros de fabricacion real.\n"
    actions += "2. **Ampliacion**: El modelo actual captura la geometria pero no el proceso. Se recomienda duplicar el dataset con mas variabilidad de temperatura.\n"
    actions += "3. **Modelo**: Con mas de 100 muestras, se puede evaluar redes neuronales o ensambles mas complejos.\n"
    actions += "4. **Optimización**: No tiene sentido optimizar hiperparametros por encima de lo actual hasta ganar en volumen muestral.\n"
    
    write_md("reports/next_actions.md", actions)
    
    # Executive Summary
    summary = "# Resumen Ejecutivo de Decision Tecnico\n\n"
    summary += "La fase actual de modelado de resistencia compresiva ha sido completada y validada con rigor ingenieril.\n\n"
    summary += f"**Conclusion**: El modelo (`{validation_result['winner']}`) ha sido validado mecanicamente pero identificado como de **baja estabilidad** por su tamano muestral ({validation_result['n_total']} filas).\n\n"
    summary += "### Datos Clave:\n"
    summary += f"- R2 Test: {validation_result['r2_test']:.3f}\n"
    summary += f"- R2 Medio de CV: {validation_result.get('avg_cv_r2', 0):.3f}\n"
    summary += "- Veredicto: **Prototipo Valido**. Es util para entender tendencias estructurales pero no para garantias de diseno.\n\n"
    summary += "### Decision Final:\n"
    summary += "Dar por **cerrada** esta fase de benchmark inicial de modelos y priorizar la **ingenieria de datos (dataset enrichment)** sobre el ajuste del algoritmo.\n"
    
    write_md("reports/executive_decision_summary.md", summary)
    
    return snapshot
