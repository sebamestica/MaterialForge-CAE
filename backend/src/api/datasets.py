from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from ..data.dataset_scanner import scan_all_files, run_ingestion_pipeline

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

@router.post("/scan")
def scan_datasets():
    """
    Scans the data directory and returns list of recognized files.
    """
    try:
        files = scan_all_files()
        return {
            "status": "success",
            "files_found": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
def import_datasets():
    """
    Runs the full ingestion pipeline to parse, clean, and normalise all datasets.
    """
    try:
        run_ingestion_pipeline()
        return {
            "status": "success",
            "message": "Full ingestion pipeline completed. Parquet files generated in data/processed/."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
def get_dataset_report():
    """
    Returns the dataset quality report and parsing manifest details.
    """
    report_path = PROCESSED_DIR / "dataset_quality_report.json"
    manifest_path = PROCESSED_DIR / "dataset_manifest.json"

    if not report_path.exists() or not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Quality reports not generated yet. Run import endpoint first.")

    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            
        return {
            "manifest": manifest,
            "quality_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")
