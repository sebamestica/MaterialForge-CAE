import os
import time
import joblib
import threading
from pathlib import Path
from src.config import MODELS_DIR, ML_MODEL_TTL_SECONDS

class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if self._initialized:
                return
            self.model = None
            self.last_accessed = 0.0
            self.lock = threading.Lock()
            self.ttl_seconds = ML_MODEL_TTL_SECONDS
            self.model_path = MODELS_DIR / "latest_model.pkl"
            
            # Start background TTL monitor thread
            self.stop_monitor = threading.Event()
            self.monitor_thread = threading.Thread(target=self._monitor_ttl, daemon=True)
            self.monitor_thread.start()
            self._initialized = True

    def get_model(self):
        """Loads and returns the model, updating last accessed time."""
        with self.lock:
            self.last_accessed = time.time()
            if self.model is None:
                start_time = time.time()
                if not self.model_path.exists():
                    print(f"[MODEL_MANAGER] Model file {self.model_path} not found.")
                    return None
                try:
                    print(f"[MODEL_MANAGER] Loading ML model from {self.model_path}...")
                    # Inject BootstrapEnsemble into the __main__ module to allow unpickling models
                    # that were trained as a __main__ script.
                    import sys
                    try:
                        from src.ml.train_models import BootstrapEnsemble
                        main_module = sys.modules.get('__main__')
                        if main_module and not hasattr(main_module, 'BootstrapEnsemble'):
                            setattr(main_module, 'BootstrapEnsemble', BootstrapEnsemble)
                    except Exception as ex:
                        print(f"[MODEL_MANAGER] Debug: could not inject BootstrapEnsemble into __main__: {ex}")

                    self.model = joblib.load(self.model_path)
                    duration_ms = (time.time() - start_time) * 1000
                    print(f"[PERF] ml_model_load took {duration_ms:.2f} ms")
                except Exception as e:
                    print(f"[MODEL_MANAGER] Error loading ML model: {e}")
                    self.model = None
            return self.model

    def unload_model(self):
        """Forces unloading the model from memory."""
        with self.lock:
            if self.model is not None:
                print("[MODEL_MANAGER] Unloading ML model from memory...")
                self.model = None
                import gc
                gc.collect()

    def reload_model(self):
        """Forces reloading the model from disk."""
        self.unload_model()
        return self.get_model()

    def model_status(self) -> dict:
        """Returns the loading and metadata status of the model."""
        with self.lock:
            exists = self.model_path.exists()
            status = {
                "loaded": self.model is not None,
                "available": exists,
                "file_path": str(self.model_path),
                "file_size_bytes": self.model_path.stat().st_size if exists else 0,
                "last_accessed": self.last_accessed,
                "ttl_seconds": self.ttl_seconds
            }
            if self.model is not None:
                # Deduce keys loaded if it's a dict
                if isinstance(self.model, dict):
                    status["trained_targets"] = list(self.model.keys())
            return status

    def _monitor_ttl(self):
        """Background loop to unload the model when TTL expires."""
        while not self.stop_monitor.is_set():
            time.sleep(15) # Check every 15 seconds
            with self.lock:
                if self.model is not None:
                    inactive_time = time.time() - self.last_accessed
                    if inactive_time >= self.ttl_seconds:
                        print(f"[MODEL_MANAGER] ML model cache TTL expired (inactive for {inactive_time:.1f}s >= {self.ttl_seconds}s). Unloading.")
                        self.model = None
                        import gc
                        gc.collect()

# Global accessor function
def get_model_manager() -> ModelManager:
    return ModelManager()
