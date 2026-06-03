import os
import json
import hashlib
from typing import Dict, Any, Optional

class TPMSPerformanceDatabase:
    """
    Performance database and geometric cache for TPMS designs.
    Caches calculated geometric metrics and prediction scores to speed up
    the multiobjective constraint solving process.
    """
    def __init__(self, cache_file: str = "C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/tpms_performance_cache.json"):
        self.cache_file = cache_file
        self.cache = {}
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"[TPMSPerformanceDatabase] Error loading cache: {e}")
                self.cache = {}

    def save_cache(self):
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"[TPMSPerformanceDatabase] Error saving cache: {e}")

    def _get_key(self, params: Dict[str, Any]) -> str:
        # Standardize key creation by sorting parameters
        key_str = f"{params.get('pattern')}_{params.get('infillDensity')}_{params.get('wallThickness')}_{params.get('infillThickness', 1.0)}_{params.get('cellSize')}_{params.get('size')}_{params.get('material')}_{params.get('orientation')}_{params.get('resolution')}"
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    def get_entry(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        key = self._get_key(params)
        return self.cache.get(key)

    def set_entry(self, params: Dict[str, Any], data: Dict[str, Any]):
        key = self._get_key(params)
        self.cache[key] = data
        self.save_cache()
