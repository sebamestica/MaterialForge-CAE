from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import pandas as pd
import numpy as np
from pathlib import Path
from ..ml.build_training_table import consolidate_training_table
from ..ml.train_models import train_and_evaluate
from ..ml.predict import Predictor

router = APIRouter(prefix="/api/ml", tags=["ml"])

MODELS_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/models")
PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

# Global predictor instance
predictor = Predictor()

class PredictPayload(BaseModel):
    material: str
    material_family: Optional[str] = "pla"
    manufacturing_process: Optional[str] = "fdm"
    test_type: str # tensile, compression
    layer_height_mm: float
    wall_thickness_mm: float
    infill_density_percent: float
    infill_pattern: str # gyroid, honeycomb, triply_periodic, grid, triangular, solid
    nozzle_temperature_C: float
    bed_temperature_C: float
    print_speed_mm_s: float
    fan_speed_percent: Optional[float] = 100.0
    nozzle_diameter_mm: Optional[float] = 0.4
    print_orientation_deg: Optional[float] = 0.0
    load_orientation: Optional[str] = "flat"
    topology: Optional[str] = None
    cell_size_mm: Optional[float] = 8.0
    strut_diameter_mm: Optional[float] = 0.0
    relative_density_percent: Optional[float] = None
    porosity_percent: Optional[float] = None
    hybrid_ratio: Optional[float] = 0.0
    post_curing_time_min: Optional[float] = 0.0
    post_curing_temperature_C: Optional[float] = 0.0

class OptimizePayload(BaseModel):
    target: str # maximize_energy_absorption, maximize_strength, maximize_stiffness, balance_strength_energy_weight
    material: Optional[str] = None
    test_type: Optional[str] = None

@router.post("/retrain")
def retrain_models():
    """
    Consolidates dataset tables and retrains XGBoost/RandomForest predict models.
    """
    try:
        # 1. Consolidate training table
        consolidate_training_table()
        # 2. Retrain models
        train_and_evaluate()
        # 3. Reload predictor model pipelines
        predictor.reload()
        return {
            "status": "success",
            "message": "Model pipelines successfully retrained and reloaded in predictor memory."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
def get_ml_metrics():
    """
    Returns metrics and feature importances of last trained model pipelines.
    """
    metrics_path = MODELS_DIR / "metrics.json"
    feat_imp_path = MODELS_DIR / "feature_importance.json"
    registry_path = MODELS_DIR / "model_registry.json"

    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="No model metadata found. Run retrain first.")

    try:
        with open(registry_path, "r") as f:
            registry = json.load(f)
        
        feat_imp = {}
        if feat_imp_path.exists():
            with open(feat_imp_path, "r") as f:
                feat_imp = json.load(f)
                
        return {
            "registry": registry,
            "feature_importance": feat_imp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading ML files: {str(e)}")

@router.post("/predict")
def predict_properties(payload: PredictPayload):
    """
    Predicts mechanical properties with uncertainty and checks for extrapolation using Domain Guard.
    """
    # Transform payload Pydantic model to dictionary
    data = payload.model_dump()
    
    # Fill defaults for topology / relative density if missing
    if not data["topology"]:
        data["topology"] = data["infill_pattern"]
    if data["relative_density_percent"] is None:
        data["relative_density_percent"] = data["infill_density_percent"]
    if data["porosity_percent"] is None:
        data["porosity_percent"] = 100.0 - data["infill_density_percent"]

    try:
        res = predictor.predict_mechanical_properties(data)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.post("/optimize")
def optimize_config(payload: OptimizePayload):
    """
    Recommends print and lattice parameter configurations within the experimental domain.
    """
    table_path = PROCESSED_DIR / "training_table.parquet"
    if not table_path.exists():
        raise HTTPException(status_code=404, detail="Training table not found. Scan and import datasets first.")

    try:
        df = pd.read_parquet(table_path)
        if df.empty:
            raise HTTPException(status_code=400, detail="Training dataset is empty.")

        # Apply filters if provided
        if payload.material:
            df = df[df["material"].str.lower() == payload.material.lower()]
        if payload.test_type:
            df = df[df["test_type"].str.lower() == payload.test_type.lower()]

        if df.empty:
            return {"status": "success", "recommendations": []}

        # Calculate optimization sorting
        target_name = payload.target
        
        if target_name == "maximize_energy_absorption":
            # Sort by energy density or SEA
            df_sorted = df.sort_values(by="energy_density_MJ_m3", ascending=False, na_position='last')
        elif target_name == "maximize_strength":
            # Sort by max stress
            df_sorted = df.sort_values(by="max_stress_MPa", ascending=False, na_position='last')
        elif target_name == "maximize_stiffness":
            # Sort by Young's Modulus
            df_sorted = df.sort_values(by="young_modulus_MPa", ascending=False, na_position='last')
        elif target_name == "balance_strength_energy_weight":
            # Balance composite index
            # Normalise metrics
            max_stress = df["max_stress_MPa"].max()
            max_energy = df["energy_density_MJ_m3"].max()
            max_infill = df["infill_density_percent"].max()
            
            stress_factor = df["max_stress_MPa"] / max_stress if max_stress > 0 else 0
            energy_factor = df["energy_density_MJ_m3"] / max_energy if max_energy > 0 else 0
            weight_factor = 1.0 - (df["infill_density_percent"] / max_infill) if max_infill > 0 else 0
            
            df["composite_score"] = (stress_factor * 0.4) + (energy_factor * 0.4) + (weight_factor * 0.2)
            df_sorted = df.sort_values(by="composite_score", ascending=False, na_position='last')
        else:
            raise HTTPException(status_code=400, detail=f"Unknown target optimization: {target_name}")

        # Drop duplicate specimen configurations to recommend unique setups
        df_sorted = df_sorted.drop_duplicates(subset=["material", "test_type", "infill_pattern", "infill_density_percent"])

        # Take top 3 recommendations
        top_recs = df_sorted.head(3).replace({np.nan: None}).to_dict(orient="records")

        # Clean specimen_id from recommendations to make them general
        recommendations = []
        for rec in top_recs:
            recommendations.append({
                "parameters": {
                    "material": rec["material"],
                    "test_type": rec["test_type"],
                    "infill_pattern": rec["infill_pattern"],
                    "infill_density_percent": rec["infill_density_percent"],
                    "layer_height_mm": rec["layer_height_mm"],
                    "wall_thickness_mm": rec["wall_thickness_mm"],
                    "nozzle_temperature_C": rec["nozzle_temperature_C"],
                    "bed_temperature_C": rec["bed_temperature_C"],
                    "print_speed_mm_s": rec["print_speed_mm_s"],
                    "cell_size_mm": rec["cell_size_mm"],
                    "print_orientation_deg": rec["print_orientation_deg"]
                },
                "expected_performance": {
                    "max_stress_MPa": rec["max_stress_MPa"],
                    "young_modulus_MPa": rec["young_modulus_MPa"],
                    "failure_strain": rec["failure_strain"],
                    "energy_density_MJ_m3": rec["energy_density_MJ_m3"],
                    "specific_energy_absorption_kJ_kg": rec["specific_energy_absorption_kJ_kg"],
                    "compressive_strength_MPa": rec["compressive_strength_MPa"],
                    "ultimate_tensile_strength_MPa": rec["ultimate_tensile_strength_MPa"],
                    "plateau_stress_MPa": rec["plateau_stress_MPa"],
                    "crushing_force_efficiency": rec["crushing_force_efficiency"]
                }
            })

        return {
            "status": "success",
            "target_optimized": target_name,
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
