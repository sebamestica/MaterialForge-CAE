import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

class SimpleVectorStore:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.vectors: List[List[float]] = []
        self.chunks: List[Dict[str, Any]] = []

    def clear(self):
        """Clears vectors and chunks in memory."""
        self.vectors = []
        self.chunks = []

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds chunks and their corresponding embeddings to the store."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks size and embeddings size must be equal.")
            
        for chunk, emb in zip(chunks, embeddings):
            self.chunks.append(chunk)
            self.vectors.append(emb)

    def save(self):
        """Persists index to disk in a human-readable JSON format."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunks": self.chunks,
            "vectors": self.vectors
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"SimpleVectorStore: saved index with {len(self.chunks)} items -> {self.index_path}")

    def load(self) -> bool:
        """Loads index from disk."""
        if not self.index_path.exists():
            return False

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.chunks = data.get("chunks", [])
            self.vectors = data.get("vectors", [])
            print(f"SimpleVectorStore: loaded index with {len(self.chunks)} items.")
            return True
        except Exception as e:
            print(f"SimpleVectorStore: error loading index from {self.index_path}: {e}")
            return False

    def similarity_search(self, query_vector: List[float], k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Runs cosine similarity search on the vectors and returns the top k chunks 
        along with similarity scores.
        """
        if not self.vectors or not self.chunks:
            return []

        # Convert to numpy arrays for fast calculations
        V = np.array(self.vectors) # shape: (N, D)
        q = np.array(query_vector)  # shape: (D,)

        # Compute cosine similarity: dot(V, q) / (norm(V) * norm(q))
        dot_product = np.dot(V, q)
        norm_V = np.linalg.norm(V, axis=1)
        norm_q = np.linalg.norm(q)

        # Avoid division by zero
        norm_V[norm_V == 0] = 1e-10
        if norm_q == 0:
            norm_q = 1e-10

        similarities = dot_product / (norm_V * norm_q)

        # Sort and take top k
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            results.append((self.chunks[idx], float(similarities[idx])))
            
        return results
