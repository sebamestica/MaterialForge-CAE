import os
import re
import pandas as pd
import numpy as np
from ...mechanics.property_extractor import (
    calculate_young_modulus,
    calculate_energy_properties,
    evaluate_curve_quality
)

def parse_fluoroelastomer_seals(file_path, source_id, import_date):
    """
    Parses a single polymer seals CSV file.
    These files have multi-column data: Strain (%) and Stress (MPa) for multiple specimens (L1, L2, R1, etc.).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    
    # Read entire file as raw lines to find headers
    df_raw = pd.read_csv(file_path, header=None)
    
    if df_raw.empty or len(df_raw) < 7:
        return [], [], [], [], []

    # Find the header row index (which contains 'Strain (%)' or similar)
    header_idx = -1
    for idx, row in df_raw.iterrows():
        row_str = [str(x).lower() for x in row]
        if any('strain' in x for x in row_str) and any('stress' in x for x in row_str):
            header_idx = idx
            break

    if header_idx == -1:
        # Default fallback
        header_idx = 5

    # The row above header_idx usually contains specimen names (e.g. L1 (ST: 2.57 mm))
    specimen_names_row = df_raw.iloc[header_idx - 1]
    
    # Data starts after header_idx
    df_data = df_raw.iloc[header_idx + 1:].reset_index(drop=True)

    specimens = []
    print_params = []
    lattice_geometries = []
    curve_points = []
    mechanical_properties = []

    # Read pairs of columns
    num_cols = df_raw.shape[1]
    for col_idx in range(0, num_cols, 2):
        if col_idx + 1 >= num_cols:
            break
            
        spec_label = specimen_names_row.iloc[col_idx]
        if pd.isna(spec_label) or str(spec_label).strip() == '':
            # Try to find label in adjacent columns
            spec_label = specimen_names_row.iloc[col_idx + 1]
            if pd.isna(spec_label) or str(spec_label).strip() == '':
                spec_label = f"Specimen-{col_idx // 2 + 1}"

        spec_label_clean = str(spec_label).strip()
        
        # Extract thickness if present in label (e.g. L1 (ST: 2.57 mm))
        thickness_match = re.search(r'ST:\s*([\d\.]+)', spec_label_clean, re.IGNORECASE)
        thickness = float(thickness_match.group(1)) if thickness_match else 2.0
        
        # Default specimen properties
        width = 6.0 # ASTM Die C width is 6mm
        length = 33.0 # ASTM Die C gauge length is 33mm or 25mm
        area = width * thickness
        
        # Specimen unique ID
        specimen_id = f"SEA-{filename.replace('.csv', '')}-{spec_label_clean.split()[0]}"
        specimen_id = re.sub(r'[^a-zA-Z0-9_\-]', '', specimen_id)

        # Extract columns
        try:
            strain_col = pd.to_numeric(df_data[col_idx], errors='coerce').values
            stress_col = pd.to_numeric(df_data[col_idx + 1], errors='coerce').values
            
            # Clean non-numeric and NaNs
            mask = ~np.isnan(strain_col) & ~np.isnan(stress_col)
            strain_vals = strain_col[mask]
            stress_vals = stress_col[mask]

            if len(strain_vals) < 5:
                continue

            # Strain is in %, convert to mm/mm
            strain_vals = strain_vals / 100.0
            
            # Compute forces and displacements for properties integration
            displacement_mm = strain_vals * length
            force_N = stress_vals * area

            # Integrate properties
            young_mod_MPa, r2_fit = calculate_young_modulus(strain_vals, stress_vals)
            energy_absorbed_J, energy_density_MJ_m3, sea_J_g = calculate_energy_properties(
                displacement_mm, force_N, strain_vals, stress_vals, mass_g=None, test_type="tensile"
            )
            quality_score, quality_warnings = evaluate_curve_quality(
                strain_vals, stress_vals, force_N, displacement_mm
            )

            max_force_N = float(np.max(force_N)) if len(force_N) > 0 else 0.0
            max_stress_MPa = float(np.max(stress_vals)) if len(stress_vals) > 0 else 0.0
            failure_strain = float(np.max(strain_vals)) if len(strain_vals) > 0 else 0.0

            # Store Specimen
            spec_entry = {
                "specimen_id": specimen_id,
                "source_id": source_id,
                "material": "fluoroelastomer",
                "material_family": "rubber",
                "manufacturing_process": "extrusion",
                "printer_model": "unknown",
                "test_type": "tensile",
                "test_standard": "ASTM D412 Die C",
                "specimen_geometry": "dogbone",
                "length_mm": length,
                "width_mm": width,
                "thickness_mm": thickness,
                "cross_section_area_mm2": area,
                "mass_g": np.nan,
                "print_orientation_deg": 0.0,
                "load_orientation": "unknown",
                "replicate": spec_label_clean.split()[0][-1] if len(spec_label_clean.split()[0]) > 1 else "A",
                "notes": f"Auxiliary seal test: {spec_label_clean} from {filename}"
            }
            specimens.append(spec_entry)

            # Store PrintParameters (dummy/empty since it's not FDM)
            params_entry = {
                "specimen_id": specimen_id,
                "layer_height_mm": np.nan,
                "wall_thickness_mm": np.nan,
                "infill_density_percent": 100.0,
                "infill_pattern": "solid",
                "nozzle_temperature_C": np.nan,
                "bed_temperature_C": np.nan,
                "print_speed_mm_s": np.nan,
                "fan_speed_percent": np.nan,
                "flow_rate_percent": np.nan,
                "nozzle_diameter_mm": np.nan,
                "chamber_temperature_C": np.nan,
                "post_curing_time_min": np.nan,
                "post_curing_temperature_C": np.nan
            }
            print_params.append(params_entry)

            # Store LatticeGeometry (dummy/solid)
            lattice_entry = {
                "specimen_id": specimen_id,
                "topology": "solid",
                "cell_size_mm": np.nan,
                "strut_diameter_mm": np.nan,
                "relative_density_percent": 100.0,
                "porosity_percent": 0.0,
                "hybrid_ratio": 0.0,
                "unit_cell_type": "solid",
                "graded_density": False,
                "stl_file_path": None,
                "geometry_file_hash": None
            }
            lattice_geometries.append(lattice_entry)

            # Vectorised cumulative integration for energy property curves
            disp_m_arr = displacement_mm / 1000.0
            if len(disp_m_arr) >= 2:
                dx_disp = np.diff(disp_m_arr)
                y_avg_force = (force_N[:-1] + force_N[1:]) / 2.0
                cum_energy_J_arr = np.concatenate(([0.0], np.cumsum(dx_disp * y_avg_force)))
                cum_energy_J_arr = np.abs(cum_energy_J_arr)
            else:
                cum_energy_J_arr = np.zeros_like(disp_m_arr)

            if len(strain_vals) >= 2:
                dx_strain = np.diff(strain_vals)
                y_avg_stress = (stress_vals[:-1] + stress_vals[1:]) / 2.0
                cum_energy_dens_arr = np.concatenate(([0.0], np.cumsum(dx_strain * y_avg_stress)))
                cum_energy_dens_arr = np.abs(cum_energy_dens_arr)
            else:
                cum_energy_dens_arr = np.zeros_like(strain_vals)

            # Store points
            for i in range(len(strain_vals)):
                pt_entry = {
                    "specimen_id": specimen_id,
                    "test_id": f"TEST-{specimen_id}",
                    "point_index": int(i),
                    "time_s": float(i * 0.1),
                    "force_N": float(force_N[i]),
                    "displacement_mm": float(displacement_mm[i]),
                    "strain": float(strain_vals[i]),
                    "stress_MPa": float(stress_vals[i]),
                    "extensometer_displacement_mm": 0.0,
                    "energy_cumulative_J": float(cum_energy_J_arr[i]),
                    "energy_density_cumulative_MJ_m3": float(cum_energy_dens_arr[i])
                }
                curve_points.append(pt_entry)

            # Store MechanicalProperties
            mech_entry = {
                "specimen_id": specimen_id,
                "test_id": f"TEST-{specimen_id}",
                "max_force_N": max_force_N,
                "max_stress_MPa": max_stress_MPa,
                "ultimate_tensile_strength_MPa": max_stress_MPa,
                "compressive_strength_MPa": np.nan,
                "young_modulus_MPa": young_mod_MPa,
                "failure_strain": failure_strain,
                "strain_at_max_stress": float(strain_vals[np.argmax(stress_vals)]) if len(stress_vals) > 0 else 0.0,
                "max_strain": failure_strain,
                "energy_absorbed_J": energy_absorbed_J,
                "energy_density_MJ_m3": energy_density_MJ_m3,
                "specific_energy_absorption_J_g": np.nan,
                "specific_energy_absorption_kJ_kg": np.nan,
                "plateau_stress_MPa": np.nan,
                "crushing_force_efficiency": np.nan,
                "toughness_MJ_m3": energy_density_MJ_m3,
                "curve_quality_score": quality_score
            }
            mechanical_properties.append(mech_entry)

        except Exception as e:
            print(f"Error parsing columns {col_idx}-{col_idx+1} in polymer seals {filename}: {e}")

    return specimens, print_params, lattice_geometries, curve_points, mechanical_properties
