from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from src.encode_features import build_preprocessor, get_feature_types

def get_base_algorithm(name, rs):
    algo_map = {
        "DummyRegressor": DummyRegressor(strategy="mean"),
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(random_state=rs),
        "Lasso": Lasso(random_state=rs),
        "ElasticNet": ElasticNet(random_state=rs),
        "RandomForestRegressor": RandomForestRegressor(random_state=rs),
        "GradientBoostingRegressor": GradientBoostingRegressor(random_state=rs)
    }
    return algo_map.get(name)

def build_fitted_models(X_train, y_train, config, logger):
    logger.info("Entrenando modelos y realizando sintonizacion basica...")
    rs = config.get("random_state", 42)
    models_to_train = config.get("models", [])
    tuning_grids = config.get("tuning", {})
    
    num_cols, cat_cols = get_feature_types(X_train)
    preprocessor = build_preprocessor(num_cols, cat_cols)
    
    trained_pipelines = {}
    
    # Simple CV folds based on dataset size
    cv_folds = min(5, len(y_train) // 2) if len(y_train) > 10 else 2
    
    for mod in models_to_train:
        base_clf = get_base_algorithm(mod, rs)
        if base_clf is None: continue
        
        main_pipe = Pipeline(steps=[('preprocessor', preprocessor), ('model', base_clf)])
        
        # Check if we have a tuning grid for this model
        if mod in tuning_grids:
            params = tuning_grids[mod]
            try:
                # n_jobs=1 to avoid issues in some environments (like the user context)
                search = GridSearchCV(main_pipe, params, cv=cv_folds, scoring='r2', n_jobs=1)
                search.fit(X_train, y_train)
                trained_pipelines[mod] = search.best_estimator_
                logger.info(f"Sintonizado {mod}: Mejor R2 CV={search.best_score_:.3f}")
            except Exception as e:
                logger.warning(f"Error sintonizando {mod}: {e}. Entrenando default.")
                main_pipe.fit(X_train, y_train)
                trained_pipelines[mod] = main_pipe
        else:
            try:
                main_pipe.fit(X_train, y_train)
                trained_pipelines[mod] = main_pipe
                logger.info(f"Entrenado {mod} con default.")
            except Exception as e:
                logger.warning(f"Error entrenando modelo {mod}: {e}")
                
    return trained_pipelines
