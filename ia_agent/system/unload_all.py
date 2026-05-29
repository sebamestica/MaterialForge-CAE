import sys
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

from backend.src.ml.model_manager import get_model_manager
from ia_agent.rag.rag_manager import get_rag_manager
from ia_agent.data_access.tabular_store import TabularStore
from ia_agent.ollama_client import OllamaClient

def main():
    print("=== UNLOADING ALL RESOURCES ===")
    get_model_manager().unload_model()
    get_rag_manager().unload_rag_index()
    TabularStore().unload()
    
    print("Unloading Ollama models...")
    client = OllamaClient()
    unloaded = client.unload_models()
    if unloaded:
         print("Ollama models unloaded.")
    print("=== ALL MEMORY CACHES AND MODELS UNLOADED ===")

if __name__ == "__main__":
    main()
