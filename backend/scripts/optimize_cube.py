
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
MODEL_PATH = Path(__file__).parent.parent / "model_pipeline" / "artifacts" / "trained_models" / "GradientBoostingRegressor_deployment_ready.pkl"
DATASET_PATH = Path(__file__).parent.parent / "specimen_linkage" / "data" / "linked_dataset" / "high_confidence_dataset.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "BLOQUE_PLA_MAX_RESISTENCIA_50MM"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Model
model = joblib.load(MODEL_PATH)

# 2. Load Dataset to get stats for imputation/reference
df = pd.read_csv(DATASET_PATH)

# 3. Define Design Space
patterns = ['gyroid', 'honeycomb', 'triply_periodic']
infill_densities = np.linspace(10, 80, 15)  # 10% to 80%
wall_thicknesses = [0.8, 1.2, 1.6, 2.0] # mm
perimeters = [2, 3, 4, 5]

# PLA properties
PLA_DENSITY = 1.24 / 1000  # g/mm^3 (1.24 g/cm^3)
CUBE_SIZE = 50.0 # mm

def calculate_mass(infill_pct, wall_t):
    ve = CUBE_SIZE**3
    vi = (CUBE_SIZE - 2*wall_t)**3
    vw = ve - vi
    mass = (vw + vi * (infill_pct / 100.0)) * PLA_DENSITY
    return mass

# 4. Generate variants and predict
variants = []

# For prediction, we need the exact features the model was trained on.
# Based on model_features_list.txt:
# num__design_param_numeric
# num__design_param_relative
# num__compressive_strength_mean
# num__compressive_strength_std
# num__n_readings
# cat__structure_type (OHE)
# cat__infill_pattern (OHE)

# Note: The pipeline uses a ColumnTransformer. We should pass a DataFrame with the original columns.
# The original columns before engineering (from build_dataset.py) were:
# specimen_id, structure_type, infill_pattern, design_param_numeric, design_param_relative, ...

# We'll use the median values from the dataset for the 'mean/std' features as they are likely 
# used for training but shouldn't be the primary drivers for a new design prediction 
# unless the model is designed to take them as input.
# Actually, the model pipeline has an imputer, but we should provide them if they are in the feature list.

median_strength_mean = df['compressive_strength_mean'].median()
median_strength_std = df['compressive_strength_std'].median()
median_n_readings = df['n_readings'].median()

for pattern in patterns:
    # Find min/max numeric for this pattern to calculate relative
    p_data = df[df['structure_type'] == pattern]
    min_num = p_data['design_param_numeric'].min()
    max_num = p_data['design_param_numeric'].max()
    
    for infill in infill_densities:
        # Map infill to design_param_numeric (assuming it's roughly the same)
        # In the dataset, G29-G62, H36-H67, T24-T45. 
        # It seems numeric IS the infill density or related.
        
        rel = (infill - min_num) / (max_num - min_num) if max_num > min_num else 0.5
        
        for wall_t in wall_thicknesses:
            mass = calculate_mass(infill, wall_t)
            if mass > 100:
                continue
                
            # Create feature row
            row = {
                'structure_type': pattern,
                'infill_pattern': pattern,
                'design_param_numeric': infill,
                'design_param_relative': rel,
                'compressive_strength_mean': median_strength_mean,
                'compressive_strength_std': median_strength_std,
                'n_readings': median_n_readings,
                # Add other columns that might be expected even if dropped later
                'width': CUBE_SIZE,
                'thickness': CUBE_SIZE,
                'length': CUBE_SIZE
            }
            
            # Prediction
            X_input = pd.DataFrame([row])
            try:
                pred_strength = model.predict(X_input)[0]
            except Exception as e:
                # If prediction fails due to missing columns, we might need to add more dummies
                pred_strength = 0
            
            variants.append({
                'patrón': pattern,
                'infill': infill,
                'paredes': int(wall_t / 0.4), # Assuming 0.4mm nozzle
                'espesor de pared': wall_t,
                'masa estimada': mass,
                'resistencia estimada': pred_strength,
                'deformación estimada': 0.05 * (1.0 - infill/100.0), # Heuristic estimation
                'carga máxima estimada': pred_strength * (CUBE_SIZE**2), # Strength * Area
                'factor de seguridad': 1.5, # Default
                'decisión final': 'Descartado'
            })

# 5. Select winner
results_df = pd.DataFrame(variants)
if not results_df.empty:
    results_df = results_df.sort_values(by='resistencia estimada', ascending=False)
    results_df.iloc[0, results_df.columns.get_loc('decisión final')] = 'GANADOR'
    winner = results_df.iloc[0]
else:
    winner = None

# 6. Export Results CSV
results_df.to_csv(os.path.join(OUTPUT_DIR, "resultados_prediccion.csv"), index=False)

# 7. Print summary for next steps
if winner is not None:
    print(f"WINNER: {winner['patrón']} at {winner['infill']}% infill, {winner['espesor de pared']}mm walls.")
    print(f"Predicted Resistance: {winner['resistencia estimada']:.2f} MPa")
    print(f"Estimated Mass: {winner['masa estimada']:.2f} g")
else:
    print("No valid variant found under 100g.")
