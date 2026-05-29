import os
import pandas as pd
import numpy as np

def parse_kaggle_3dprinter(file_path, source_id, import_date):
    """
    Parses the Kaggle 3D Printer dataset (data.csv).
    This dataset contains process parameters and mechanical properties but no curves.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)
    
    # Handle misspelling of tension_strength in columns
    df.columns = [c.replace('tension_strenght', 'tension_strength') for c in df.columns]

    specimens = []
    print_params = []
    lattice_geometries = []
    curve_points = [] # empty for this dataset
    mechanical_properties = []

    for i, row in df.iterrows():
        specimen_id = f"KAG-FDM-{i:03d}"
        material = str(row['material']).upper()
        
        # Dimensions are not detailed, but standard ASTM D638 Type I dogbone shape is used for FDM tests:
        # standard is 165mm long, 13mm width, 3.2mm thickness.
        width = 13.0
        thickness = 3.2
        area = width * thickness

        # Create Specimen
        spec_entry = {
            "specimen_id": specimen_id,
            "source_id": source_id,
            "material": material,
            "material_family": "PLA" if "PLA" in material else ("ABS" if "ABS" in material else "unknown"),
            "manufacturing_process": "FDM",
            "printer_model": "unknown",
            "test_type": "tensile",
            "test_standard": "ASTM D638",
            "specimen_geometry": "dogbone",
            "length_mm": 165.0,
            "width_mm": width,
            "thickness_mm": thickness,
            "cross_section_area_mm2": area,
            "mass_g": np.nan,
            "print_orientation_deg": 0.0,
            "load_orientation": "flat",
            "replicate": "A",
            "notes": f"Kaggle FDM baseline dataset sample #{i}"
        }
        specimens.append(spec_entry)

        # Create PrintParameters
        params_entry = {
            "specimen_id": specimen_id,
            "layer_height_mm": float(row['layer_height']),
            "wall_thickness_mm": float(row['wall_thickness']),
            "infill_density_percent": float(row['infill_density']),
            "infill_pattern": str(row['infill_pattern']).lower(),
            "nozzle_temperature_C": float(row['nozzle_temperature']),
            "bed_temperature_C": float(row['bed_temperature']),
            "print_speed_mm_s": float(row['print_speed']),
            "fan_speed_percent": float(row['fan_speed']),
            "flow_rate_percent": 100.0,
            "nozzle_diameter_mm": 0.4, # standard nozzle diameter
            "chamber_temperature_C": np.nan,
            "post_curing_time_min": 0.0,
            "post_curing_temperature_C": np.nan
        }
        print_params.append(params_entry)

        # Create LatticeGeometry
        lattice_entry = {
            "specimen_id": specimen_id,
            "topology": str(row['infill_pattern']).lower(),
            "cell_size_mm": np.nan,
            "strut_diameter_mm": np.nan,
            "relative_density_percent": float(row['infill_density']),
            "porosity_percent": 100.0 - float(row['infill_density']),
            "hybrid_ratio": 0.0,
            "unit_cell_type": str(row['infill_pattern']).lower(),
            "graded_density": False,
            "stl_file_path": None,
            "geometry_file_hash": None
        }
        lattice_geometries.append(lattice_entry)

        # Create MechanicalProperties
        max_stress = float(row['tension_strength'])
        elongation_percent = float(row['elongation'])
        failure_strain = elongation_percent / 100.0 # convert percentage to strain mm/mm

        mech_entry = {
            "specimen_id": specimen_id,
            "test_id": f"TEST-{specimen_id}",
            "max_force_N": max_stress * area, # force = stress * area
            "max_stress_MPa": max_stress,
            "ultimate_tensile_strength_MPa": max_stress,
            "compressive_strength_MPa": np.nan,
            "young_modulus_MPa": np.nan, # Modulus not present in this dataset
            "failure_strain": failure_strain,
            "strain_at_max_stress": failure_strain,
            "max_strain": failure_strain,
            "energy_absorbed_J": np.nan,
            "energy_density_MJ_m3": np.nan,
            "specific_energy_absorption_J_g": np.nan,
            "specific_energy_absorption_kJ_kg": np.nan,
            "plateau_stress_MPa": np.nan,
            "crushing_force_efficiency": np.nan,
            "toughness_MJ_m3": np.nan,
            "curve_quality_score": 1.0 # default high score since values are clean, though no curve points exist
        }
        mechanical_properties.append(mech_entry)

    return specimens, print_params, lattice_geometries, curve_points, mechanical_properties
