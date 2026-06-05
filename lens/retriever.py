"""Retrieves relevant chunks for a query or task."""
from lens.embedder import embed_query
from lens.indexer  import query


def retrieve(query_text: str, n_results: int = 5) -> list[dict]:
    """
    Embed the query and fetch top-N relevant chunks from the index.
    Returns: [{text, source, page, score}]
    """
    embedding = embed_query(query_text)
    return query(embedding, n_results=n_results)


def retrieve_multi(queries: list[str], n_per_query: int = 3) -> list[dict]:
    """
    Run multiple queries and return a deduplicated merged result set.
    Used for multi-query RAG in task mode.
    """
    seen  = set()
    merged = []

    for q in queries:
        results = retrieve(q, n_results=n_per_query)
        for chunk in results:
            key = (chunk["source"], chunk["page"], chunk["text"][:50])
            if key not in seen:
                seen.add(key)
                merged.append(chunk)

    # Sort by score descending
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged
