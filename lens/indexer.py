"""LanceDB interactions — store and retrieve embeddings locally."""
import os
import lancedb
import pyarrow as pa

DB_PATH    = os.path.join(os.path.expanduser("~"), ".lens", "lancedb")
TABLE_NAME = "lens_docs"

_db    = None
_table = None


def _get_db():
    global _db
    if _db is None:
        os.makedirs(DB_PATH, exist_ok=True)
        _db = lancedb.connect(DB_PATH)
    return _db


def get_table():
    global _table
    if _table is None:
        db = _get_db()
        if TABLE_NAME in db.table_names():
            _table = db.open_table(TABLE_NAME)
    return _table


def add_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Store chunks + their embeddings in LanceDB."""
    global _table
    db = _get_db()

    rows = [
        {
            "vector": emb,
            "text":   chunk["text"],
            "source": chunk["source"],
            "page":   chunk["page"],
        }
        for chunk, emb in zip(chunks, embeddings)
    ]

    if TABLE_NAME in db.table_names():
        db.open_table(TABLE_NAME).add(rows)
        _table = db.open_table(TABLE_NAME)
    else:
        _table = db.create_table(TABLE_NAME, data=rows)


def query(embedding: list[float], n_results: int = 5) -> list[dict]:
    """Find top-N most similar chunks to the query embedding."""
    table = get_table()
    if table is None:
        return []

    results = (
        table.search(embedding)
             .metric("cosine")
             .limit(n_results)
             .to_list()
    )

    return [
        {
            "text":   r["text"],
            "source": r["source"],
            "page":   r["page"],
            "score":  round(1 - r.get("_distance", 0), 3),
        }
        for r in results
    ]


def list_sources() -> list[str]:
    """Return all unique source document names in the index."""
    table = get_table()
    if table is None:
        return []
    rows = table.to_arrow()
    sources = rows.column("source").to_pylist()
    return sorted(set(sources))


def clear_index():
    """Drop the table entirely."""
    global _table
    db = _get_db()
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
    _table = None
