"""Decomposes tasks and synthesizes structured output via Claude."""


def run_task(description: str) -> dict:
    """
    1. Decompose task into sub-queries
    2. Retrieve relevant chunks per sub-query
    3. Send to Claude with structured output instruction
    4. Return {table, sources, summary}
    """
    # TODO: implement
    pass


def ask_question(question: str) -> dict:
    """
    Standard Q&A with citations.
    Returns {answer, sources: [{source, page, excerpt}]}
    """
    # TODO: implement
    pass
