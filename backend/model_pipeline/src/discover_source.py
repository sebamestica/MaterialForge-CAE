from pathlib import Path
from src.utils import load_json, write_md

def find_master_source(logger):
    logger.info("Buscando fuente maestra de compresion...")
    config = load_json("config/source_config.json")
    
    dirs = config.get("search_dirs", [])
    keywords = config.get("keywords", [])
    prohibited = config.get("prohibited", [])
    
    candidates = []
    
    for d in dirs:
        p = Path(d)
        if not p.exists():
            continue
        for f in p.glob("**/*.csv"):
            fname = f.name
            
            is_prohibited = any(proh.lower() in fname.lower() for proh in prohibited)
            if is_prohibited:
                continue
                
            has_keyword = any(kw.lower() in fname.lower() for kw in keywords)
            if has_keyword:
                candidates.append(f)
                
    report_md = "# Seleccion de Fuente Maestra\n\n"
    
    if not candidates:
        logger.error("No se encontro ninguna fuente maestra valida.")
        report_md += "CRITICO: No se encontraron candidatos validos para el master dataset.\n"
        write_md("reports/source_selection.md", report_md)
        raise FileNotFoundError("Master compression dataset not found.")
        
    master = candidates[0]
    for c in candidates:
        if "high_confidence" in c.name or "hc" in c.name:
            master = c
            break
            
    logger.info(f"Fuente maestra seleccionada: {master.name}")
    
    report_md += f"## Archivo Oficial Utilizado\n- **{master.name}**\n- Ruta: `{master.resolve()}`\n\n"
    report_md += "## Criterios de Exclusion Aplicados\n- Archivos con nombres tensiles ('Tension') fueron ignorados logicamente.\n- Archivos base como `data.csv` fueron descartados para prevenir leakage de senales mixtas.\n"
    
    write_md("reports/source_selection.md", report_md)
    return str(master)
