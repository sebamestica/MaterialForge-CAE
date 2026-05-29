import os
import hashlib
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Import parsers
from .parsers.mendeley_pla_lattice import parse_mendeley_pla_lattice
from .parsers.carbon_pla import parse_carbon_pla_dataset
from .parsers.kaggle_3dprinter import parse_kaggle_3dprinter
from .parsers.figshare_hybrid_lattice import parse_figshare_hybrid_lattice
from .parsers.generic_stress_strain import parse_fluoroelastomer_seals

DATA_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data")
PROCESSED_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/processed")

def calculate_sha256(file_path):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def detect_dataset_type(file_path):
    """
    Detects dataset type from filename, path, sheets, or headers.
    """
    path_str = str(file_path).lower()
    name = file_path.name.lower()
    
    if "nvzrft8c7d" in path_str or "ensayos_mecanicos_validos" in path_str or "ensayos_mecanicos_corrupto" in path_str:
        if name == "compressivedata.xlsx" or name == "compressivedata.csv":
            return "mendeley_pla_lattice_compression"
        elif name == "tensiondataa.xlsx" or name == "tensiondataa.csv":
            return "mendeley_pla_lattice_tension_a"
        elif name == "tensiondatab.xlsx" or name == "tensiondatab.csv":
            return "mendeley_pla_lattice_tension_b"

    if "carbon-pla" in path_str or "carbon_pla" in path_str or "carbon pla" in path_str:
        if name.endswith(".xls") or name.endswith(".xlsx"):
            return "mendeley_carbon_pla"

    if "3dprinter" in path_str or "kaggle" in path_str or name == "data.csv":
        if name == "data.csv":
            return "kaggle_3dprinter"

    if "abaqus" in path_str or "hybrid" in path_str or name.endswith(".inp"):
        return "figshare_hybrid_lattice"

    if "fluoroelastomer" in path_str or "seal" in path_str:
        if name.endswith(".csv"):
            return "generic_stress_strain"

    return "unknown"

def scan_all_files():
    """
    Scans the data directory, identifies files, hashes them, and classifies them.
    Returns a list of dicts.
    """
    files_registry = []
    if not DATA_DIR.exists():
        print(f"Data directory does not exist: {DATA_DIR}")
        return files_registry

    # Scan recursively
    for root, _, files in os.walk(DATA_DIR):
        # Skip processed folder
        if "processed" in root:
            continue
            
        for file in files:
            file_path = Path(root) / file
            # Ignore zip files from direct parsing, we parse unpacked files
            if file.startswith(".") or file.endswith(".zip") or file.endswith(".7z"):
                continue

            try:
                rel_path = file_path.relative_to(DATA_DIR)
                file_hash = calculate_sha256(file_path)
                dtype = detect_dataset_type(file_path)
                
                if dtype == "unknown":
                    continue

                files_registry.append({
                    "relative_path": str(rel_path),
                    "absolute_path": str(file_path),
                    "filename": file,
                    "file_hash": file_hash,
                    "dataset_type": dtype,
                    "size_bytes": file_path.stat().st_size
                })
            except Exception as e:
                print(f"Error scanning file {file}: {e}")

    return files_registry

