import os
import re
import pandas as pd
import numpy as np
from ...mechanics.property_extractor import (
    calculate_young_modulus,
    calculate_energy_properties,
    calculate_cfe_and_plateau,
    evaluate_curve_quality
)

# Pattern mappings
PATTERN_PREFIXES = {
    'G': 'gyroid',
    'H': 'honeycomb',
    'T': 'triply_periodic',
    'R': 'grid',
    'HEX': 'honeycomb',
    'TRI': 'triangular',
    'GRID': 'grid'
}

def decode_specimen_id(sheet_name):
    """
    Decodes pattern, infill density, and replicate from the sheet name.
    Examples:
    - G29A -> gyroid, 29%, replicate A
    - H36E -> honeycomb, 36%, replicate E
    - Tri49B -> triangular, 49%, replicate B
    - Solid A -> solid, 100%, replicate A
    - 10RA -> grid, 10%, replicate A
    - WWhoneyA -> honeycomb, 35% (default), replicate A
    """
    sheet_name_clean = sheet_name.strip()
    
    # Solid
    if re.search(r'solid', sheet_name_clean, re.IGNORECASE) or re.search(r'sol\.', sheet_name_clean, re.IGNORECASE):
        # Extract replicate if any
        rep_match = re.search(r'([A-G])$', sheet_name_clean)
        replicate = rep_match.group(1) if rep_match else 'A'
        return 'solid', 'solid', 100.0, replicate

    # Pattern G29A, H36E, T24B, etc.
    match = re.match(r'^([GHT])(\d+)([A-G])$', sheet_name_clean, re.IGNORECASE)
    if match:
        prefix = match.group(1).upper()
        density = float(match.group(2))
        replicate = match.group(3).upper()
        pattern = PATTERN_PREFIXES.get(prefix, 'unknown')
        return pattern, pattern, density, replicate

    # Pattern like Tri49B, Hex22C, Grid36A
    match = re.match(r'^([a-zA-Z]+)(\d+)([A-G])$', sheet_name_clean, re.IGNORECASE)
    if match:
        prefix = match.group(1).upper()
        density = float(match.group(2))
        replicate = match.group(3).upper()
        # Find prefix mapping
        pattern = 'unknown'
        for k, v in PATTERN_PREFIXES.items():
            if k in prefix:
                pattern = v
                break
        return pattern, pattern, density, replicate

    # Pattern like 10RA, 36RB, 56RC, 90RA (10 Rect A, etc.)
    match = re.match(r'^(\d+)([R|T])([A-G])', sheet_name_clean, re.IGNORECASE)
    if match:
        density = float(match.group(1))
        prefix = match.group(2).upper()
        replicate = match.group(3).upper()
        pattern = 'grid' if prefix == 'R' else 'triply_periodic'
        return pattern, pattern, density, replicate

    # Custom ones like WWhoneyA
    if 'honey' in sheet_name_clean.lower() or 'wh' in sheet_name_clean.lower() or 'xh' in sheet_name_clean.lower() or 'yh' in sheet_name_clean.lower() or 'zh' in sheet_name_clean.lower():
        # Replicate
        rep_match = re.search(r'([A-G])$', sheet_name_clean)
        replicate = rep_match.group(1).upper() if rep_match else 'A'
        # Default infill for these honeycomb specimens
        return 'honeycomb', 'honeycomb', 35.0, replicate

    # Fallback
    rep_match = re.search(r'([A-G])$', sheet_name_clean)
    replicate = rep_match.group(1).upper() if rep_match else 'A'
    return 'unknown', 'unknown', np.nan, replicate

