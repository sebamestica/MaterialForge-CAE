import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from .chunker import Chunker
from .embeddings import OllamaEmbeddings
from .vector_store import SimpleVectorStore
from ..data_access.tabular_store import TabularStore

INDEX_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/rag_index")
WORKSPACE_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE")

class Indexer:
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR, index_dir: Path = INDEX_DIR):
        self.workspace_dir = workspace_dir
        self.index_dir = index_dir
        self.index_file = index_dir / "vector_store.json"
        
        self.chunker = Chunker(chunk_size=1000, chunk_overlap=150)
        self.embeddings = OllamaEmbeddings()
        self.store = SimpleVectorStore(self.index_file)
        self.tabular = TabularStore()

    def build_materials_knowledge_chunks(self) -> List[Dict[str, Any]]:
        """
        Generates synthetic markdown knowledge files describing materials summary 
        properties from the tabular store and returns them as chunks.
        """
        chunks = []
        materials = self.tabular.get_available_materials()
        
        for mat in materials:
            summary = self.tabular.get_material_summary(mat)
            if summary.get("status") == "not_found":
                continue
                
            text = (
                f"# Caracterización Mecánica del Material: {mat.upper()}\n\n"
                f"El material {mat.upper()} cuenta con {summary.get('samples_count', 0)} probetas analizadas en la base de datos de MaterialForge.\n"
                f"- Esfuerzo Máximo Promedio (UTS/Compresión): {summary.get('avg_max_stress_MPa', 'N/A')} MPa\n"
                f"- Módulo elástico de Young Promedio: {summary.get('avg_young_modulus_MPa', 'N/A')} MPa\n"
                f"- Densidad de Energía Absorbida Promedio: {summary.get('avg_energy_density_MJ_m3', 'N/A')} MJ/m³\n"
                f"- Rango de Densidad de Infill (Relleno) de entrenamiento: {summary.get('infill_range', 'N/A')} %\n"
            )
            
            chunk_hash = hashlib.md5(f"synthetic_{mat}_{text}".encode()).hexdigest()
            chunks.append({
                "chunk_id": f"CHUNK-SYN-{chunk_hash[:8].upper()}",
                "text": text,
                "metadata": {
                    "source_path": "synthetic/materials_summary.md",
                    "source_type": "md",
                    "chunk_index": 0,
                    "file_hash": hashlib.sha256(text.encode()).hexdigest(),
                    "created_at": datetime.now().isoformat(),
                    "size_chars": len(text)
                }
            })
            
        return chunks

    def scan_workspace_files(self) -> List[Path]:
        """Finds all relevant markdown, text, and JSON report files in the project workspace."""
        files = []
        
        # 1. Main Readme
        readme_main = self.workspace_dir / "README.md"
        if readme_main.exists():
            files.append(readme_main)
            
        # 2. ia_agent Readme
        readme_agent = self.workspace_dir / "ia_agent" / "README.md"
        if readme_agent.exists():
            files.append(readme_agent)
            
        # 3. Reports
        quality_rep = self.workspace_dir / "data" / "processed" / "dataset_quality_report.json"
        if quality_rep.exists():
            files.append(quality_rep)
            
        manifest = self.workspace_dir / "data" / "processed" / "dataset_manifest.json"
        if manifest.exists():
            files.append(manifest)

        return files

    def run_indexing(self) -> Dict[str, Any]:
        """
        Runs the full indexing pipeline: scans, chunks, embeds, 
        saves the vector index, and writes the manifest.
        """
        print("=== STARTING RAG INDEXING PIPELINE ===")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.store.clear()
        
        files_to_index = self.scan_workspace_files()
        all_chunks = []
        
        # 1. Chunks from scanned files
        for f in files_to_index:
            print(f"Indexing file: {f.name}...")
            file_chunks = self.chunker.chunk_file(f, relative_to=self.workspace_dir)
            all_chunks.extend(file_chunks)

        # 2. Add synthetic tabular summaries chunks
        print("Generating synthetic material summaries for RAG context...")
        synthetic_chunks = self.build_materials_knowledge_chunks()
        all_chunks.extend(synthetic_chunks)

        if not all_chunks:
            print("No chunks found to index.")
            return {"status": "empty", "message": "No documents found to index."}

        # 3. Generate Embeddings using Ollama embeddings model
        print(f"Generating embeddings for {len(all_chunks)} text chunks...")
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings_list = self.embeddings.embed_documents(texts)

        # 4. Add to SimpleVectorStore and Save
        self.store.add_documents(all_chunks, embeddings_list)
        self.store.save()

        # 5. Write manifest file
        manifest = {
            "indexed_at": datetime.now().isoformat(),
            "embedding_model": self.embeddings.model,
            "total_documents": len(files_to_index),
            "total_chunks": len(all_chunks),
            "indexed_files": [str(f.relative_to(self.workspace_dir)) for f in files_to_index]
        }
        
        manifest_path = self.index_dir / "index_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4)
            
        print("=== RAG INDEXING PIPELINE COMPLETED ===")
        return {
            "status": "success",
            "total_chunks": len(all_chunks),
            "embedding_model": self.embeddings.model
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Manual RAG Indexer CLI")
    parser.add_argument("--data", type=str, default=str(WORKSPACE_DIR), help="Workspace root directory")
    parser.add_argument("--output", type=str, default=str(INDEX_DIR), help="Output index directory")
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    out_path = Path(args.output).resolve()
    
    print(f"[RAG_CLI] Running indexer on '{data_path}' -> outputting to '{out_path}'")
    idx = Indexer(workspace_dir=data_path, index_dir=out_path)
    idx.run_indexing()
