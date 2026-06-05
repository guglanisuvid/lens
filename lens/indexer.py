"""ChromaDB interactions — store and retrieve embeddings locally."""
import os
import uuid
import chromadb

DB_PATH        = os.path.join(os.path.expanduser("~"), ".lens", "chroma_db")
COLLECTION_NAME = "lens_docs"

_client     = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        os.makedirs(DB_PATH, exist_ok=True)
        _client     = chromadb.PersistentClient(path=DB_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Store chunks + their embeddings in ChromaDB."""
    col = get_collection()
    col.add(
        ids        = [str(uuid.uuid4()) for _ in chunks],
        embeddings = embeddings,
        documents  = [c["text"]   for c in chunks],
        metadatas  = [{"source": c["source"], "page": c["page"]} for c in chunks],
    )


def query(embedding: list[float], n_results: int = 5) -> list[dict]:
    """Find top-N most similar chunks to the query embedding."""
    col = get_collection()
    total = col.count()
    if total == 0:
        return []

    results = col.query(
        query_embeddings = [embedding],
        n_results        = min(n_results, total),
        include          = ["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":   doc,
            "source": meta["source"],
            "page":   meta["page"],
            "score":  round(1 - dist, 3),  # cosine similarity
        })
    return chunks


def list_sources() -> list[str]:
    """Return all unique source document names in the index."""
    col = get_collection()
    if col.count() == 0:
        return []
    results = col.get(include=["metadatas"])
    sources = {m["source"] for m in results["metadatas"]}
    return sorted(sources)


def clear_index():
    """Delete the entire collection and recreate it empty."""
    global _collection
    col = get_collection()
    _client.delete_collection(COLLECTION_NAME)
    _collection = None
