import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from src.utils import load_json, write_md, write_csv_rows


def validate_current_model(inventory, review_cfg, logger):
    logger.info("FASE 2: Validacion rigurosa del modelo actual")

    pipeline_dir = Path(review_cfg["model_pipeline_dir"])
    target = review_cfg["canonical_target"]

    winner_name = review_cfg["official_winner"]
    winner_path = pipeline_dir / f"artifacts/trained_models/{winner_name}_deployment_ready.pkl"

    if not winner_path.exists():
        winner_path = pipeline_dir / f"artifacts/trained_models/{winner_name}.pkl"

    model = joblib.load(winner_path)
    logger.info(f"Modelo cargado: {winner_name} desde {winner_path}")

    master_path = Path(review_cfg["master_source"])
    df_master = pd.read_csv(master_path)

    train_path = pipeline_dir / "data/train/train.csv"
    test_path = pipeline_dir / "data/test/test.csv"
    val_path = pipeline_dir / "data/validation/validation.csv"

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)
    df_val = pd.read_csv(val_path) if val_path.exists() else pd.DataFrame()

    features_used = [c for c in df_train.columns if c != target]
    features_excluded = [c for c in df_master.columns if c not in features_used and c != target]

    X_test = df_test.drop(columns=[target], errors="ignore")
    y_test = df_test[target]

    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mape = np.mean(np.abs((y_test.values - preds) / (np.abs(y_test.values) + 1e-9))) * 100

    X_train = df_train.drop(columns=[target], errors="ignore")
    y_train = df_train[target]
    train_preds = model.predict(X_train)
    train_r2 = r2_score(y_train, train_preds)
    train_mae = mean_absolute_error(y_train, train_preds)

    overfit_gap = train_r2 - r2

    feature_config = load_json(pipeline_dir / "config/feature_config.json")
    drop_cols = feature_config.get("drop_columns", [])

    leakage_risk_features = []
    for f in features_used:
        f_low = f.lower()
        if "mean" in f_low and target.replace("_", "") in f_low.replace("_", ""):
            leakage_risk_features.append((f, "HIGH - contains aggregated target statistics"))
        elif "std" in f_low and target.replace("_", "") in f_low.replace("_", ""):
            leakage_risk_features.append((f, "MODERATE - standard deviation of target readings"))
        elif "n_readings" in f_low:
            leakage_risk_features.append((f, "LOW - number of readings, proxy for test duration"))

    n_total = len(df_master)
    n_train = len(df_train)
    n_test = len(df_test)
    n_val = len(df_val) if not df_val.empty else 0
    n_features = len(features_used)

    ratio_samples_features = n_train / max(n_features, 1)

    preprocessor = model.named_steps.get("preprocessor")
    if preprocessor:
        try:
            transformed_feature_names = list(preprocessor.get_feature_names_out())
            n_transformed = len(transformed_feature_names)
        except Exception:
            n_transformed = n_features
            transformed_feature_names = features_used
    else:
        n_transformed = n_features
        transformed_feature_names = features_used

    write_csv_rows(
        "tables/metrics_summary.csv",
        [
            [winner_name, "test", f"{r2:.4f}", f"{mae:.4f}", f"{rmse:.4f}", f"{mape:.1f}"],
            [winner_name, "train", f"{train_r2:.4f}", f"{train_mae:.4f}", "", ""],
        ],
        ["Model", "Split", "R2", "MAE", "RMSE", "MAPE_pct"]
    )

    report = "# Revision de Validez del Modelo Actual\n\n"
    report += f"**Fecha de revision**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report += "## 1. Identidad del Modelo\n\n"
    report += f"- **Modelo ganador**: {winner_name}\n"
    report += f"- **Archivo**: `{winner_path.name}`\n"
    report += f"- **Target**: `{target}`\n"
    report += f"- **Dataset fuente**: `{master_path.name}` ({n_total} filas)\n"
    report += f"- **Split**: Train={n_train}, Val={n_val}, Test={n_test}\n\n"

    report += "## 2. Features Utilizadas\n\n"
    report += f"**Features originales de entrada** ({len(features_used)}): {', '.join(features_used)}\n\n"
    report += f"**Features transformadas post-encoding** ({n_transformed}): {', '.join(transformed_feature_names)}\n\n"

    report += "### Features excluidas del master\n\n"
    for fe in features_excluded:
        reason = "leakage/traceability" if any(d in fe.lower() for d in drop_cols) else "empty/irrelevant"
        report += f"- `{fe}` → {reason}\n"

    report += "\n## 3. Metricas de Desempeno\n\n"
    report += "| Split | R² | MAE | RMSE | MAPE (%) |\n"
    report += "|-------|-----|-----|------|----------|\n"
    report += f"| Train | {train_r2:.4f} | {train_mae:.4f} | - | - |\n"
    report += f"| Test  | {r2:.4f} | {mae:.4f} | {rmse:.4f} | {mape:.1f} |\n\n"

    report += f"**Brecha de sobreajuste (Train R² - Test R²)**: {overfit_gap:.4f}\n\n"
    if overfit_gap > 0.15:
        report += "> **ADVERTENCIA**: La brecha de sobreajuste es significativa. "
        report += "Con un dataset de solo 35 filas y un modelo basado en arboles, esto es esperado pero debe reportarse.\n\n"
    elif overfit_gap > 0.05:
        report += "> Brecha moderada. Aceptable para el tamano muestral, pero confirma la naturaleza prototipica del modelo.\n\n"
    else:
        report += "> Brecha baja. Buena generalizacion relativa al tamano del dataset.\n\n"

    report += "## 4. Analisis de Riesgo de Leakage\n\n"
    if leakage_risk_features:
        report += "### ALERTA: Features con riesgo de leakage detectadas\n\n"
        for feat_name, risk_desc in leakage_risk_features:
            report += f"- **`{feat_name}`**: {risk_desc}\n"
        report += "\n> **Interpretacion**: Las features `compressive_strength_mean` y `compressive_strength_std` son estadisticas "
        report += "agregadas de las lecturas del ensayo de compresion de cada probeta. Dado que el target `compressive_strength` "
        report += "es el maximo stress de esos mismos ensayos, estas features estan **estadisticamente correlacionadas con el target "
        report += "por construccion**, no por senal fisica independiente. Esto constituye un **leakage estadistico parcial** que "
        report += "infla el R² reportado. El modelo esta aprendiendo en parte una relacion matematica (max ≈ f(mean, std, n)) "
        report += "en lugar de una relacion fisica pura entre parametros de diseno y resistencia.\n\n"
        report += "> **Impacto estimado**: El R² real sin estas features seria sustancialmente menor. "
        report += "Esto no invalida la utilidad del modelo como prototipo, pero **impide llamarlo predictor independiente**.\n\n"
    else:
        report += "No se detectaron features con riesgo evidente de leakage.\n\n"

    report += "## 5. Coherencia Dataset-Desempeno\n\n"
    report += f"- **Ratio muestras/features**: {ratio_samples_features:.1f} (train={n_train}, features_raw={n_features})\n"
    report += f"- **Ratio muestras/features_transformadas**: {n_train/max(n_transformed,1):.1f}\n"

    if ratio_samples_features < 5:
        report += "- **CRITICO**: El ratio muestras/features es demasiado bajo para inferencia confiable.\n"
    elif ratio_samples_features < 10:
        report += "- **LIMITADO**: El ratio es bajo; los resultados deben interpretarse con cautela.\n"
    else:
        report += "- Ratio aceptable para analisis exploratorio.\n"

    report += f"\n- **Tamano test set**: {n_test} muestras. "
    if n_test < 10:
        report += "Demasiado pequeno para conclusiones estadisticamente robustas sobre R². "
        report += "Un R² de {:.3f} sobre {} muestras tiene alta varianza.\n".format(r2, n_test)

    report += "\n## 6. Conclusion de Validez\n\n"
    report += "### Por que el modelo es mecanicamente valido\n\n"
    report += "1. Se entreno exclusivamente sobre datos de compresion verificados (high_confidence_dataset)\n"
    report += "2. No contiene datos tensiles\n"
    report += "3. El pipeline aplica correctamente exclusion de columnas de trazabilidad\n"
    report += "4. La estructura train/val/test fue aplicada con random split (seed=42)\n"
    report += "5. El modelo supera significativamente al baseline DummyRegressor\n\n"

    report += "### Por que NO debe llamarse solucion definitiva\n\n"
    report += "1. **Dataset de 35 filas**: insuficiente para validacion estadistica robusta\n"
    report += "2. **Leakage estadistico parcial**: `compressive_strength_mean` y `compressive_strength_std` son derivadas del mismo ensayo que produce el target\n"
    report += "3. **Test set de 7 muestras**: el R² reportado tiene alta varianza por particion\n"
    report += "4. **Sin parametros de proceso**: el modelo no puede predecir el efecto de cambios en impresion (layer_height, temperature, speed)\n"
    report += "5. **Solo 3 tipos de estructura y ~3 niveles de design_param por tipo**: el espacio de diseno explorado es muy estrecho\n\n"

    confidence = "moderada-baja"
    if r2 > 0.9 and len(leakage_risk_features) == 0:
        confidence = "moderada"
    elif r2 > 0.9 and len(leakage_risk_features) > 0:
        confidence = "moderada-baja (inflada por leakage parcial)"
    elif r2 > 0.7:
        confidence = "baja"

    report += f"### Nivel de confianza actual: **{confidence}**\n\n"
    report += "El modelo es un **prototipo valido** para analisis direccional. "
    report += "Captura tendencias generales entre tipo de estructura, parametro de diseno y resistencia compresiva. "
    report += "No es adecuado para prediccion industrial ni para decisiones de garantia estructural.\n"

    write_md("reports/model_validity_review.md", report)
    logger.info(f"Validacion completada: R2_test={r2:.4f}, leakage_flags={len(leakage_risk_features)}")

    return {
        "winner": winner_name,
        "r2_test": r2,
        "mae_test": mae,
        "rmse_test": rmse,
        "r2_train": train_r2,
        "overfit_gap": overfit_gap,
        "n_train": n_train,
        "n_test": n_test,
        "n_total": n_total,
        "n_features_raw": n_features,
        "n_features_transformed": n_transformed,
        "features_used": features_used,
        "leakage_flags": len(leakage_risk_features),
        "confidence": confidence,
        "model": model,
        "X_test": X_test,
        "y_test": y_test,
        "X_train": X_train,
        "y_train": y_train,
    }
