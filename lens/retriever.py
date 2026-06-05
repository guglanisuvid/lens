"""Retrieves relevant chunks for a query or task."""


def retrieve(query: str, n_results: int = 5) -> list[dict]:
    """
    Embed the query and fetch top-N relevant chunks from the index.
    Returns: [{text, source, page, score}]
    """
    # TODO: implement
    pass
