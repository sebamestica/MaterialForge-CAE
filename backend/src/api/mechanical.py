from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from pathlib import Path

router = APIRouter(prefix="/api/mechanical", tags=["mechanical"])

PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

def clean_nan_values(df: pd.DataFrame) -> list:
    """Replaces NaNs with None to produce clean JSON serialization."""
    df_clean = df.replace({np.nan: None})
    return df_clean.to_dict(orient="records")

@router.get("/specimens")
def get_specimens():
    """
    Returns list of all normalised specimens joined with print parameters.
    """
    spec_path = PROCESSED_DIR / "specimens.parquet"
    params_path = PROCESSED_DIR / "print_parameters.parquet"
    
    if not spec_path.exists():
        raise HTTPException(status_code=404, detail="Specimens data not found. Run import first.")

    try:
        df_spec = pd.read_parquet(spec_path)
        if params_path.exists():
            df_params = pd.read_parquet(params_path)
            # Merge to show print settings along with specimens
            df_merged = df_spec.merge(df_params, on="specimen_id", how="left")
        else:
            df_merged = df_spec
            
        return clean_nan_values(df_merged)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/specimens/{specimen_id}/curve")
def get_specimen_curve(specimen_id: str):
    """
    Returns stress-strain and force-displacement curve points for a specific specimen ID.
    """
    curves_path = PROCESSED_DIR / "mechanical_curve_points.parquet"
    
    if not curves_path.exists():
        raise HTTPException(status_code=404, detail="Mechanical curves data not found. Run import first.")

    try:
        df_curves = pd.read_parquet(curves_path)
        # Filter for specimen_id
        df_filtered = df_curves[df_curves["specimen_id"] == specimen_id].copy()
        
        if df_filtered.empty:
            # Try matching with fallback ID format
            # In case the ID in path matches Mendeley but has a slightly different pattern
            df_filtered = df_curves[df_curves["specimen_id"].str.contains(specimen_id, case=False, na=False)].copy()

        if df_filtered.empty:
            raise HTTPException(status_code=404, detail=f"No curve points found for specimen ID: {specimen_id}")

        # Sort by point index
        df_filtered = df_filtered.sort_values(by="point_index")
        return clean_nan_values(df_filtered)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/properties")
def get_mechanical_properties():
    """
    Returns consolidated mechanical properties table.
    """
    props_path = PROCESSED_DIR / "mechanical_properties.parquet"
    spec_path = PROCESSED_DIR / "specimens.parquet"
    
    if not props_path.exists():
        raise HTTPException(status_code=404, detail="Mechanical properties table not found. Run import first.")

    try:
        df_props = pd.read_parquet(props_path)
        if spec_path.exists():
            df_spec = pd.read_parquet(spec_path)[["specimen_id", "material", "test_type", "replicate"]]
            df_merged = df_props.merge(df_spec, on="specimen_id", how="left")
        else:
            df_merged = df_props

        return clean_nan_values(df_merged)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
