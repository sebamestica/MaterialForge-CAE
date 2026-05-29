from .ollama_client import OllamaClient

def select_best_model() -> str:
    """Selects the best available chat model from Ollama tags."""
    client = OllamaClient()
    return client.select_best_chat_model()

def select_embedding_model() -> str:
    """Selects the best available embedding model from Ollama tags."""
    client = OllamaClient()
    return client.select_embedding_model()
