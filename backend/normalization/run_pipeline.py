import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.utils import setup_logger
from src.discover_files import discover_all_files
from src.extract_archives import extract_all_archives
from src.profile_datasets import profile_datasets
from src.detect_duplicates import detect_duplicates
from src.standardize_columns import standardize_columns
from src.clean_values import clean_dataset_values
from src.validate_schemas import validate_and_classify
from src.export_reports import export_summary

def run():
    BASE_DIR = "c:/dev/PLA_3dPrinter_RESISTENCE/data"
    REGISTRY_PATH = "config/file_registry.json"
    RAW_UNPACKED_DIR = "raw_unpacked"
    INTERIM_DIR = "interim"
    CLEANED_DIR = "cleaned"
    REPORTS_DIR = "reports"
    COL_MAP_PATH = "config/column_mappings.json"
    SUMMARY_PATH = "reports/summary.md"
    LOG_FILE = "logs/pipeline.log"
    
    logger = setup_logger(LOG_FILE)
    logger.info("=== INICIANDO PIPELINE DE NORMALIZACIÓN ===")
    
    try:
        discover_all_files(BASE_DIR, REGISTRY_PATH, logger)
        extract_all_archives(REGISTRY_PATH, RAW_UNPACKED_DIR, logger)
        detect_duplicates(REGISTRY_PATH, logger)
        profile_datasets(REGISTRY_PATH, REPORTS_DIR, logger)
        standardize_columns(REGISTRY_PATH, INTERIM_DIR, INTERIM_DIR, COL_MAP_PATH, logger)
        clean_dataset_values(REGISTRY_PATH, CLEANED_DIR, logger)
        validate_and_classify(REGISTRY_PATH, logger)
        export_summary(REGISTRY_PATH, SUMMARY_PATH, logger)
        
        logger.info("=== PIPELINE COMPLETADO EXITOSAMENTE ===")
    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN PIPELINE: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()
