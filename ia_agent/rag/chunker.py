import re
import hashlib
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

class Chunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """Splits text by character size with overlap, trying to respect paragraphs or sentences."""
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunks.append(text[start:])
                break

            # Try to break on paragraph
            p_break = text.rfind("\n\n", start, end)
            if p_break != -1 and p_break > start + self.chunk_size // 2:
                end = p_break + 2
            else:
                # Try to break on line
                l_break = text.rfind("\n", start, end)
                if l_break != -1 and l_break > start + self.chunk_size // 2:
                    end = l_break + 1
                else:
                    # Try to break on sentence/period
                    s_break = text.rfind(". ", start, end)
                    if s_break != -1 and s_break > start + self.chunk_size // 2:
                        end = s_break + 2

            chunks.append(text[start:end])
            start = end - self.chunk_overlap

        return [c.strip() for c in chunks if c.strip()]

    def chunk_file(self, file_path: Path, relative_to: Path = Path(".")) -> List[Dict[str, Any]]:
        """Reads and chunks a file, generating detailed metadata."""
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"Chunker: error reading {file_path}: {e}")
            return []

        try:
            rel_path = file_path.relative_to(relative_to)
        except Exception:
            rel_path = file_path

        file_hash = hashlib.sha256(content.encode()).hexdigest()
        created_at = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        
        raw_chunks = self.split_text(content)
        
        chunks_with_metadata = []
        for i, text in enumerate(raw_chunks):
            chunk_hash = hashlib.md5(f"{file_hash}_{i}_{text}".encode()).hexdigest()
            chunks_with_metadata.append({
                "chunk_id": f"CHUNK-{chunk_hash[:8].upper()}",
                "text": text,
                "metadata": {
                    "source_path": str(rel_path),
                    "source_type": file_path.suffix.lstrip(".").lower() or "txt",
                    "chunk_index": i,
                    "file_hash": file_hash,
                    "created_at": created_at,
                    "size_chars": len(text)
                }
            })
            
        return chunks_with_metadata
