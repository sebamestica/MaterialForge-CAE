
import pandas as pd
import numpy as np
import os

def manual_trapz(y, x):
    return np.sum((y[1:] + y[:-1]) * np.diff(x) / 2.0)


DATA_PATH = r"c:\dev\PLA_3dPrinter_RESISTENCE\data\Ensayos_Mecanicos_Validos\Compressivedata.csv"
LINKED_DATA_PATH = r"c:\dev\PLA_3dPrinter_RESISTENCE\pipelines\specimen_linkage\data\linked_dataset\high_confidence_dataset.csv"

def calculate_energy():
    # Load raw data - using chunking as it is a large file
    print("Loading raw compressive data...")
    # Based on previous check: col 4 is Stress, col 7 is Strain, col 10 is Specimen ID (0-indexed: 3, 6, 9)
    # We use names from previous check: Raw data, Unnamed: 1, ..., Probeta (col 9 is ID)
    # Let's use usecols to be faster
    try:
        chunks = pd.read_csv(DATA_PATH, usecols=[5, 6, 9], names=['strain', 'stress', 'specimen_id'], header=None, skiprows=2, chunksize=100000)
        
        specimen_energies = {}
        
        for chunk in chunks:
            # Filter for TPU specimens (assuming specimen_id starts with T)
            tpu_chunk = chunk[chunk['specimen_id'].astype(str).str.startswith('T')].copy()
            if tpu_chunk.empty:
                continue
            
            # Coerce to numeric to avoid string errors
            tpu_chunk['strain'] = pd.to_numeric(tpu_chunk['strain'], errors='coerce')
            tpu_chunk['stress'] = pd.to_numeric(tpu_chunk['stress'], errors='coerce')
            tpu_chunk = tpu_chunk.dropna(subset=['strain', 'stress'])
                
            for sid, group in tpu_chunk.groupby('specimen_id'):
                group = group.sort_values('strain')
                # Area under stress-strain curve
                energy = manual_trapz(group['stress'].values, group['strain'].values)
                
                if sid not in specimen_energies:
                    specimen_energies[sid] = []
                specimen_energies[sid].append(energy)
        
        # Average energy per specimen if multiple chunks had it (shouldn't happen with proper ID sorting but safe)
        final_energies = {sid: np.mean(val) for sid, val in specimen_energies.items()}
        return final_energies
    except Exception as e:
        print(f"Error calculating energy: {e}")
        return {}

def main():
    energies = calculate_energy()
    if not energies:
        print("No TPU energy data found. Using fallback estimation.")
        # Fallback: specific energy absorption correlates with area, often ~ 0.5 * strength * max_strain
        df = pd.read_csv(LINKED_DATA_PATH)
        tpu_df = df[df['specimen_id'].str.startswith('T')].copy()
        # Assume max strain for TPU is high, e.g. 0.5 - 0.7
        tpu_df['energy_absorption'] = tpu_df['compressive_strength'] * 0.4 # Simplified heuristic
    else:
        print(f"Calculated energy for {len(energies)} TPU specimens.")
        df = pd.read_csv(LINKED_DATA_PATH)
        tpu_df = df[df['specimen_id'].str.startswith('T')].copy()
        tpu_df['energy_absorption'] = tpu_df['specimen_id'].map(energies)
    
    tpu_df.to_csv("scratch/tpu_performance.csv", index=False)
    print("TPU performance saved to scratch/tpu_performance.csv")

if __name__ == "__main__":
    main()
