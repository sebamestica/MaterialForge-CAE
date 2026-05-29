import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "rag_index"
MODELS_DIR = DATA_DIR / "models"

# Resource Modes: light, normal, heavy
APP_RESOURCE_MODE = os.getenv("APP_RESOURCE_MODE", "light").lower().strip()
if APP_RESOURCE_MODE not in ["light", "normal", "heavy"]:
    APP_RESOURCE_MODE = "light"

# Load default profiles based on App Resource Mode
if APP_RESOURCE_MODE == "light":
    DEFAULT_ML_TTL = 300           # 5 minutes
    DEFAULT_RAG_TTL = 300          # 5 minutes
    DEFAULT_TABULAR_TTL = 120      # 2 minutes
    DEFAULT_OLLAMA_KEEP_ALIVE = "30s"
    DEFAULT_OLLAMA_NUM_CTX = 4096
    MAX_RAG_CHUNKS = 5
    MAX_TABULAR_ROWS = 5
elif APP_RESOURCE_MODE == "normal":
    DEFAULT_ML_TTL = 900           # 15 minutes
    DEFAULT_RAG_TTL = 900          # 15 minutes
    DEFAULT_TABULAR_TTL = 300      # 5 minutes
    DEFAULT_OLLAMA_KEEP_ALIVE = "10m"
    DEFAULT_OLLAMA_NUM_CTX = 8192
    MAX_RAG_CHUNKS = 8
    MAX_TABULAR_ROWS = 10
else:  # heavy
    DEFAULT_ML_TTL = 3600          # 1 hour
    DEFAULT_RAG_TTL = 3600         # 1 hour
    DEFAULT_TABULAR_TTL = 900      # 15 minutes
    DEFAULT_OLLAMA_KEEP_ALIVE = "30m"
    DEFAULT_OLLAMA_NUM_CTX = 16384
    MAX_RAG_CHUNKS = 15
    MAX_TABULAR_ROWS = 20

# Environment variables overrides
ML_MODEL_TTL_SECONDS = int(os.getenv("ML_MODEL_TTL_SECONDS", str(DEFAULT_ML_TTL)))
RAG_INDEX_TTL_SECONDS = int(os.getenv("RAG_INDEX_TTL_SECONDS", str(DEFAULT_RAG_TTL)))
TABULAR_CACHE_TTL_SECONDS = int(os.getenv("TABULAR_CACHE_TTL_SECONDS", str(DEFAULT_TABULAR_TTL)))

OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", DEFAULT_OLLAMA_KEEP_ALIVE)
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", str(DEFAULT_OLLAMA_NUM_CTX)))
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5-coder:3b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip('/')

# Limits in Prompts
RAG_TOP_K = int(os.getenv("RAG_TOP_K", str(MAX_RAG_CHUNKS)))
TABULAR_TOP_K = int(os.getenv("TABULAR_TOP_K", str(MAX_TABULAR_ROWS)))

print(f"[CONFIG] Loaded profile: {APP_RESOURCE_MODE.upper()}")
print(f"[CONFIG] TTLs -> ML: {ML_MODEL_TTL_SECONDS}s | RAG: {RAG_INDEX_TTL_SECONDS}s | Tabular: {TABULAR_CACHE_TTL_SECONDS}s")
print(f"[CONFIG] Ollama -> Model: {OLLAMA_CHAT_MODEL} | KeepAlive: {OLLAMA_KEEP_ALIVE} | Ctx: {OLLAMA_NUM_CTX}")
