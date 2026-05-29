import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from xgboost import XGBRegressor

PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")
MODELS_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/models")

FEATURES_CAT = ["material", "material_family", "manufacturing_process", "test_type", "infill_pattern", "load_orientation", "topology"]
FEATURES_NUM = [
    "layer_height_mm", "wall_thickness_mm", "infill_density_percent", 
    "nozzle_temperature_C", "bed_temperature_C", "print_speed_mm_s",
    "fan_speed_percent", "nozzle_diameter_mm", "print_orientation_deg",
    "cell_size_mm", "strut_diameter_mm", "relative_density_percent",
    "porosity_percent", "hybrid_ratio", "post_curing_time_min",
    "post_curing_temperature_C"
]
ALL_FEATURES = FEATURES_CAT + FEATURES_NUM

TARGETS = [
    "max_stress_MPa",
    "young_modulus_MPa",
    "failure_strain",
    "energy_density_MJ_m3",
    "specific_energy_absorption_kJ_kg",
    "compressive_strength_MPa",
    "ultimate_tensile_strength_MPa",
    "plateau_stress_MPa",
    "crushing_force_efficiency"
]

class BootstrapEnsemble:
    """
    Ensemble of models trained on bootstrapped samples to estimate p10-p90 uncertainty.
    """
    def __init__(self, base_estimator_class, n_bootstrap=10, **kwargs):
        self.base_estimator_class = base_estimator_class
        self.n_bootstrap = n_bootstrap
        self.kwargs = kwargs
        self.estimators = []

    def fit(self, X, y):
        self.estimators = []
        n_samples = X.shape[0]
        for i in range(self.n_bootstrap):
            # Bootstrap sample
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_boot = X[indices] if isinstance(X, np.ndarray) else X.iloc[indices]
            y_boot = y[indices] if isinstance(y, np.ndarray) else y.iloc[indices]
            
            est = self.base_estimator_class(**self.kwargs)
            est.fit(X_boot, y_boot)
            self.estimators.append(est)

    def predict(self, X):
        preds = np.array([est.predict(X) for est in self.estimators])
        mean_pred = np.mean(preds, axis=0)
        p10 = np.percentile(preds, 10, axis=0)
        p90 = np.percentile(preds, 90, axis=0)
        return mean_pred, p10, p90

