import os
import pandas as pd
import numpy as np
from pathlib import Path

PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

FEATURES = [
    "material",
    "material_family",
    "manufacturing_process",
    "test_type",
    "layer_height_mm",
    "wall_thickness_mm",
    "infill_density_percent",
    "infill_pattern",
    "nozzle_temperature_C",
    "bed_temperature_C",
    "print_speed_mm_s",
    "fan_speed_percent",
    "nozzle_diameter_mm",
    "print_orientation_deg",
    "load_orientation",
    "topology",
    "cell_size_mm",
    "strut_diameter_mm",
    "relative_density_percent",
    "porosity_percent",
    "hybrid_ratio",
    "post_curing_time_min",
    "post_curing_temperature_C"
]

TARGETS = [
    "max_stress_MPa",
    "young_modulus_MPa",
    "failure_strain",
    "energy_density_MJ_m3",
    "specific_energy_absorption_kJ_kg",
    "compressive_strength_MPa",
    "ultimate_tensile_strength_MPa",
    "plateau_stress_MPa",
    "crushing_force_efficiency"
]

def consolidate_training_table():
    """
    Consolidates specimens, print parameters, geometries, and mechanical properties into a master training table.
    """
    print("=== CONSOLIDATING TRAINING TABLE ===")
    
    # Load parquets
    df_spec = pd.read_parquet(PROCESSED_DIR / "specimens.parquet")
    df_params = pd.read_parquet(PROCESSED_DIR / "print_parameters.parquet")
    df_geom = pd.read_parquet(PROCESSED_DIR / "lattice_geometries.parquet")
    df_mech = pd.read_parquet(PROCESSED_DIR / "mechanical_properties.parquet")

    # Merge on specimen_id
    df_master = df_spec.merge(df_params, on="specimen_id", how="inner")
    df_master = df_master.merge(df_geom, on="specimen_id", how="inner")
    df_master = df_master.merge(df_mech, on="specimen_id", how="inner")

    # Select features & targets
    cols_to_keep = ["specimen_id"] + FEATURES + TARGETS
    
    # Check if all columns exist, if not create empty/nan columns
    for col in cols_to_keep:
        if col not in df_master.columns:
            df_master[col] = np.nan

    df_training = df_master[cols_to_keep].copy()

    # Data cleaning & Imputation (where safe)
    # If ultimate_tensile_strength_MPa or compressive_strength_MPa are missing, fill them with max_stress_MPa based on test_type
    tensile_mask = df_training["test_type"] == "tensile"
    comp_mask = df_training["test_type"] == "compression"

    df_training.loc[tensile_mask & df_training["ultimate_tensile_strength_MPa"].isna(), "ultimate_tensile_strength_MPa"] = df_training["max_stress_MPa"]
    df_training.loc[comp_mask & df_training["compressive_strength_MPa"].isna(), "compressive_strength_MPa"] = df_training["max_stress_MPa"]

    # Deduplicate print_orientation_deg and fan_speed_percent values
    df_training["print_orientation_deg"] = df_training["print_orientation_deg"].fillna(0.0)
    df_training["fan_speed_percent"] = df_training["fan_speed_percent"].fillna(100.0)
    df_training["nozzle_diameter_mm"] = df_training["nozzle_diameter_mm"].fillna(0.4)
    df_training["post_curing_time_min"] = df_training["post_curing_time_min"].fillna(0.0)
    df_training["post_curing_temperature_C"] = df_training["post_curing_temperature_C"].fillna(0.0)

    # Impute categorical variables
    df_training["material"] = df_training["material"].fillna("PLA").astype(str).str.lower()
    df_training["material_family"] = df_training["material_family"].fillna("PLA").astype(str).str.lower()
    df_training["manufacturing_process"] = df_training["manufacturing_process"].fillna("FDM").astype(str).str.lower()
    df_training["infill_pattern"] = df_training["infill_pattern"].fillna("solid").astype(str).str.lower()
    df_training["topology"] = df_training["topology"].fillna("solid").astype(str).str.lower()
    df_training["test_type"] = df_training["test_type"].fillna("tensile").astype(str).str.lower()
    df_training["load_orientation"] = df_training["load_orientation"].fillna("flat").astype(str).str.lower()

    # Convert numeric fields
    numeric_fields = [
        "layer_height_mm", "wall_thickness_mm", "infill_density_percent", 
        "nozzle_temperature_C", "bed_temperature_C", "print_speed_mm_s",
        "fan_speed_percent", "nozzle_diameter_mm", "print_orientation_deg",
        "cell_size_mm", "strut_diameter_mm", "relative_density_percent",
        "porosity_percent", "hybrid_ratio", "post_curing_time_min",
        "post_curing_temperature_C"
    ]
    for col in numeric_fields:
        df_training[col] = pd.to_numeric(df_training[col], errors='coerce')

    # Save to parquet
    out_path = PROCESSED_DIR / "training_table.parquet"
    df_training.to_parquet(out_path, index=False)
    print(f"Master training table successfully consolidated: {len(df_training)} specimens -> {out_path}")
    return df_training

if __name__ == "__main__":
    consolidate_training_table()