def clean_dataframe_headers(df):
    """
    Cleans excel dataframes where headers might be in row 0.
    """
    if df.empty:
        return df

    # Check if 'Axial Force' is in the columns
    cols = [str(c).strip() for c in df.columns]
    if 'Axial Force' in cols or 'Stress[MPa]' in cols or 'Stress' in cols or 'Force' in cols:
        df.columns = cols
        return df

    # Check if headers are in row 0
    row_0 = [str(val).strip() for val in df.iloc[0]]
    if 'Axial Force' in row_0 or 'Stress[MPa]' in row_0 or 'Force' in row_0 or 'Stress' in row_0:
        new_cols = []
        for i, val in enumerate(df.iloc[0]):
            if pd.notna(val):
                new_cols.append(str(val).strip())
            else:
                new_cols.append(str(df.columns[i]).strip())
        df.columns = new_cols
        df = df.iloc[1:].reset_index(drop=True)

    # Let's clean standard column name variations
    col_mappings = {
        'Stress[MPa]': 'stress_MPa',
        'stress[mpa]': 'stress_MPa',
        'stress [mpa]': 'stress_MPa',
        'Stress (MPa)': 'stress_MPa',
        'Stress': 'stress_MPa',
        'Strain [mm/mm]': 'strain',
        'strain [mm/mm]': 'strain',
        'Strain': 'strain',
        'StrainExt[mm/mm]': 'strain_ext',
        'StrainExt': 'strain_ext',
        'Axial Force': 'force_N',
        'force [n]': 'force_N',
        'force': 'force_N',
        'Axial Displacement': 'displacement_mm',
        'displacement [mm]': 'displacement_mm',
        'displacement': 'displacement_mm',
        'Time': 'time_s',
        'time': 'time_s',
    }

    cols = df.columns.tolist()
    new_cols = []
    for c in cols:
        c_clean = str(c).strip()
        matched = False
        for k, v in col_mappings.items():
            if k.lower() == c_clean.lower():
                new_cols.append(v)
                matched = True
                break
        if not matched:
            new_cols.append(c_clean)
    
    df.columns = new_cols
    return df

