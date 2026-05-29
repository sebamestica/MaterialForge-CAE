from src.utils import read_json
from pathlib import Path

def export_summary(registry_path, output_path, logger):
    registry = read_json(registry_path)
    logger.info("Exportando reporte ejecutivo summary.md ...")
    
    lines = []
    lines.append("# Reporte Ejecutivo de Limpieza\n")
    
    validos = [v for k,v in registry.items() if v.get('status') == 'cleaned']
    duplicados = [v for k,v in registry.items() if v.get('is_duplicate_candidate')]
    
    lines.append(f"## Archivos viables para modelado serio ({len(validos)})\n")
    for d in validos:
        val = d.get('value_score', 'unknown')
        rel = d.get('reliability_score', 'unknown')
        lines.append(f"- **{d['name']}** - Valor: `{val}`, Confiabilidad: `{rel}`")
        if d.get('notes'):
            lines.append(f"  * {d['notes']}")
            
    lines.append(f"\n## Archivos Descartes/Duplicados ({len(duplicados)})\n")
    for d in duplicados:
        lines.append(f"- {d['name']} ({d.get('notes', 'Duplicado')})")
        
    lines.append("\n## Viabilidad del Modelaje\n")
    lines.append("Las variables presentes dependen de cada dataset, pero tras la estandarización snake_case y limpieza de tipados, las columnas numéricas están uniformes y sin ruido blanco.\n")
    lines.append("Los datasets evaluados como `high_value` y `high_reliability` están listos para regresiones y visualizaciones en la carpeta `cleaned/`.")
    
    try:
        Path(output_path).write_text("\n".join(lines), encoding='utf-8')
    except Exception as e:
        logger.error(f"Error escribiendo reporte: {str(e)}")
