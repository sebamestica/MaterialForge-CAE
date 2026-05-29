import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from src.utils import write_md

def split_and_segment(df, config, logger):
    logger.info("Estratificando master dataset en Train/Val/Test...")
    
    test_size = config.get("test_size", 0.2)
    val_size = config.get("validation_size", 0.1)
    rs = config.get("random_state", 42)
    
    group_col = config.get("group_column")
    fallback = config.get("fallback_group_column")
    
    active_group = None
    if group_col in df.columns: active_group = group_col
    elif fallback in df.columns: active_group = fallback
    
    target = "compressive_strength" 
    X = df.drop(columns=[target], errors='ignore')
    y = df[target] if target in df.columns else df.iloc[:, -1]
    
    report_md = "# Reporte de Data Splitting\n\n"
    
    if active_group and df[active_group].nunique() > 2:
        logger.info(f"GroupShuffleSplit activado usando: {active_group}")
        groups = df[active_group]
        gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=rs)
        train_idx, test_idx = next(gss.split(X, y, groups))
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
        
        report_md += f"Se utilizo Group Shuffle Splitting respetando la columna `{active_group}` para evitar fuga interna de muestras similares o lotes identicos.\n"
    else:
        logger.info("Split Aleatorio activado")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=rs)
        report_md += "Se utilizo Test/Train Random Splitting puro.\n"
        
    val_rel = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=val_rel, random_state=rs)
    
    Path("data/train").mkdir(parents=True, exist_ok=True)
    Path("data/validation").mkdir(parents=True, exist_ok=True)
    Path("data/test").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    df.to_csv("data/processed/master_processed.csv", index=False)
    pd.concat([X_train, y_train], axis=1).to_csv(f"data/train/train.csv", index=False)
    pd.concat([X_val, y_val], axis=1).to_csv(f"data/validation/validation.csv", index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(f"data/test/test.csv", index=False)
    
    report_md += f"\n- **Train Size**: {X_train.shape[0]}\n- **Validation Size**: {X_val.shape[0]}\n- **Test Size**: {X_test.shape[0]}\n\n"
    write_md("reports/split_report.md", report_md)
    
    return X_train, X_val, X_test, y_train, y_val, y_test
