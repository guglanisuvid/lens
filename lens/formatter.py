"""Rich terminal output — tables, citations, errors."""
from rich.console import Console
from rich.table import Table

console = Console()


def print_table(data: list[dict]):
    """Render a list of dicts as a Rich table."""
    # TODO: implement
    pass


def print_answer(answer: str, sources: list[dict]):
    """Render a Q&A answer with cited sources."""
    # TODO: implement
    pass


def print_sources(sources: list[str]):
    """Render the list of indexed documents."""
    # TODO: implement
    pass
