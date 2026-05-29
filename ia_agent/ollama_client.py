import os
import urllib.request
import json
import time
from typing import List, Dict, Any, Optional

class OllamaClient:
    def __init__(
        self, 
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        keep_alive: Optional[str] = None
    ):
        from backend.src.config import (
            OLLAMA_BASE_URL, OLLAMA_KEEP_ALIVE, OLLAMA_NUM_CTX, 
            OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL
        )
        self.base_url = base_url or OLLAMA_BASE_URL
        self.chat_model_override = chat_model or OLLAMA_CHAT_MODEL
        self.embed_model_override = embed_model or OLLAMA_EMBED_MODEL
        self.keep_alive = keep_alive or OLLAMA_KEEP_ALIVE
        self.num_ctx = OLLAMA_NUM_CTX

    def get_installed_models(self) -> List[str]:
        """Queries local Ollama tags API endpoint to find active models."""
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode())
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            print(f"Ollama tags query error: {e}")
            return []

    def select_best_chat_model(self) -> str:
        """Selects the best installed model according to the project priority."""
        models = self.get_installed_models()
        if not models:
            raise RuntimeError(
                f"Ollama no está en ejecución en {self.base_url} o no hay modelos instalados."
            )

        # Priority 1: User defined model in environment
        if self.chat_model_override:
            for m in models:
                if m.startswith(self.chat_model_override) or self.chat_model_override in m:
                    return m

        # Priority 2: Higher parameter coder/reasoning models
        preferred_models = [
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "llama3.1:8b",
            "llama3.1",
            "llama3.2:3b",
            "gemma3:4b",
            "gemma3",
            "llama3.2",
            "qwen2.5-coder:3b",
            "qwen2.5-coder:1.5b",
            "llama3",
            "gemma2"
        ]

        for pm in preferred_models:
            for m in models:
                if m.startswith(pm) or pm in m:
                    return m

        # Fallback to whatever is installed
        return models[0]

    def select_embedding_model(self) -> str:
        """Selects the best available embedding model."""
        models = self.get_installed_models()
        if not models:
            return "nomic-embed-text"

        if self.embed_model_override in models:
            return self.embed_model_override

        # Look for standard embedding model names
        embedding_keywords = ["nomic", "embed", "all-minilm", "bge-", "mxbai"]
        for kw in embedding_keywords:
            for m in models:
                if kw in m:
                    return m
                    
        return "nomic-embed-text"

    def chat_stream(self, messages: List[Dict[str, str]], model: Optional[str] = None, options: Optional[Dict[str, Any]] = None):
        """Streams NDJSON tokens from Ollama locally."""
        selected_model = model or self.select_best_chat_model()
        
        default_options = {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": self.num_ctx
        }
        if options:
            default_options.update(options)

        ollama_payload = {
            "model": selected_model,
            "messages": messages,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": default_options
        }

        url = f"{self.base_url}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(ollama_payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        # Generator returns the raw NDJSON stream
        def generator():
            try:
                with urllib.request.urlopen(req, timeout=300.0) as response:
                    for line in response:
                        if line:
                            yield line.decode('utf-8')
            except Exception as e:
                yield json.dumps({"error": str(e), "done": True}) + "\n"

        return generator()

    def chat_json(self, messages: List[Dict[str, str]], model: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Queries Ollama expecting a JSON structured response."""
        selected_model = model or self.select_best_chat_model()
        
        default_options = {
            "temperature": 0.1,
            "num_ctx": self.num_ctx
        }
        if options:
            default_options.update(options)

        ollama_payload = {
            "model": selected_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "keep_alive": self.keep_alive,
            "options": default_options
        }

        url = f"{self.base_url}/api/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(ollama_payload).encode(),
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120.0) as response:
                res_data = json.loads(response.read().decode())
                duration_ms = (time.time() - start_time) * 1000
                print(f"[PERF] ollama_chat_json ({selected_model}) took {duration_ms:.2f} ms")
                msg_content = res_data.get("message", {}).get("content", "")
                return json.loads(msg_content)
        except Exception as e:
            print(f"Ollama JSON query error: {e}")
            raise

    def embed_texts(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generates embeddings using Ollama's modern /api/embed endpoint."""
        start_time = time.time()
        selected_model = model or self.select_embedding_model()
        
        # Try modern endpoint: /api/embed
        ollama_payload = {
            "model": selected_model,
            "input": texts,
            "keep_alive": self.keep_alive
        }

        try:
            url = f"{self.base_url}/api/embed"
            req = urllib.request.Request(
                url,
                data=json.dumps(ollama_payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30.0) as response:
                res_data = json.loads(response.read().decode())
                duration_ms = (time.time() - start_time) * 1000
                print(f"[PERF] ollama_embed_texts ({selected_model}) took {duration_ms:.2f} ms")
                return res_data.get("embeddings", [])
        except Exception as e:
            # Fallback to legacy endpoint: /api/embeddings (one by one)
            print(f"Ollama modern /api/embed failed ({e}). Falling back to legacy /api/embeddings...")
            embeddings = []
            for text in texts:
                try:
                    url = f"{self.base_url}/api/embeddings"
                    req = urllib.request.Request(
                        url,
                        data=json.dumps({"model": selected_model, "prompt": text}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=15.0) as response:
                        res_data = json.loads(response.read().decode())
                        embeddings.append(res_data.get("embedding", []))
                except Exception as ex:
                    print(f"Ollama legacy embedding failed: {ex}")
                    # Return zero vector fallback
                    embeddings.append([0.0] * 768)
            duration_ms = (time.time() - start_time) * 1000
            print(f"[PERF] ollama_embed_texts (legacy fallback) took {duration_ms:.2f} ms")
            return embeddings

    def unload_models(self) -> bool:
        """Sends empty keep_alive=0 requests to Ollama to unload models from VRAM."""
        try:
            # Unload chat model
            chat_model = self.select_best_chat_model()
            payload = {"model": chat_model, "messages": [], "keep_alive": 0}
            url = f"{self.base_url}/api/chat"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=5.0) as response:
                    response.read()
            except Exception:
                pass
            
            # Unload embedding model
            embed_model = self.select_embedding_model()
            payload_emb = {"model": embed_model, "input": [], "keep_alive": 0}
            url_emb = f"{self.base_url}/api/embed"
            req_emb = urllib.request.Request(
                url_emb,
                data=json.dumps(payload_emb).encode(),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req_emb, timeout=5.0) as response:
                    response.read()
            except Exception:
                pass
                
            print(f"[OLLAMA] Unloaded models from VRAM/RAM: {chat_model}, {embed_model}")
            return True
        except Exception as e:
            print(f"[OLLAMA] Error unloading models: {e}")
            return False
