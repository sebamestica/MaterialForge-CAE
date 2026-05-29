import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

def calculate_young_modulus(strain, stress):
    """
    Calculates Young's modulus using linear regression in the elastic region.
    Region:
    - strain between 0.0005 and 0.0025 if available.
    - Fallback: first 10% of the curve before the maximum stress.
    Returns (young_modulus_MPa, r2_elastic_fit).
    """
    if len(strain) < 5 or len(stress) < 5:
        return 0.0, 0.0

    # Ensure inputs are numpy arrays
    strain = np.array(strain)
    stress = np.array(stress)

    # Filter out NaNs
    mask = ~np.isnan(strain) & ~np.isnan(stress)
    strain = strain[mask]
    stress = stress[mask]

    if len(strain) < 5:
        return 0.0, 0.0

    # Sort by strain
    idx = np.argsort(strain)
    strain = strain[idx]
    stress = stress[idx]

    # Try standard region: 0.0005 to 0.0025
    elastic_mask = (strain >= 0.0005) & (strain <= 0.0025)
    
    # Fallback if standard region doesn't have enough points
    if np.sum(elastic_mask) < 3:
        max_stress_idx = np.argmax(stress)
        if max_stress_idx > 5:
            # Take the first 10% of points before maximum stress
            fallback_limit = max(3, int(max_stress_idx * 0.1))
            elastic_mask = np.zeros_like(strain, dtype=bool)
            elastic_mask[:fallback_limit] = True
        else:
            # General fallback to first 10% of the whole curve
            fallback_limit = max(3, int(len(strain) * 0.1))
            elastic_mask = np.zeros_like(strain, dtype=bool)
            elastic_mask[:fallback_limit] = True

    x = strain[elastic_mask]
    y = stress[elastic_mask]

    if len(x) < 2:
        return 0.0, 0.0

    # Perform linear fit
    try:
        slope, intercept = np.polyfit(x, y, 1)
        # Calculate R2
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return float(slope), float(r2)
    except Exception:
        return 0.0, 0.0

def calculate_energy_properties(displacement_mm, force_N, strain, stress_MPa, mass_g=None, test_type="compression"):
    """
    Integrates curves to calculate energy absorption.
    - energy_absorbed_J: integrate force (N) vs displacement (m)
    - energy_density_MJ_m3: integrate stress (MPa) vs strain
    - specific_energy_absorption_J_g: energy_absorbed_J / mass_g
    """
    # Ensure inputs are sorted by strain/displacement
    displacement_mm = np.array(displacement_mm)
    force_N = np.array(force_N)
    strain = np.array(strain)
    stress_MPa = np.array(stress_MPa)

    # Clean NaNs
    mask = ~np.isnan(displacement_mm) & ~np.isnan(force_N)
    disp_clean = displacement_mm[mask]
    force_clean = force_N[mask]

    mask_ss = ~np.isnan(strain) & ~np.isnan(stress_MPa)
    strain_clean = strain[mask_ss]
    stress_clean = stress_MPa[mask_ss]

    energy_absorbed_J = 0.0
    energy_density_MJ_m3 = 0.0

    if len(disp_clean) >= 2:
        # Sort by displacement
        idx = np.argsort(disp_clean)
        disp_clean = disp_clean[idx]
        force_clean = force_clean[idx]
        # Convert mm to meters
        disp_m = disp_clean / 1000.0
        energy_absorbed_J = float(trapezoid(force_clean, disp_m))

    if len(strain_clean) >= 2:
        # Sort by strain
        idx = np.argsort(strain_clean)
        strain_clean = strain_clean[idx]
        stress_clean = stress_clean[idx]
        # MPa integrated vs strain yields MJ/m^3 directly
        energy_density_MJ_m3 = float(trapezoid(stress_clean, strain_clean))

    # Handle negative values (sometimes compression curves come with negative sign)
    energy_absorbed_J = abs(energy_absorbed_J)
    energy_density_MJ_m3 = abs(energy_density_MJ_m3)

    sea_J_g = 0.0
    if mass_g is not None and mass_g > 0.0:
        sea_J_g = energy_absorbed_J / float(mass_g)

    return energy_absorbed_J, energy_density_MJ_m3, sea_J_g

def calculate_cfe_and_plateau(strain, stress_MPa, force_N, test_type="compression"):
    """
    Calculates:
    - CFE: crushing_force_efficiency = mean_crushing_force_N / peak_force_N
    - plateau_stress_MPa: mean stress in strain range 0.2 to 0.5 (or fallback)
    Only relevant for compression.
    """
    if test_type != "compression" or len(strain) < 5:
        return 0.0, 0.0

    strain = np.array(strain)
    stress_MPa = np.array(stress_MPa)
    force_N = np.array(force_N)

    # Take absolute values for compression
    stress_abs = np.abs(stress_MPa)
    force_abs = np.abs(force_N)

    # Peak force
    peak_force = np.max(force_abs) if len(force_abs) > 0 else 1.0
    if peak_force == 0:
        peak_force = 1.0

    # Crushing region is usually after elastic limit, say strain >= 0.1
    crush_mask = (strain >= 0.1) & (strain <= 0.6)
    if np.sum(crush_mask) < 3:
        crush_mask = (strain >= 0.05)

    mean_force = np.mean(force_abs[crush_mask]) if np.sum(crush_mask) > 0 else 0.0
    cfe = float(mean_force / peak_force)

    # Plateau Stress (strain 0.2 to 0.5)
    plateau_mask = (strain >= 0.2) & (strain <= 0.5)
    if np.sum(plateau_mask) < 3:
        plateau_mask = (strain >= 0.1) & (strain <= 0.4)
    if np.sum(plateau_mask) < 3:
        plateau_mask = (strain >= 0.05)

    plateau_stress = float(np.mean(stress_abs[plateau_mask])) if np.sum(plateau_mask) > 0 else 0.0

    return cfe, plateau_stress

def evaluate_curve_quality(strain, stress_MPa, force_N, displacement_mm):
    """
    Evaluates curve quality score (0.0 to 1.0):
    - number of points
    - percentage of null values
    - presence of required fields
    - noise/impossible values
    """
    score = 1.0
    warnings = []

    n_points = len(strain)
    if n_points < 10:
        score -= 0.5
        warnings.append("Insufficient data points (< 10)")
    elif n_points < 100:
        score -= 0.1
        warnings.append("Low number of data points (< 100)")

    # Null percentage
    nulls = pd.Series(stress_MPa).isnull().mean()
    if nulls > 0.5:
        score -= 0.4
        warnings.append(f"High percentage of null stress values ({nulls:.1%})")
    elif nulls > 0.05:
        score -= 0.1
        warnings.append(f"Some null stress values ({nulls:.1%})")

    # Noise checking (spikes)
    if n_points > 10:
        stress_series = pd.Series(stress_MPa).interpolate().fillna(0).values
        diffs = np.diff(stress_series)
        std_diff = np.std(diffs)
        # If there are sudden extreme changes, lower the score
        if std_diff > 10.0:  # Stress jumps of > 10 MPa
            score -= 0.2
            warnings.append("Extreme noise or spikes detected in stress values")

    # Physical boundaries
    if np.any(np.array(displacement_mm) < -10.0) or np.any(np.array(displacement_mm) > 200.0):
        score -= 0.2
        warnings.append("Displacement values out of physical bounds")

    score = max(0.0, min(1.0, score))
    return float(score), warnings
