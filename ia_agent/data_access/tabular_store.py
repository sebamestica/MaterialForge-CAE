import os
import time
import sys
import pandas as pd
import numpy as np
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Setup path resolution for src imports
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

from backend.src.config import PROCESSED_DIR, DATA_DIR, TABULAR_CACHE_TTL_SECONDS

class TabularStore:
    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(TabularStore, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, processed_dir: Path = PROCESSED_DIR):
        with self._singleton_lock:
            if self._initialized:
                return
            self.processed_dir = processed_dir
            self._training_table: Optional[pd.DataFrame] = None
            self._mech_properties: Optional[pd.DataFrame] = None
            self._specimens: Optional[pd.DataFrame] = None
            self.last_accessed = 0.0
            self._lock = threading.Lock()
            self.ttl_seconds = TABULAR_CACHE_TTL_SECONDS

            # Start TTL monitor thread
            self.stop_monitor = threading.Event()
            self.monitor_thread = threading.Thread(target=self._monitor_ttl, daemon=True)
            self.monitor_thread.start()
            self._initialized = True

    def _update_access(self):
        self.last_accessed = time.time()

    def _load_table(self, table_name: str):
        """Loads a specific Parquet table under demand."""
        try:
            start_time = time.time()
            path = self.processed_dir / f"{table_name}.parquet"
            if not path.exists():
                return
            
            print(f"[TABULAR_STORE] Loading lazy parquet table: {table_name}...")
            df = pd.read_parquet(path)
            
            if table_name == "training_table":
                self._training_table = df
            elif table_name == "mechanical_properties":
                self._mech_properties = df
            elif table_name == "specimens":
                self._specimens = df
                
            duration_ms = (time.time() - start_time) * 1000
            print(f"[PERF] tabular_load of {table_name} took {duration_ms:.2f} ms")
        except Exception as e:
            print(f"[TABULAR_STORE] Error loading Parquet table '{table_name}': {e}")

    @property
    def training_table(self) -> Optional[pd.DataFrame]:
        with self._lock:
            self._update_access()
            if self._training_table is None:
                self._load_table("training_table")
            return self._training_table

    @property
    def mech_properties(self) -> Optional[pd.DataFrame]:
        with self._lock:
            self._update_access()
            if self._mech_properties is None:
                self._load_table("mechanical_properties")
            return self._mech_properties

    @property
    def specimens(self) -> Optional[pd.DataFrame]:
        with self._lock:
            self._update_access()
            if self._specimens is None:
                self._load_table("specimens")
            return self._specimens

    def load_data(self):
        """Manual reload trigger (backward compatibility)."""
        self.reload()

    def reload(self):
        """Forces unloading and triggers reloading."""
        self.unload()
        # Access properties to reload
        _ = self.training_table
        _ = self.mech_properties
        _ = self.specimens

    def unload(self):
        """Clears all cached tables from memory."""
        with self._lock:
            if self._training_table is not None or self._mech_properties is not None or self._specimens is not None:
                print("[TABULAR_STORE] Unloading tabular store DataFrames from memory...")
                self._training_table = None
                self._mech_properties = None
                self._specimens = None
                import gc
                gc.collect()

    def get_available_materials(self) -> List[str]:
        """Returns list of unique materials available in the dataset."""
        df = self.training_table
        if df is not None and "material" in df.columns:
            return [str(x).upper() for x in df["material"].dropna().unique()]
        return ["PLA", "TPU", "ABS", "PETG", "CARBON-PLA"]

    def get_available_patterns(self) -> List[str]:
        """Returns list of unique infill patterns / topologies available."""
        df = self.training_table
        if df is not None and "infill_pattern" in df.columns:
            return [str(x).lower() for x in df["infill_pattern"].dropna().unique()]
        return ["gyroid", "honeycomb", "triply_periodic", "grid"]

    def get_material_summary(self, material: str) -> Dict[str, Any]:
        """Returns average mechanical properties for a given material."""
        df = self.training_table
        if df is None:
            return {"material": material, "status": "no_data"}
        
        df_mat = df[df["material"].str.lower() == material.lower()]
        if df_mat.empty:
            return {"material": material, "status": "not_found"}

        summary = {
            "material": material,
            "samples_count": len(df_mat),
            "avg_max_stress_MPa": float(df_mat["max_stress_MPa"].mean()) if "max_stress_MPa" in df_mat else None,
            "avg_young_modulus_MPa": float(df_mat["young_modulus_MPa"].mean()) if "young_modulus_MPa" in df_mat else None,
            "avg_energy_density_MJ_m3": float(df_mat["energy_density_MJ_m3"].mean()) if "energy_density_MJ_m3" in df_mat else None,
            "infill_range": [float(df_mat["infill_density_percent"].min()), float(df_mat["infill_density_percent"].max())]
        }
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in summary.items()}

    def get_similar_experiments(self, config: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top similar experiments matching material, infill pattern and closest infill density."""
        df = self.training_table
        if df is None or df.empty:
            return []

        material = str(config.get("material", "pla")).lower()
        pattern = str(config.get("infill_pattern", config.get("pattern", "gyroid"))).lower()
        infill = float(config.get("infill_density_percent", config.get("infill", 35.0)))

        # Filter by material and pattern
        df_filtered = df[
            (df["material"].str.lower() == material) &
            (df["infill_pattern"].str.lower() == pattern)
        ].copy()

        if df_filtered.empty:
            # Fallback to material filter only
            df_filtered = df[df["material"].str.lower() == material].copy()

        if df_filtered.empty:
            return []

        # Sort by distance in infill density
        df_filtered["infill_diff"] = (df_filtered["infill_density_percent"] - infill).abs()
        df_filtered = df_filtered.sort_values(by="infill_diff")

        # Select relevant properties
        cols = [
            "specimen_id", "material", "test_type", "infill_density_percent", "infill_pattern",
            "layer_height_mm", "wall_thickness_mm", "max_stress_MPa", "young_modulus_MPa",
            "energy_density_MJ_m3", "specific_energy_absorption_kJ_kg"
        ]
        cols_existing = [c for c in cols if c in df_filtered.columns]
        
        top_df = df_filtered[cols_existing].head(limit)
        return top_df.replace({np.nan: None}).to_dict(orient="records")

    def get_best_configs_for_target(self, target: str, material: Optional[str] = None, test_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves best configurations sorted by a target objective."""
        df = self.training_table
        if df is None or df.empty:
            return []

        df_copy = df.copy()

        # Map target query
        target_col = "max_stress_MPa"
        if "energy" in target.lower():
            target_col = "energy_density_MJ_m3"
        elif "modulus" in target.lower() or "stiffness" in target.lower() or "young" in target.lower():
            target_col = "young_modulus_MPa"
        elif "sea" in target.lower() or "absorption" in target.lower():
            target_col = "specific_energy_absorption_kJ_kg"

        if target_col not in df_copy.columns:
            target_col = "max_stress_MPa"

        # Apply filters
        if material:
            df_copy = df_copy[df_copy["material"].str.lower() == material.lower()]
        if test_type:
            df_copy = df_copy[df_copy["test_type"].str.lower() == test_type.lower()]

        # Filter out rows where target is missing
        df_copy = df_copy.dropna(subset=[target_col])
        if df_copy.empty:
            return []

        # Sort descending
        df_sorted = df_copy.sort_values(by=target_col, ascending=False)
        
        # Deduplicate to show distinct printable recommendations
        df_sorted = df_sorted.drop_duplicates(subset=["material", "test_type", "infill_pattern", "infill_density_percent"])

        cols = [
            "material", "infill_pattern", "infill_density_percent", "layer_height_mm", 
            "wall_thickness_mm", "print_speed_mm_s", "max_stress_MPa", "young_modulus_MPa", 
            "energy_density_MJ_m3", "specific_energy_absorption_kJ_kg"
        ]
        cols_existing = [c for c in cols if c in df_sorted.columns]

        top_df = df_sorted[cols_existing].head(limit)
        return top_df.replace({np.nan: None}).to_dict(orient="records")

    def get_property_ranges(self, material: str, test_type: str) -> Dict[str, Tuple[float, float]]:
        """Returns the min and max values of key mechanical properties for a material and test type."""
        ranges = {}
        df = self.training_table
        if df is None or df.empty:
            return ranges

        df_filtered = df[
            (df["material"].str.lower() == material.lower()) &
            (df["test_type"].str.lower() == test_type.lower())
        ]
        if df_filtered.empty:
            return ranges

        properties = ["max_stress_MPa", "young_modulus_MPa", "energy_density_MJ_m3"]
        for prop in properties:
            if prop in df_filtered.columns:
                valid_vals = df_filtered[prop].dropna()
                if not valid_vals.empty:
                    ranges[prop] = (float(valid_vals.min()), float(valid_vals.max()))
        return ranges

    def get_training_domain(self) -> Dict[str, Any]:
        """Gets min/max boundaries of numeric variables and unique options of categoricals."""
        domain = {
            "bounds": {},
            "categories": {}
        }
        df = self.training_table
        if df is None or df.empty:
            # Defaults fallback
            domain["bounds"] = {
                "layer_height_mm": (0.05, 0.40),
                "wall_thickness_mm": (0.4, 4.0),
                "infill_density_percent": (10.0, 100.0),
                "nozzle_temperature_C": (190.0, 260.0),
                "print_speed_mm_s": (10.0, 150.0),
                "cell_size_mm": (1.0, 10.0),
                "print_orientation_deg": (0.0, 90.0),
                "post_curing_time_min": (0.0, 120.0)
            }
            domain["categories"] = {
                "material": ["pla", "tpu", "abs", "petg", "carbon-pla"],
                "infill_pattern": ["gyroid", "honeycomb", "triply_periodic", "grid"]
            }
            return domain

        # Categoricals
        cat_cols = ["material", "infill_pattern", "test_type", "topology"]
        for col in cat_cols:
            if col in df.columns:
                domain["categories"][col] = [str(x).lower().strip() for x in df[col].dropna().unique()]

        # Numerics
        num_cols = [
            "layer_height_mm", "wall_thickness_mm", "infill_density_percent", 
            "nozzle_temperature_C", "bed_temperature_C", "print_speed_mm_s",
            "cell_size_mm", "print_orientation_deg", "post_curing_time_min"
        ]
        for col in num_cols:
            if col in df.columns:
                valid_vals = df[col].dropna()
                if not valid_vals.empty:
                    domain["bounds"][col] = (float(valid_vals.min()), float(valid_vals.max()))

        return domain

    def _monitor_ttl(self):
        """Evicts dataframes from memory if TTL expires."""
        while not self.stop_monitor.is_set():
            time.sleep(15) # Check every 15 seconds
            with self._lock:
                if self._training_table is not None or self._mech_properties is not None or self._specimens is not None:
                    inactive_time = time.time() - self.last_accessed
                    if inactive_time >= self.ttl_seconds:
                        print(f"[TABULAR_STORE] Tabular cache TTL expired (inactive for {inactive_time:.1f}s >= {self.ttl_seconds}s). Unloading.")
                        self._training_table = None
                        self._mech_properties = None
                        self._specimens = None
                        import gc
                        gc.collect()
