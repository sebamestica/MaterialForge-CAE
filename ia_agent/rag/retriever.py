from pathlib import Path
from typing import List, Dict, Any, Optional

from .embeddings import OllamaEmbeddings
from .vector_store import SimpleVectorStore

INDEX_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/rag_index")

class Retriever:
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index_dir = index_dir
        self.embeddings = OllamaEmbeddings()

    @property
    def store(self):
        from .rag_manager import get_rag_manager
        return get_rag_manager().get_rag_index()

    @property
    def store_loaded(self):
        from .rag_manager import get_rag_manager
        return get_rag_manager().store_loaded

    def reload(self):
        """Reloads index from disk."""
        from .rag_manager import get_rag_manager
        get_rag_manager().reload_rag_index()

    def retrieve_context(self, query: str, current_config: Dict[str, Any], intent: str, k: int = 6) -> List[Dict[str, Any]]:
        """
        Embeds query, searches vector store, and applies optional metadata 
        filtering to return relevant context chunks.
        """
        from .rag_manager import get_rag_manager
        if not get_rag_manager().is_index_available():
            return []

        # Get loaded vector store (triggers lazy loading and latency logs)
        vector_store = self.store
        if not get_rag_manager().store_loaded:
            return []

        # 1. Generate query embedding
        query_vector = self.embeddings.embed_query(query)
        
        # 2. Similarity search (get double elements first for filtering)
        raw_results = vector_store.similarity_search(query_vector, k=k*2)

        # 3. Apply metadata filters (if config specified material)
        material = str(current_config.get("material", "")).lower().strip()
        filtered_results = []
        
        for chunk, score in raw_results:
            metadata = chunk.get("metadata", {})
            source_path = str(metadata.get("source_path", "")).lower()
            
            # Keep if:
            # - no material filter specified, OR
            # - chunk is a general documentation file (README, etc.) OR
            # - chunk matches the active material
            if not material:
                filtered_results.append((chunk, score))
            elif "readme" in source_path:
                filtered_results.append((chunk, score))
            elif material in source_path or material in chunk["text"].lower():
                filtered_results.append((chunk, score))
            else:
                # Include as low priority
                filtered_results.append((chunk, score * 0.9))

        # Re-sort after adjusting scores
        filtered_results = sorted(filtered_results, key=lambda x: x[1], reverse=True)[:k]

        formatted = []
        for chunk, score in filtered_results:
            formatted.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "source": chunk["metadata"]["source_path"],
                "confidence": score
            })

        return formatted