def parse_mendeley_pla_lattice(file_path, test_type, source_id, import_date):
    """
    Parses a single Mendeley PLA lattice file (Excel or CSV) (Compressivedata, TensiondataA, TensiondataB).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    specimens = []
    print_params = []
    lattice_geometries = []
    curve_points = []
    mechanical_properties = []

    # Detect file type
    is_csv = str(file_path).lower().endswith('.csv')

    if is_csv:
        # Load CSV
        main_df = pd.read_csv(file_path)
        if main_df.empty:
            return specimens, print_params, lattice_geometries, curve_points, mechanical_properties

        # Check if row 0 has headers (like in Compressivedata.csv)
        row_0 = main_df.iloc[0].astype(str).tolist()
        if any('axial force' in str(val).lower() for val in row_0):
            new_cols = []
            for idx, val in enumerate(main_df.iloc[0]):
                if idx == 9:
                    new_cols.append('Probeta')
                elif pd.notna(val) and str(val).strip() != '':
                    new_cols.append(str(val).strip())
                else:
                    new_cols.append(main_df.columns[idx])
            main_df.columns = new_cols
            main_df = main_df.iloc[1:].reset_index(drop=True)

        # We must find the 'Probeta' column
        probeta_col = None
        for col in main_df.columns:
            if str(col).lower().strip() == 'probeta':
                probeta_col = col
                break

        if probeta_col is None:
            # Try to guess: if column index 9 exists, use it
            if len(main_df.columns) > 9:
                probeta_col = main_df.columns[9]
                main_df = main_df.rename(columns={probeta_col: 'Probeta'})
                probeta_col = 'Probeta'
            else:
                raise ValueError(f"Probeta column not found in CSV {file_path}")

        # Clean Probeta values (remove whitespace)
        main_df[probeta_col] = main_df[probeta_col].astype(str).str.strip()
        # Group by Probeta
        groups = main_df.groupby(probeta_col)
        # We will loop through the groups like sheets
        sheet_groups = [(name, grp) for name, grp in groups]
    else:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        sheet_groups = []
        for sheet in sheet_names:
            if sheet.lower() == 'resumen':
                continue
            df = xl.parse(sheet)
            sheet_groups.append((sheet, df))

    # Map file dimension defaults
    # In compression, specimens are 50x50x50 mm cubes
    # In tension, they are standard dogbones, say thickness=4mm, width=10mm, gauge length=50mm
    default_length = 50.0
    default_width = 50.0 if test_type == "compression" else 10.0
    default_thickness = 50.0 if test_type == "compression" else 4.0
    default_area = default_width * default_thickness

    for sheet, df in sheet_groups:
        if str(sheet).lower() == 'resumen' or str(sheet).strip() == '' or str(sheet).lower() == 'nan':
            continue

        try:
            df = clean_dataframe_headers(df)
            
            if df.empty:
                continue

            # Decode specimen configuration
            pattern, topology, density, replicate = decode_specimen_id(sheet)
            specimen_id = f"MEN-{test_type[:4].upper()}-{sheet}"

            # Create Specimen entry
            spec_entry = {
                "specimen_id": specimen_id,
                "source_id": source_id,
                "material": "PLA",
                "material_family": "PLA",
                "manufacturing_process": "FDM",
                "printer_model": "Original Prusa i3 MK3S" if test_type == "compression" else "unknown",
                "test_type": test_type,
                "test_standard": "ISO 604" if test_type == "compression" else "ASTM D638",
                "specimen_geometry": "cube" if test_type == "compression" else "dogbone",
                "length_mm": default_length,
                "width_mm": default_width,
                "thickness_mm": default_thickness,
                "cross_section_area_mm2": default_area,
                "mass_g": np.nan,
                "print_orientation_deg": 0.0,
                "load_orientation": "flat" if test_type == "compression" else "on-edge",
                "replicate": replicate,
                "notes": f"Sheet parsed from {os.path.basename(file_path)}"
            }
            specimens.append(spec_entry)

            # Create PrintParameters
            params_entry = {
                "specimen_id": specimen_id,
                "layer_height_mm": 0.2, # default FDM layer height
                "wall_thickness_mm": 1.2, # standard shell
                "infill_density_percent": density if pd.notna(density) else 100.0,
                "infill_pattern": topology,
                "nozzle_temperature_C": 210.0,
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

            # Create LatticeGeometry
            lattice_entry = {
                "specimen_id": specimen_id,
                "topology": topology,
                "cell_size_mm": 8.0 if test_type == "compression" else 4.0, # default cellular engine grid size
                "strut_diameter_mm": np.nan,
                "relative_density_percent": density if pd.notna(density) else 100.0,
                "porosity_percent": 100.0 - density if pd.notna(density) else 0.0,
                "hybrid_ratio": 0.0,
                "unit_cell_type": topology,
                "graded_density": False,
                "stl_file_path": None,
                "geometry_file_hash": None
            }
            lattice_geometries.append(lattice_entry)

            # Clean and parse curve points
            # Ensure required columns are present
            required_cols = ['displacement_mm', 'force_N']
            # Fallback to check if stress and strain are there
            has_disp_force = 'displacement_mm' in df.columns and 'force_N' in df.columns
            has_stress_strain = 'stress_MPa' in df.columns and 'strain' in df.columns

            if not (has_disp_force or has_stress_strain):
                continue

            # Convert to numeric and drop NaNs
            curve_df = df.copy()
            for col in curve_df.columns:
                curve_df[col] = pd.to_numeric(curve_df[col], errors='coerce')
            
            # Fill stress and strain or force and displacement if missing
            if has_disp_force and not has_stress_strain:
                # Compression / Tension curves might have negative sign, clean it
                curve_df['displacement_mm'] = curve_df['displacement_mm'].abs()
                curve_df['force_N'] = curve_df['force_N'].abs()
                
                # Compute stress = force / area
                curve_df['stress_MPa'] = curve_df['force_N'] / default_area
                # Compute strain = displacement / length
                curve_df['strain'] = curve_df['displacement_mm'] / default_length
            elif has_stress_strain and not has_disp_force:
                curve_df['stress_MPa'] = curve_df['stress_MPa'].abs()
                curve_df['strain'] = curve_df['strain'].abs()
                
                # Compute force = stress * area
                curve_df['force_N'] = curve_df['stress_MPa'] * default_area
                # Compute displacement = strain * length
                curve_df['displacement_mm'] = curve_df['strain'] * default_length

            # Fill missing time if not present
            if 'time_s' not in curve_df.columns:
                curve_df['time_s'] = np.arange(len(curve_df)) * 0.1 # assuming 10Hz sampling rate

            # Drop rows where displacement, force, strain, or stress is NaN
            curve_clean = curve_df.dropna(subset=['displacement_mm', 'force_N', 'strain', 'stress_MPa']).reset_index(drop=True)

            # Integrate and extract properties
            displacement_mm_arr = curve_clean['displacement_mm'].values
            force_N_arr = curve_clean['force_N'].values
            strain_arr = curve_clean['strain'].values
            stress_MPa_arr = curve_clean['stress_MPa'].values
            time_s_arr = curve_clean['time_s'].values
            ext_disp = curve_clean['strain_ext'].values if 'strain_ext' in curve_clean.columns else np.zeros_like(displacement_mm_arr)

            young_mod_MPa, r2_fit = calculate_young_modulus(strain_arr, stress_MPa_arr)
            energy_absorbed_J, energy_density_MJ_m3, sea_J_g = calculate_energy_properties(
                displacement_mm_arr, force_N_arr, strain_arr, stress_MPa_arr, mass_g=None, test_type=test_type
            )
            cfe, plateau_stress = calculate_cfe_and_plateau(strain_arr, stress_MPa_arr, force_N_arr, test_type=test_type)
            quality_score, quality_warnings = evaluate_curve_quality(
                strain_arr, stress_MPa_arr, force_N_arr, displacement_mm_arr
            )

            max_force_N = float(np.max(force_N_arr)) if len(force_N_arr) > 0 else 0.0
            max_stress_MPa = float(np.max(stress_MPa_arr)) if len(stress_MPa_arr) > 0 else 0.0
            failure_strain = float(np.max(strain_arr)) if len(strain_arr) > 0 else 0.0

            # Vectorised cumulative integration for energy property curves
            disp_m_arr = curve_clean['displacement_mm'].values / 1000.0
            force_N_arr = curve_clean['force_N'].values
            if len(disp_m_arr) >= 2:
                dx_disp = np.diff(disp_m_arr)
                y_avg_force = (force_N_arr[:-1] + force_N_arr[1:]) / 2.0
                cum_energy_J_arr = np.concatenate(([0.0], np.cumsum(dx_disp * y_avg_force)))
                cum_energy_J_arr = np.abs(cum_energy_J_arr)
            else:
                cum_energy_J_arr = np.zeros_like(disp_m_arr)

            strain_arr = curve_clean['strain'].values
            stress_MPa_arr = curve_clean['stress_MPa'].values
            if len(strain_arr) >= 2:
                dx_strain = np.diff(strain_arr)
                y_avg_stress = (stress_MPa_arr[:-1] + stress_MPa_arr[1:]) / 2.0
                cum_energy_dens_arr = np.concatenate(([0.0], np.cumsum(dx_strain * y_avg_stress)))
                cum_energy_dens_arr = np.abs(cum_energy_dens_arr)
            else:
                cum_energy_dens_arr = np.zeros_like(strain_arr)

            # Store curve points in memory
            for i, row in curve_clean.iterrows():
                pt_entry = {
                    "specimen_id": specimen_id,
                    "test_id": f"TEST-{specimen_id}",
                    "point_index": int(i),
                    "time_s": float(row.get('time_s', i * 0.1)),
                    "force_N": float(row['force_N']),
                    "displacement_mm": float(row['displacement_mm']),
                    "strain": float(row['strain']),
                    "stress_MPa": float(row['stress_MPa']),
                    "extensometer_displacement_mm": float(row.get('strain_ext', 0.0)) * default_length,
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
                "ultimate_tensile_strength_MPa": max_stress_MPa if test_type == "tensile" else np.nan,
                "compressive_strength_MPa": max_stress_MPa if test_type == "compression" else np.nan,
                "young_modulus_MPa": young_mod_MPa,
                "failure_strain": failure_strain,
                "strain_at_max_stress": float(strain_arr[np.argmax(stress_MPa_arr)]) if len(stress_MPa_arr) > 0 else 0.0,
                "max_strain": failure_strain,
                "energy_absorbed_J": energy_absorbed_J,
                "energy_density_MJ_m3": energy_density_MJ_m3,
                "specific_energy_absorption_J_g": sea_J_g if sea_J_g > 0 else np.nan,
                "specific_energy_absorption_kJ_kg": sea_J_g if sea_J_g > 0 else np.nan,
                "plateau_stress_MPa": plateau_stress if test_type == "compression" else np.nan,
                "crushing_force_efficiency": cfe if test_type == "compression" else np.nan,
                "toughness_MJ_m3": energy_density_MJ_m3,
                "curve_quality_score": quality_score
            }
            mechanical_properties.append(mech_entry)

        except Exception as e:
            print(f"Error parsing sheet {sheet} in {os.path.basename(file_path)}: {e}")

    return specimens, print_params, lattice_geometries, curve_points, mechanical_properties