def run_ingestion_pipeline():
    """
    Executes scanning, parsing, properties calculation, and Parquet creation.
    """
    print("=== STARTING INGESTION PIPELINE ===")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    import_date = datetime.now().isoformat()

    files = scan_all_files()
    
    dataset_sources = []
    all_specimens = []
    all_print_params = []
    all_lattice_geometries = []
    all_curve_points = []
    all_mechanical_properties = []

    manifest = {
        "generated_at": import_date,
        "files_scanned": len(files),
        "sources": {}
    }

    warnings = []

    # Map dataset type to parser
    for file_info in files:
        rel_path = file_info["relative_path"]
        abs_path = file_info["absolute_path"]
        file_hash = file_info["file_hash"]
        dtype = file_info["dataset_type"]
        
        source_id = f"SRC-{hashlib.md5(rel_path.encode()).hexdigest()[:6].upper()}"
        
        # Register DatasetSource
        source_entry = {
            "source_id": source_id,
            "source_name": dtype,
            "source_type": "experimental" if "sim" not in dtype else "simulation",
            "portal_url": "",
            "license": "open_access",
            "file_path": rel_path,
            "file_hash": file_hash,
            "imported_at": import_date,
            "parser_used": "",
            "status": "pending",
            "warnings": ""
        }

        try:
            print(f"Parsing {rel_path} as {dtype}...")
            
            # Dispatch
            if dtype == "mendeley_pla_lattice_compression":
                source_entry["parser_used"] = "parse_mendeley_pla_lattice"
                source_entry["portal_url"] = "https://data.mendeley.com/datasets/nvzrft8c7d/2"
                res = parse_mendeley_pla_lattice(abs_path, "compression", source_id, import_date)
            elif dtype in ["mendeley_pla_lattice_tension_a", "mendeley_pla_lattice_tension_b"]:
                source_entry["parser_used"] = "parse_mendeley_pla_lattice"
                source_entry["portal_url"] = "https://data.mendeley.com/datasets/nvzrft8c7d/2"
                res = parse_mendeley_pla_lattice(abs_path, "tensile", source_id, import_date)
            elif dtype == "mendeley_carbon_pla":
                source_entry["parser_used"] = "parse_carbon_pla_dataset"
                source_entry["portal_url"] = "https://data.mendeley.com/datasets/yb96s7pcsw/1"
                res = parse_carbon_pla_dataset(abs_path, source_id, import_date)
            elif dtype == "kaggle_3dprinter":
                source_entry["parser_used"] = "parse_kaggle_3dprinter"
                source_entry["portal_url"] = "https://www.kaggle.com/datasets/afumetto/3dprinter"
                res = parse_kaggle_3dprinter(abs_path, source_id, import_date)
            elif dtype == "figshare_hybrid_lattice":
                source_entry["parser_used"] = "parse_figshare_hybrid_lattice"
                source_entry["portal_url"] = "https://figshare.com/articles/dataset/Dataset_The_Effects_of_Hybrid_Design_and_Post-curing_Time_on_the_Mechanical_Performance_of_3D-Printed_Lattice_Structures/29205026"
                res = parse_figshare_hybrid_lattice(abs_path, source_id, import_date)
            elif dtype == "generic_stress_strain":
                source_entry["parser_used"] = "parse_fluoroelastomer_seals"
                source_entry["portal_url"] = "https://data.mendeley.com/datasets/c9zsnv7m4p/2"
                res = parse_fluoroelastomer_seals(abs_path, source_id, import_date)
            else:
                continue

            spec, params, geom, curves, mech = res
            
            if len(spec) == 0:
                source_entry["status"] = "empty"
                source_entry["warnings"] = "No specimens parsed from file."
                warnings.append(f"No specimens parsed from {rel_path}")
            else:
                all_specimens.extend(spec)
                all_print_params.extend(params)
                all_lattice_geometries.extend(geom)
                all_curve_points.extend(curves)
                all_mechanical_properties.extend(mech)
                source_entry["status"] = "success"
                print(f"Successfully parsed {len(spec)} specimens.")

        except Exception as e:
            source_entry["status"] = "failed"
            source_entry["warnings"] = str(e)
            warnings.append(f"Failed to parse {rel_path}: {e}")
            print(f"Error parsing file {rel_path}: {e}")

        dataset_sources.append(source_entry)
        manifest["sources"][source_id] = {
            "relative_path": rel_path,
            "hash": file_hash,
            "dataset_type": dtype,
            "status": source_entry["status"]
        }

    # Save manifest
    with open(PROCESSED_DIR / "dataset_manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)

    # Convert to DataFrames and save to Parquet
    print("Saving aggregated data structures to Parquet...")
    
    df_sources = pd.DataFrame(dataset_sources)
    df_specimens = pd.DataFrame(all_specimens)
    df_print_params = pd.DataFrame(all_print_params)
    df_lattice_geometries = pd.DataFrame(all_lattice_geometries)
    df_curve_points = pd.DataFrame(all_curve_points)
    df_mechanical_properties = pd.DataFrame(all_mechanical_properties)

    # Check for empty dataframes to prevent errors
    if df_specimens.empty:
        print("WARNING: No specimens found. Pipeline completed with empty output.")
        return

    # Export canonical Parquet files
    df_sources.to_parquet(PROCESSED_DIR / "sources.parquet", index=False)
    df_specimens.to_parquet(PROCESSED_DIR / "specimens.parquet", index=False)
    df_print_params.to_parquet(PROCESSED_DIR / "print_parameters.parquet", index=False)
    df_lattice_geometries.to_parquet(PROCESSED_DIR / "lattice_geometries.parquet", index=False)
    
    if not df_curve_points.empty:
        df_curve_points.to_parquet(PROCESSED_DIR / "mechanical_curve_points.parquet", index=False)
    else:
        # Create empty placeholder file with columns
        cols = [
            "specimen_id", "test_id", "point_index", "time_s", "force_N", 
            "displacement_mm", "strain", "stress_MPa", "extensometer_displacement_mm",
            "energy_cumulative_J", "energy_density_cumulative_MJ_m3"
        ]
        pd.DataFrame(columns=cols).to_parquet(PROCESSED_DIR / "mechanical_curve_points.parquet", index=False)

    df_mechanical_properties.to_parquet(PROCESSED_DIR / "mechanical_properties.parquet", index=False)

    # Generate quality report
    generate_quality_report(df_specimens, df_mechanical_properties, warnings)

    # Consolidate training table
    try:
        from ..ml.build_training_table import consolidate_training_table
        consolidate_training_table()
    except Exception as e:
        print(f"Error consolidating training table: {e}")

    print("=== INGESTION PIPELINE FINISHED SUCCESSFUL ===")

def generate_quality_report(df_spec, df_mech, warnings):
    """
    Generates data quality report metrics and saves it as JSON.
    """
    total_specimens = len(df_spec)
    null_modulus = df_mech['young_modulus_MPa'].isnull().sum()
    null_strength = df_mech['max_stress_MPa'].isnull().sum()

    report = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "total_specimens": int(total_specimens),
            "materials_count": df_spec['material'].value_counts().to_dict(),
            "test_types_count": df_spec['test_type'].value_counts().to_dict(),
            "avg_curve_quality_score": float(df_mech['curve_quality_score'].mean()) if 'curve_quality_score' in df_mech else 1.0,
            "null_properties": {
                "young_modulus": int(null_modulus),
                "max_stress": int(null_strength)
            }
        },
        "quality_warnings": warnings
    }

    with open(PROCESSED_DIR / "dataset_quality_report.json", "w") as f:
        json.dump(report, f, indent=4)

if __name__ == "__main__":
    run_ingestion_pipeline()
