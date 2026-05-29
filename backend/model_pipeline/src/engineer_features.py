import pandas as pd
from src.utils import write_md, load_json

def engineer_features(df, config, logger):
    logger.info("Filtrando e inyectando features fisico-mecanicas...")
    
    drop_cols = config.get("drop_columns", [])
    target = load_json("config/target_config.json").get("canonical_target")
    
    report_lines = ["# Reporte de Feature Engineering\n"]
    
    initial_features = df.columns.tolist()
    report_lines.append(f"## Features de Entrada ({len(initial_features)})\n- {', '.join(initial_features)}")
    
    df_feat = df.copy()
    derived_vars = []
    
    # Derivaciones razonables
    if 'width' in initial_features and 'thickness' in initial_features and 'transverse_area' not in initial_features:
        df_feat['derived_area'] = df_feat['width'] * df_feat['thickness']
        derived_vars.append("`derived_area` (Area logica = width x thickness)")
        
    cols_to_drop = []
    for c in df_feat.columns:
        c_low = c.lower()
        if c == target: continue
        
        # Filtros de fuga por leak correlacionado (residuos mecanicos) post-ensayos
        is_leaky = any(skip in c_low for skip in drop_cols)
        if is_leaky:
            cols_to_drop.append(c)
        elif c_low == 'max_force':
            cols_to_drop.append(c)
            
    # Adicional: droppear columnas 100% nulas
    all_nulls = df_feat.columns[df_feat.isnull().all()].tolist()
    for n in all_nulls:
        if n not in cols_to_drop:
            cols_to_drop.append(n)

    df_cleaned = df_feat.drop(columns=cols_to_drop, errors='ignore')
    
    report_lines.append("\n## Features Derivadas")
    if derived_vars:
        for dv in derived_vars: report_lines.append(f"- {dv}")
    else:
        report_lines.append("- Ninguna")
        
    report_lines.append("\n## Features Excluidas")
    if cols_to_drop:
        for ex in cols_to_drop:
            if any(lk in ex.lower() for lk in drop_cols): reason = "Leakage"
            elif ex.lower() == 'max_force': reason = "Correlacion Directa"
            elif ex in all_nulls: reason = "Columna Vacia"
            else: reason = "Configuracion"
            report_lines.append(f"- `{ex}` -> Razon: {reason}")
    else:
        report_lines.append("- Ninguna")
        
    final_features = df_cleaned.columns.tolist()
    report_lines.append(f"\n## Features Finales ({len(final_features)})\n- {', '.join(final_features)}")
    
    write_md("reports/feature_report.md", "\n".join(report_lines))
    return df_cleaned
