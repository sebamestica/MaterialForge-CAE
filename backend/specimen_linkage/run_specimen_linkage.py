import sys
import os
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import setup_logger, write_json
from src.discover_linkage_sources import discover_linkage_sources
from src.inspect_compression_specimens import inspect_compression_specimens
from src.parse_specimen_ids import parse_specimen_ids
from src.infer_feature_links import infer_feature_links
from src.validate_links import validate_links
from src.build_final_model_dataset import build_final_model_dataset
from src.export_linkage_outputs import export_linkage_outputs

REPORTS_DIR = "reports"
ARTIFACTS_DIR = "artifacts"
LOGS_DIR = "logs"
DATA_DIR = "data/linked_dataset"


def run_linkage():
    for d in [
        REPORTS_DIR, LOGS_DIR,
        f"{ARTIFACTS_DIR}/candidate_sources",
        f"{ARTIFACTS_DIR}/parsed_tables",
        f"{ARTIFACTS_DIR}/linkage_tables",
        f"{ARTIFACTS_DIR}/specimen_feature_registry",
        DATA_DIR,
        "data/unresolved",
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

    logger = setup_logger(f"{LOGS_DIR}/linkage.log")
    logger.info("=" * 60)
    logger.info("  SPECIMEN LINKAGE — PLA_3dPrinter_RESISTENCE")
    logger.info("=" * 60)

    logger.info("\n[1/7] Inventario de fuentes de linkage")
    source_inventory = discover_linkage_sources(logger, ARTIFACTS_DIR)

    logger.info("\n[2/7] Registro maestro de probetas compresivas")
    registry = inspect_compression_specimens(logger, ARTIFACTS_DIR)

    logger.info("\n[3/7] Parseo y normalización de IDs de probeta")
    parsed_registry, interpretation_notes = parse_specimen_ids(registry, logger, ARTIFACTS_DIR)

    logger.info("\n[4/7] Inferencia de features enlazables")
    linked_registry = infer_feature_links(parsed_registry, interpretation_notes, logger, ARTIFACTS_DIR)

    logger.info("\n[5/7] Validación y clasificación de enlaces")
    validated_registry, link_counts = validate_links(linked_registry, logger, ARTIFACTS_DIR)

    logger.info("\n[6/7] Construcción del dataset final de modelado")
    dataset_summary, df_hc, df_exp, df_unresolved = build_final_model_dataset(
        validated_registry, logger, DATA_DIR
    )

    logger.info("\n[7/7] Exportación de reportes y artefactos")
    export_linkage_outputs(
        source_inventory, registry, parsed_registry, interpretation_notes,
        linked_registry, validated_registry, link_counts,
        dataset_summary, df_hc, df_exp, df_unresolved,
        REPORTS_DIR, ARTIFACTS_DIR, logger
    )

    logger.info("\n" + "=" * 60)
    logger.info("  LINKAGE COMPLETADO")
    logger.info(f"  Especímenes en registro: {len(registry)}")
    logger.info(f"  Link counts: {link_counts}")
    logger.info(f"  Dataset high_confidence: {dataset_summary['high_confidence']['rows']} filas")
    logger.info(f"  Dataset expanded: {dataset_summary['expanded_with_caution']['rows']} filas")
    logger.info(f"  Casos no resueltos: {dataset_summary['unresolved_count']}")
    logger.info("=" * 60)

    hc_rows = dataset_summary["high_confidence"]["rows"]
    exp_rows = dataset_summary["expanded_with_caution"]["rows"]
    hc_feats = dataset_summary["high_confidence"]["feature_cols"]

    if hc_rows >= 15 and len(hc_feats) >= 2:
        logger.info(
            f"\n  >> BLOQUEO PARCIALMENTE LEVANTADO: {hc_rows} especímenes en high_confidence con "
            f"{len(hc_feats)} features. Modelado exploratorio habilitado. "
            f"Advertencia: sin parámetros de proceso FDM el modelo solo puede analizar "
            f"estructura y parámetro de diseño."
        )
    else:
        logger.warning(
            f"\n  >> BLOQUEO ACTIVO: dataset insuficiente para modelado. "
            f"hc_rows={hc_rows}, features={len(hc_feats)}."
        )

    return dataset_summary


if __name__ == "__main__":
    run_linkage()
