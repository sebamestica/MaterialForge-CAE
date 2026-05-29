from typing import List, Optional
from ..ollama_client import OllamaClient

class OllamaEmbeddings:
    def __init__(self, client: Optional[OllamaClient] = None, model: Optional[str] = None):
        self.client = client or OllamaClient()
        self._model = model

    @property
    def model(self) -> str:
        if self._model is None:
            self._model = self.client.select_embedding_model()
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds multiple documents/chunks."""
        if not texts:
            return []
        return self.client.embed_texts(texts, model=self.model)

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single user search query."""
        res = self.client.embed_texts([text], model=self.model)
        return res[0] if res else [0.0] * 768
