"""Generates embeddings via Ollama (nomic-embed-text) running locally."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBED_MODEL     = "nomic-embed-text"


def _embed(text: str) -> list[float]:
    """Call Ollama embeddings API for a single text."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Returns embedding vectors for a list of text chunks."""
    return [_embed(chunk) for chunk in chunks]


def embed_query(query: str) -> list[float]:
    """Returns embedding vector for a single query string."""
    return _embed(query)


def check_ollama() -> bool:
    """Returns True if Ollama is running and the model is available."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = [m["name"] for m in response.json().get("models", [])]
        return any(EMBED_MODEL in m for m in models)
    except Exception:
        return False