def train_and_evaluate():
    """Trains FDM & lattice property prediction models."""
    print("=== TRAINING MECHANICAL PREDICTION MODELS ===")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    training_table_path = PROCESSED_DIR / "training_table.parquet"
    if not training_table_path.exists():
        print(f"Training table not found at {training_table_path}. Run ingestion first.")
        return

    df = pd.read_parquet(training_table_path)
    if len(df) < 5:
        print("Not enough data to train models.")
        return

    # Clean NaNs in features by imputing mean/mode
    for col in FEATURES_NUM:
        mean_val = df[col].mean()
        if pd.isna(mean_val):
            mean_val = 0.0
        df[col] = df[col].fillna(mean_val)
    for col in FEATURES_CAT:
        mode_series = df[col].mode()
        mode_val = mode_series.iloc[0] if not mode_series.empty else "unknown"
        if pd.isna(mode_val):
            mode_val = "unknown"
        df[col] = df[col].fillna(mode_val)

    # Define Column Transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), FEATURES_NUM),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), FEATURES_CAT)
        ])

    # Construct group key: material + test_type + infill_pattern + density
    df["group_key"] = df["material"].astype(str) + "_" + \
                      df["test_type"].astype(str) + "_" + \
                      df["infill_pattern"].astype(str) + "_" + \
                      df["infill_density_percent"].astype(str)

    # Cross-validation setup
    n_splits = min(5, len(df["group_key"].unique()))
    if n_splits < 2:
        # Fallback to standard KFold if grouping lacks distinct options
        gkf = GroupKFold(n_splits=2)
        groups = np.arange(len(df))
    else:
        gkf = GroupKFold(n_splits=n_splits)
        # Map group keys to integer ids
        group_ids = df["group_key"].astype('category').cat.codes
        groups = group_ids.values

    metrics = {}
    models_registry = {}
    feature_importance = {}

    best_pipelines = {}

    for target in TARGETS:
        # Filter rows where target is valid
        target_df = df.dropna(subset=[target]).copy()
        if len(target_df) < 5:
            print(f"Skipping target '{target}' due to insufficient data ({len(target_df)} rows).")
            continue

        X = target_df[ALL_FEATURES]
        y = target_df[target]
        t_groups = groups[target_df.index]

        print(f"\nTraining models for target: {target} (Muestras: {len(target_df)})...")

        # Run K-Fold CV to evaluate models
        cv_scores = {"RF": [], "XGB": [], "Ridge": []}
        
        for train_idx, test_idx in gkf.split(X, y, groups=t_groups):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # 1. Ridge
            pipe_ridge = Pipeline([('prep', preprocessor), ('model', Ridge(alpha=1.0))])
            pipe_ridge.fit(X_train, y_train)
            cv_scores["Ridge"].append(r2_score(y_test, pipe_ridge.predict(X_test)))

            # 2. RF
            pipe_rf = Pipeline([('prep', preprocessor), ('model', RandomForestRegressor(n_estimators=100, random_state=42))])
            pipe_rf.fit(X_train, y_train)
            cv_scores["RF"].append(r2_score(y_test, pipe_rf.predict(X_test)))

            # 3. XGBoost
            pipe_xgb = Pipeline([('prep', preprocessor), ('model', XGBRegressor(n_estimators=100, random_state=42, n_jobs=1))])
            pipe_xgb.fit(X_train, y_train)
            cv_scores["XGB"].append(r2_score(y_test, pipe_xgb.predict(X_test)))

        # Average R2 scores
        avg_r2 = {k: float(np.mean(v)) for k, v in cv_scores.items()}
        print(f"Average CV R2 scores: {avg_r2}")

        # Choose best algorithm
        best_algo = max(avg_r2, key=avg_r2.get)
        print(f"Selected best algorithm: {best_algo}")

        # Train final Bootstrap Ensemble on the whole dataset using the best algorithm
        if best_algo == "XGB":
            base_model_cls = XGBRegressor
            model_kwargs = {"n_estimators": 100, "random_state": 42, "n_jobs": 1}
        elif best_algo == "RF":
            base_model_cls = RandomForestRegressor
            model_kwargs = {"n_estimators": 100, "random_state": 42}
        else:
            base_model_cls = Ridge
            model_kwargs = {"alpha": 1.0}

        # Apply preprocessing first, using a fresh preprocessor to avoid sharing/mutation issues
        target_preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), FEATURES_NUM),
                ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), FEATURES_CAT)
            ])
        X_trans = target_preprocessor.fit_transform(X)
        
        ensemble = BootstrapEnsemble(base_model_cls, n_bootstrap=10, **model_kwargs)
        ensemble.fit(X_trans, y)

        # Full pipeline wrapping preprocessor and ensemble
        full_pipe = {
            "preprocessor": target_preprocessor,
            "ensemble": ensemble,
            "feature_names": ALL_FEATURES,
            "target_name": target
        }
        best_pipelines[target] = full_pipe

        # Evaluate performance on training set for metrics.json
        y_pred, y_p10, y_p90 = ensemble.predict(X_trans)
        mae = float(mean_absolute_error(y, y_pred))
        rmse = float(root_mean_squared_error(y, y_pred))
        r2 = float(r2_score(y, y_pred))

        metrics[target] = {
            "best_algorithm": best_algo,
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "cv_r2": avg_r2[best_algo]
        }

        # Save feature importance (from RandomForestRegressor or XGBRegressor on fully fit data)
        try:
            temp_model = base_model_cls(**model_kwargs)
            temp_model.fit(X_trans, y)
            
            # Map features
            ohe = preprocessor.named_transformers_['cat']
            cat_features_ohe = ohe.get_feature_names_out(FEATURES_CAT).tolist()
            feature_names = FEATURES_NUM + cat_features_ohe
            
            importances = temp_model.feature_importances_ if hasattr(temp_model, 'feature_importances_') else np.abs(temp_model.coef_)
            importances = importances / np.sum(importances) # normalize
            
            feat_imp_dict = {feature_names[j]: float(importances[j]) for j in range(len(feature_names))}
            # Sort
            feat_imp_dict = dict(sorted(feat_imp_dict.items(), key=lambda item: item[1], reverse=True)[:15])
            feature_importance[target] = feat_imp_dict
        except Exception as e:
            print(f"Could not compute feature importances for {target}: {e}")

    # Save latest models bundle
    model_file_path = MODELS_DIR / "latest_model.pkl"
    joblib.dump(best_pipelines, model_file_path)
    print(f"Model pipelines successfully saved to {model_file_path}")

    # Save metrics
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)

    # Save feature importances
    with open(MODELS_DIR / "feature_importance.json", "w") as f:
        json.dump(feature_importance, f, indent=4)

    # Save registry metadata
    registry = {
        "model_version": "1.1.0",
        "last_trained_at": datetime.now().isoformat(),
        "total_training_samples": len(df),
        "targets_trained": list(metrics.keys()),
        "metrics": metrics
    }
    with open(MODELS_DIR / "model_registry.json", "w") as f:
        json.dump(registry, f, indent=4)

    print("=== MODEL TRAINING PIPELINE COMPLETED ===")

if __name__ == "__main__":
    train_and_evaluate()
