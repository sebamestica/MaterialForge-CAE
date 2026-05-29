import os
import time
import json
import sys
import threading
from pathlib import Path
from datetime import datetime

# Setup path resolution for src imports
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

from backend.src.config import INDEX_DIR, RAG_INDEX_TTL_SECONDS, WORKSPACE_DIR
from .vector_store import SimpleVectorStore

class RAGManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RAGManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if self._initialized:
                return
            self.index_dir = INDEX_DIR
            self.index_file = INDEX_DIR / "vector_store.json"
            self.manifest_path = INDEX_DIR / "index_manifest.json"
            self.store = SimpleVectorStore(self.index_file)
            self.store_loaded = False
            self.last_accessed = 0.0
            self.lock = threading.Lock()
            self.ttl_seconds = RAG_INDEX_TTL_SECONDS
            
            # Start background TTL monitor thread
            self.stop_monitor = threading.Event()
            self.monitor_thread = threading.Thread(target=self._monitor_ttl, daemon=True)
            self.monitor_thread.start()
            self._initialized = True

    def is_index_available(self) -> bool:
        """Returns True if the vector index file exists on disk."""
        return self.index_file.exists() and self.manifest_path.exists()

    def is_index_stale(self) -> bool:
        """Checks if the index manifest exists and if it is older than scanned workspace files."""
        if not self.manifest_path.exists():
            return True
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            indexed_at_str = manifest.get("indexed_at")
            if not indexed_at_str:
                return True
            indexed_at = datetime.fromisoformat(indexed_at_str)
            
            # Check modified times of workspace key files
            files_to_check = [
                WORKSPACE_DIR / "README.md",
                WORKSPACE_DIR / "ia_agent" / "README.md",
                WORKSPACE_DIR / "data" / "processed" / "dataset_quality_report.json",
                WORKSPACE_DIR / "data" / "processed" / "dataset_manifest.json"
            ]
            for f in files_to_check:
                if f.exists():
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime > indexed_at:
                        return True
            return False
        except Exception:
            return True

    def get_rag_index(self) -> SimpleVectorStore:
        """Gets loaded SimpleVectorStore, loading it from disk under demand."""
        with self.lock:
            self.last_accessed = time.time()
            if not self.store_loaded:
                start_time = time.time()
                print(f"[RAG_MANAGER] Loading RAG index from {self.index_file}...")
                self.store_loaded = self.store.load()
                duration_ms = (time.time() - start_time) * 1000
                print(f"[PERF] RAG_load took {duration_ms:.2f} ms")
            return self.store

    def unload_rag_index(self):
        """Forces unloading RAG index from memory."""
        with self.lock:
            if self.store_loaded:
                print("[RAG_MANAGER] Unloading RAG index from memory...")
                self.store.clear()
                self.store_loaded = False
                import gc
                gc.collect()

    def reload_rag_index(self) -> SimpleVectorStore:
        """Forces reloading index from disk."""
        self.unload_rag_index()
        return self.get_rag_index()

    def rag_status(self) -> dict:
        """Returns the loading and manifest metadata details of RAG."""
        with self.lock:
            available = self.is_index_available()
            status = {
                "loaded": self.store_loaded,
                "available": available,
                "stale": self.is_index_stale() if available else True,
                "chunks_count": len(self.store.chunks) if self.store_loaded else 0,
                "last_accessed": self.last_accessed,
                "ttl_seconds": self.ttl_seconds
            }
            if available:
                try:
                    with open(self.manifest_path, "r", encoding="utf-8") as f:
                        status["manifest"] = json.load(f)
                except Exception:
                    pass
            return status

    def _monitor_ttl(self):
        """Background loop to unload RAG vector store when TTL expires."""
        while not self.stop_monitor.is_set():
            time.sleep(15) # Check every 15 seconds
            with self.lock:
                if self.store_loaded:
                    inactive_time = time.time() - self.last_accessed
                    if inactive_time >= self.ttl_seconds:
                        print(f"[RAG_MANAGER] RAG index cache TTL expired (inactive for {inactive_time:.1f}s >= {self.ttl_seconds}s). Unloading.")
                        self.store.clear()
                        self.store_loaded = False
                        import gc
                        gc.collect()

# Global accessor function
def get_rag_manager() -> RAGManager:
    return RAGManager()
