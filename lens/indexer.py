"""ChromaDB interactions — store and retrieve embeddings."""


def get_collection():
    """Returns (or creates) the ChromaDB collection."""
    # TODO: implement
    pass


def add_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Store chunks + embeddings in ChromaDB."""
    # TODO: implement
    pass


def query(embedding: list[float], n_results: int = 5) -> list[dict]:
    """Find top-N most similar chunks to the query embedding."""
    # TODO: implement
    pass


def list_sources() -> list[str]:
    """Return all unique source document names in the index."""
    # TODO: implement
    pass


def clear_index():
    """Delete all documents from the index."""
    # TODO: implement
    pass
