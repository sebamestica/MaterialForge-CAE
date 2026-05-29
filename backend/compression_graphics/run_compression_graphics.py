import sys
import os
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(_SCRIPT_DIR)
sys.path.insert(0, str(_SCRIPT_DIR))

import matplotlib
matplotlib.use("Agg")

from src.utils import setup_logger, write_json
from src.discover_sources import discover_sources
from src.validate_compression_sources import validate_compression_sources
from src.load_final_dataset import load_final_dataset, inspect_columns
from src.generate_quality_plots import generate_quality_plots
from src.generate_target_plots import generate_target_plots
from src.generate_relationship_plots import generate_relationship_plots
from src.generate_group_comparisons import generate_group_comparisons
from src.generate_linkage_plots import generate_linkage_plots
from src.generate_summary_plots import generate_summary_plots
from src.export_catalog import export_catalog

LOGS_DIR      = "logs"
OUTPUTS_DIR   = "outputs"
REPORTS_DIR   = "reports"
TABLES_DIR    = "tables"

OUTPUT_SUBDIRS = [
    "distributions", "quality", "targets", "relationships",
    "comparisons", "linkage", "summaries", "catalogs",
]


def run_compression_graphics():
    for d in [LOGS_DIR, REPORTS_DIR, TABLES_DIR] + \
             [f"{OUTPUTS_DIR}/{s}" for s in OUTPUT_SUBDIRS]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger = setup_logger(f"{LOGS_DIR}/compression_graphics.log")
    logger.info("=" * 60)
    logger.info("  COMPRESSION GRAPHICS — PLA_3dPrinter_RESISTENCE")
    logger.info("=" * 60)

    catalog  = []
    failed   = []
    all_gen  = []

    logger.info("\n[1/8] Descubriendo fuentes...")
    discovered, forbidden = discover_sources(logger, TABLES_DIR)

    logger.info("\n[2/8] Validando fuentes de compresión...")
    validation, chosen_id = validate_compression_sources(discovered, logger, REPORTS_DIR, TABLES_DIR)

    if not chosen_id:
        logger.error("  FATAL: No valid compressive dataset found. Cannot generate graphics.")
        return

    logger.info(f"  Chosen source: {chosen_id}")

    logger.info("\n[3/8] Cargando dataset e inspeccionando columnas...")
    df = load_final_dataset(validation, chosen_id, logger)
    profile = inspect_columns(df, logger, TABLES_DIR)

    logger.info("\n[4/8] Gráficos de calidad del dataset...")
    try:
        gen = generate_quality_plots(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [quality] Error: {e}")
        failed.append({"name": "quality_block", "reason": str(e)})

    logger.info("\n[5/8] Gráficos del target...")
    try:
        gen = generate_target_plots(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [targets] Error: {e}")
        failed.append({"name": "targets_block", "reason": str(e)})

    logger.info("\n[6/8] Gráficos de relaciones feature-target...")
    try:
        gen = generate_relationship_plots(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [relationships] Error: {e}")
        failed.append({"name": "relationships_block", "reason": str(e)})

    logger.info("\n[7/8] Gráficos de comparaciones por grupo...")
    try:
        gen = generate_group_comparisons(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [comparisons] Error: {e}")
        failed.append({"name": "comparisons_block", "reason": str(e)})

    logger.info("\n[7b/8] Gráficos de linkage y trazabilidad...")
    try:
        gen = generate_linkage_plots(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [linkage] Error: {e}")
        failed.append({"name": "linkage_block", "reason": str(e)})

    logger.info("\n[7c/8] Gráficos resumen ejecutivos...")
    try:
        gen = generate_summary_plots(df, profile, OUTPUTS_DIR, catalog, logger)
        all_gen.extend(gen)
    except Exception as e:
        logger.error(f"  [summaries] Error: {e}")
        failed.append({"name": "summaries_block", "reason": str(e)})

    logger.info("\n[8/8] Exportando catálogo y reportes...")
    export_catalog(catalog, profile, all_gen, failed, OUTPUTS_DIR, REPORTS_DIR, logger)

    logger.info("\n" + "=" * 60)
    logger.info("  COMPRESSION GRAPHICS COMPLETADO")
    logger.info(f"  Dataset usado: {chosen_id}")
    logger.info(f"  Figuras generadas: {len(all_gen)}")
    logger.info(f"  Bloques con error: {len(failed)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_compression_graphics()
