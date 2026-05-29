import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import cross_val_score, RepeatedKFold, LeaveOneOut
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from src.utils import load_json, write_md, write_csv_rows
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def run_stability_checks(validation_result, val_cfg, logger):
    logger.info("FASE 3: Validacion de estabilidad del modelo")

    model = validation_result["model"]
    X_train = validation_result["X_train"]
    y_train = validation_result["y_train"]
    X_test = validation_result["X_test"]
    y_test = validation_result["y_test"]
    n_total = validation_result["n_total"]
    rs = val_cfg.get("random_state", 42)

    all_X = pd.concat([X_train, X_test], ignore_index=True)
    all_y = pd.concat([y_train, y_test], ignore_index=True)

    results = {}

    for k in val_cfg.get("cv_folds_options", [3, 5]):
        if k > len(all_y) // 2:
            continue
        n_repeats = val_cfg.get("cv_repeats", 10)
        rkf = RepeatedKFold(n_splits=k, n_repeats=n_repeats, random_state=rs)

        r2_scores = cross_val_score(model, all_X, all_y, cv=rkf, scoring="r2")
        mae_scores = -cross_val_score(model, all_X, all_y, cv=rkf, scoring="neg_mean_absolute_error")
        rmse_scores = np.sqrt(-cross_val_score(model, all_X, all_y, cv=rkf, scoring="neg_mean_squared_error"))

        results[f"RepeatedKFold_k{k}"] = {
            "r2_mean": float(np.mean(r2_scores)),
            "r2_std": float(np.std(r2_scores)),
            "r2_min": float(np.min(r2_scores)),
            "r2_max": float(np.max(r2_scores)),
            "mae_mean": float(np.mean(mae_scores)),
            "mae_std": float(np.std(mae_scores)),
            "rmse_mean": float(np.mean(rmse_scores)),
            "rmse_std": float(np.std(rmse_scores)),
            "n_splits": k,
            "n_repeats": n_repeats,
            "r2_all": r2_scores.tolist(),
        }
        logger.info(f"  CV k={k} x{n_repeats}: R2={np.mean(r2_scores):.3f}+/-{np.std(r2_scores):.3f}")

    if len(all_y) <= 40:
        logger.info("  Ejecutando Leave-One-Out por dataset pequeno...")
        loo = LeaveOneOut()
        loo_preds = []
        loo_reals = []
        for train_idx, test_idx in loo.split(all_X):
            X_tr = all_X.iloc[train_idx]
            y_tr = all_y.iloc[train_idx]
            X_te = all_X.iloc[test_idx]
            y_te = all_y.iloc[test_idx]
            try:
                from sklearn.base import clone
                m_clone = clone(model)
                m_clone.fit(X_tr, y_tr)
                p = m_clone.predict(X_te)
                loo_preds.append(p[0])
                loo_reals.append(y_te.values[0])
            except Exception as e:
                logger.warning(f"LOO fold failed: {e}")

        if loo_preds:
            loo_r2 = r2_score(loo_reals, loo_preds)
            loo_mae = mean_absolute_error(loo_reals, loo_preds)
            loo_rmse = np.sqrt(mean_squared_error(loo_reals, loo_preds))
            results["LOO"] = {
                "r2": float(loo_r2),
                "mae": float(loo_mae),
                "rmse": float(loo_rmse),
                "n_folds": len(loo_preds),
            }
            logger.info(f"  LOO: R2={loo_r2:.3f}, MAE={loo_mae:.3f}")

    test_r2 = validation_result["r2_test"]
    report = "# Validacion de Estabilidad del Modelo\n\n"
    report += f"**Modelo**: {validation_result['winner']}\n"
    report += f"**Dataset total**: {n_total} muestras\n"
    report += f"**R² reportado en test set original**: {test_r2:.4f}\n\n"

    report += "## Resultados de Validacion Cruzada\n\n"
    report += "| Metodo | R² medio | R² std | R² min | R² max | MAE medio | RMSE medio |\n"
    report += "|--------|----------|--------|--------|--------|-----------|------------|\n"

    cv_rows = []
    for method, res in results.items():
        if method == "LOO":
            report += f"| LOO | {res['r2']:.4f} | - | - | - | {res['mae']:.4f} | {res['rmse']:.4f} |\n"
            cv_rows.append([method, f"{res['r2']:.4f}", "-", "-", "-", f"{res['mae']:.4f}", f"{res['rmse']:.4f}"])
        else:
            report += f"| {method} | {res['r2_mean']:.4f} | {res['r2_std']:.4f} | {res['r2_min']:.4f} | {res['r2_max']:.4f} | {res['mae_mean']:.4f} | {res['rmse_mean']:.4f} |\n"
            cv_rows.append([method, f"{res['r2_mean']:.4f}", f"{res['r2_std']:.4f}", f"{res['r2_min']:.4f}", f"{res['r2_max']:.4f}", f"{res['mae_mean']:.4f}", f"{res['rmse_mean']:.4f}"])

    report += f"\n| Test original | {test_r2:.4f} | - | - | - | {validation_result['mae_test']:.4f} | {validation_result['rmse_test']:.4f} |\n"

    report += "\n## Interpretacion\n\n"

    cv_r2_values = []
    for method, res in results.items():
        if method == "LOO":
            cv_r2_values.append(res["r2"])
        else:
            cv_r2_values.append(res["r2_mean"])

    if cv_r2_values:
        avg_cv_r2 = np.mean(cv_r2_values)
        gap_vs_test = test_r2 - avg_cv_r2

        report += f"- **R² promedio en CV**: {avg_cv_r2:.4f}\n"
        report += f"- **R² en test original**: {test_r2:.4f}\n"
        report += f"- **Diferencia**: {gap_vs_test:.4f}\n\n"

        if gap_vs_test > 0.15:
            report += "> **ALERTA**: El R² del test original es significativamente mayor que el R² medio de CV. "
            report += "Esto sugiere que la particion original de test fue **favorablemente sesgada** o que el modelo "
            report += "tiene **alta varianza entre particiones**. El desempeno real esperado es mas cercano al R² de CV.\n\n"
            stability_verdict = "inestable"
        elif gap_vs_test > 0.05:
            report += "> El test original muestra desempeno ligeramente superior al CV promedio. "
            report += "Esperable con datasets pequenos pero indica variabilidad moderada.\n\n"
            stability_verdict = "moderadamente_estable"
        elif gap_vs_test < -0.05:
            report += "> El CV promedio supera al test original. El modelo es razonablemente estable "
            report += "y la particion de test original puede haber sido ligeramente desfavorable.\n\n"
            stability_verdict = "estable"
        else:
            report += "> Consistencia buena entre test original y CV. Modelo razonablemente estable.\n\n"
            stability_verdict = "estable"

        high_variance = False
        for method, res in results.items():
            if method != "LOO" and res.get("r2_std", 0) > 0.2:
                high_variance = True
                report += f"> **ADVERTENCIA**: Alta dispersion en {method} (std={res['r2_std']:.3f}). "
                report += "Con datasets de ~35 muestras, la particion domina el resultado.\n\n"

        if high_variance:
            stability_verdict = "inestable"
    else:
        avg_cv_r2 = test_r2
        stability_verdict = "no_evaluable"

    report += "## Dependencia de Particion\n\n"
    report += f"Con solo {n_total} muestras, el modelo es **altamente sensible** a que muestras caen en train vs test. "
    report += "Esto es una limitacion fundamental del tamano muestral, no del algoritmo.\n\n"
    report += f"**Veredicto de estabilidad**: `{stability_verdict}`\n"

    write_md("reports/stability_validation.md", report)

    Path("figures/grouped_validation").mkdir(parents=True, exist_ok=True)
    for method, res in results.items():
        if method == "LOO" or "r2_all" not in res:
            continue
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(res["r2_all"], bins=15, color="#2196F3", edgecolor="white", alpha=0.8)
        ax.axvline(test_r2, color="#F44336", linestyle="--", linewidth=2, label=f"Test original R²={test_r2:.3f}")
        ax.axvline(res["r2_mean"], color="#4CAF50", linestyle="-", linewidth=2, label=f"CV mean R²={res['r2_mean']:.3f}")
        ax.set_xlabel("R²")
        ax.set_ylabel("Frecuencia")
        ax.set_title(f"Distribucion de R² - {method}")
        ax.legend()
        plt.tight_layout()
        fig.savefig(f"figures/grouped_validation/cv_r2_distribution_{method}.png", dpi=150)
        plt.close(fig)

    if "LOO" in results:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(results["LOO"].get("reals", loo_reals), results["LOO"].get("preds", loo_preds),
                   color="#2196F3", edgecolor="white", s=60, zorder=3)
        lims = [min(min(loo_reals), min(loo_preds)) - 1, max(max(loo_reals), max(loo_preds)) + 1]
        ax.plot(lims, lims, "--", color="#999", linewidth=1)
        ax.set_xlabel("Real")
        ax.set_ylabel("Predicho (LOO)")
        ax.set_title(f"LOO: Real vs Predicho (R²={results['LOO']['r2']:.3f})")
        plt.tight_layout()
        fig.savefig("figures/grouped_validation/loo_real_vs_predicted.png", dpi=150)
        plt.close(fig)

    logger.info(f"Estabilidad evaluada: veredicto={stability_verdict}")

    return {
        "cv_results": results,
        "stability_verdict": stability_verdict,
        "avg_cv_r2": float(avg_cv_r2),
        "gap_vs_test": float(test_r2 - avg_cv_r2) if cv_r2_values else 0,
    }
