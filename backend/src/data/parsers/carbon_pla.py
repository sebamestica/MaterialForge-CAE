import os
import re
import pandas as pd
import numpy as np
from ...mechanics.property_extractor import (
    calculate_young_modulus,
    calculate_energy_properties,
    evaluate_curve_quality
)

def parse_carbon_pla_dataset(file_path, source_id, import_date):
    """
    Parses a single Carbon-PLA xls/xlsx file corresponding to a printing angle.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    # Extract angle from filename (e.g. "0 Deg.xls" -> 0.0)
    angle_match = re.search(r'(\d+)\s*Deg', filename, re.IGNORECASE)
    angle = float(angle_match.group(1)) if angle_match else 0.0

    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names

    specimens = []
    print_params = []
    lattice_geometries = []
    curve_points = []
    mechanical_properties = []

    # Read the summary properties from tab 'Data'
    if 'Data' not in sheet_names:
        return [], [], [], [], []

    df_data = xl.parse('Data')
    # Filter rows starting from row 2 where 'Test No' is a valid number
    df_data_clean = df_data.copy()
    # Replace header strings if present
    df_data_clean = df_data_clean[pd.to_numeric(df_data_clean['Test No'], errors='coerce').notna()]
    
    # Store specimen dimensions map: replicate -> area, width, thickness
    specimen_dims = {}
    for _, row in df_data_clean.iterrows():
        try:
            test_no = int(float(row['Test No']))
            replicate = chr(64 + test_no) # 1 -> 'A', 2 -> 'B', 3 -> 'C'
            
            width = float(row.get('Width', 13.0))
            thickness = float(row.get('Thickness', 3.6))
            area = float(row.get('Sectional area', width * thickness))
            
            # Map values
            specimen_dims[test_no] = {
                "replicate": replicate,
                "width": width,
                "thickness": thickness,
                "area": area,
                "max_force_summary": float(row.get('Maximum point', 0.0)),
                "max_stress_summary": float(row.get('Maximum point.1', 0.0)),
                # Convert GPa modulus to MPa
                "young_mod_summary": float(row.get('Elastic modulus', 0.0)) * 1000.0 if pd.notna(row.get('Elastic modulus')) else np.nan,
                "failure_strain_summary": float(row.get('Break point', 0.0)) / 100.0 if pd.notna(row.get('Break point')) else np.nan
            }
        except Exception as e:
            print(f"Error reading specimen row in Carbon-PLA 'Data': {e}")

    # Gauge length from metadata is 50 mm
    gage_length = 50.0

    # Parse individual curve tabs (SS-Curve001, SS-Curve002, SS-Curve003)
    curve_sheets = [s for s in sheet_names if s.startswith('SS-Curve') and not s.endswith('Ave')]

    for sheet in curve_sheets:
        try:
            # Find replicate index
            num_match = re.search(r'Curve(\d+)', sheet)
            if not num_match:
                continue
            curve_idx = int(num_match.group(1))
            
            if curve_idx not in specimen_dims:
                # Fallback to defaults if no matching summary info
                specimen_dims[curve_idx] = {
                    "replicate": chr(64 + curve_idx) if curve_idx <= 26 else 'A',
                    "width": 13.0,
                    "thickness": 3.6,
                    "area": 46.8,
                    "max_force_summary": np.nan,
                    "max_stress_summary": np.nan,
                    "young_mod_summary": np.nan,
                    "failure_strain_summary": np.nan
                }

            spec_dim = specimen_dims[curve_idx]
            replicate = spec_dim["replicate"]
            width = spec_dim["width"]
            thickness = spec_dim["thickness"]
            area = spec_dim["area"]

            specimen_id = f"CAR-{int(angle):02d}D-{replicate}"

            # Create Specimen entry
            spec_entry = {
                "specimen_id": specimen_id,
                "source_id": source_id,
                "material": "Carbon-PLA",
                "material_family": "PLA",
                "manufacturing_process": "FDM",
                "printer_model": "unknown",
                "test_type": "tensile",
                "test_standard": "ASTM D638-03",
                "specimen_geometry": "dogbone",
                "length_mm": 165.0, # ASTM D638 Type I length
                "width_mm": width,
                "thickness_mm": thickness,
                "cross_section_area_mm2": area,
                "mass_g": np.nan,
                "print_orientation_deg": angle,
                "load_orientation": "on-edge",
                "replicate": replicate,
                "notes": f"Carbon-PLA tensile test at {angle} deg print orientation"
            }
            specimens.append(spec_entry)

            # Create PrintParameters
            params_entry = {
                "specimen_id": specimen_id,
                "layer_height_mm": 0.2, # standard fallback
                "wall_thickness_mm": 1.2,
                "infill_density_percent": 100.0, # Solid filament tensile test
                "infill_pattern": "solid",
                "nozzle_temperature_C": 220.0,
                "bed_temperature_C": 60.0,
                "print_speed_mm_s": 50.0,
                "fan_speed_percent": 100.0,
                "flow_rate_percent": 100.0,
                "nozzle_diameter_mm": 0.4,
                "chamber_temperature_C": np.nan,
                "post_curing_time_min": 0.0,
                "post_curing_temperature_C": np.nan
            }
            print_params.append(params_entry)

            # Create LatticeGeometry (none, solid)
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

            # Read curve sheet
            df_curve = xl.parse(sheet)
            # Find actual data rows (skip unit row 0)
            df_curve_clean = df_curve.copy()
            df_curve_clean = df_curve_clean[pd.to_numeric(df_curve_clean['Elongation'], errors='coerce').notna()]
            
            # Extract variables
            displacement_mm_arr = pd.to_numeric(df_curve_clean['Elongation'], errors='coerce').values
            force_N_arr = pd.to_numeric(df_curve_clean['Load'], errors='coerce').values
            
            # Compute stress and strain
            # Stress (MPa) = force (N) / area (mm2)
            stress_MPa_arr = force_N_arr / area
            # Strain = displacement (mm) / gage length (50 mm)
            strain_arr = displacement_mm_arr / gage_length

            # Integrate and extract properties
            young_mod_MPa, r2_fit = calculate_young_modulus(strain_arr, stress_MPa_arr)
            energy_absorbed_J, energy_density_MJ_m3, sea_J_g = calculate_energy_properties(
                displacement_mm_arr, force_N_arr, strain_arr, stress_MPa_arr, mass_g=None, test_type="tensile"
            )
            quality_score, quality_warnings = evaluate_curve_quality(
                strain_arr, stress_MPa_arr, force_N_arr, displacement_mm_arr
            )

            max_force_N = float(np.max(force_N_arr)) if len(force_N_arr) > 0 else 0.0
            max_stress_MPa = float(np.max(stress_MPa_arr)) if len(stress_MPa_arr) > 0 else 0.0
            failure_strain = float(np.max(strain_arr)) if len(strain_arr) > 0 else 0.0

            # Vectorised cumulative integration for energy property curves
            disp_m_arr = displacement_mm_arr / 1000.0
            if len(disp_m_arr) >= 2:
                dx_disp = np.diff(disp_m_arr)
                y_avg_force = (force_N_arr[:-1] + force_N_arr[1:]) / 2.0
                cum_energy_J_arr = np.concatenate(([0.0], np.cumsum(dx_disp * y_avg_force)))
                cum_energy_J_arr = np.abs(cum_energy_J_arr)
            else:
                cum_energy_J_arr = np.zeros_like(disp_m_arr)

            if len(strain_arr) >= 2:
                dx_strain = np.diff(strain_arr)
                y_avg_stress = (stress_MPa_arr[:-1] + stress_MPa_arr[1:]) / 2.0
                cum_energy_dens_arr = np.concatenate(([0.0], np.cumsum(dx_strain * y_avg_stress)))
                cum_energy_dens_arr = np.abs(cum_energy_dens_arr)
            else:
                cum_energy_dens_arr = np.zeros_like(strain_arr)

            # Store curve points
            for i in range(len(displacement_mm_arr)):
                pt_entry = {
                    "specimen_id": specimen_id,
                    "test_id": f"TEST-{specimen_id}",
                    "point_index": int(i),
                    "time_s": float(i * 0.1), # mock time if not present
                    "force_N": float(force_N_arr[i]),
                    "displacement_mm": float(displacement_mm_arr[i]),
                    "strain": float(strain_arr[i]),
                    "stress_MPa": float(stress_MPa_arr[i]),
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
                "young_modulus_MPa": young_mod_MPa if young_mod_MPa > 0 else spec_dim.get("young_mod_summary", np.nan),
                "failure_strain": failure_strain if failure_strain > 0 else spec_dim.get("failure_strain_summary", np.nan),
                "strain_at_max_stress": float(strain_arr[np.argmax(stress_MPa_arr)]) if len(stress_MPa_arr) > 0 else 0.0,
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
            print(f"Error parsing sheet {sheet} in Carbon-PLA {filename}: {e}")

    return specimens, print_params, lattice_geometries, curve_points, mechanical_properties
