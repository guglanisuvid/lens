"""Rich terminal output — tables, citations, answers."""
from rich.console   import Console
from rich.table     import Table
from rich.panel     import Panel
from rich.markdown  import Markdown
from rich.text      import Text
from rich           import box

console = Console()


def print_output(output: str, sources: list[dict]):
    """Render task output (markdown) with sources."""
    console.print()
    console.print(Panel(Markdown(output), title="[bold blue]Result[/bold blue]", border_style="blue"))
    _print_sources(sources)


def print_answer(answer: str, sources: list[dict]):
    """Render a Q&A answer with cited sources."""
    console.print()
    console.print(Panel(Markdown(answer), title="[bold green]Answer[/bold green]", border_style="green"))
    _print_sources(sources)


def print_sources_list(sources: list[str]):
    """Render the list of indexed documents."""
    if not sources:
        console.print("[yellow]No documents indexed yet. Run: lens upload <file>[/yellow]")
        return

    table = Table(title="Indexed Documents", box=box.ROUNDED, border_style="dim")
    table.add_column("#",        style="dim",  width=4)
    table.add_column("Document", style="bold")

    for i, source in enumerate(sources, 1):
        table.add_row(str(i), source)

    console.print()
    console.print(table)


def print_upload_progress(filename: str, n_chunks: int):
    console.print(f"  [green]✓[/green] [bold]{filename}[/bold] — {n_chunks} chunks indexed")


def print_error(message: str):
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str):
    console.print(f"[dim]{message}[/dim]")


def _print_sources(sources: list[dict]):
    if not sources:
        return

    table = Table(title="Sources", box=box.SIMPLE, border_style="dim", show_header=True)
    table.add_column("Score", style="dim",   width=7)
    table.add_column("File",  style="cyan")
    table.add_column("Page",  style="dim",   width=6)

    seen = set()
    for s in sources:
        key = (s["source"], s["page"])
        if key in seen:
            continue
        seen.add(key)
        table.add_row(str(s["score"]), s["source"], str(s["page"]))

    console.print()
    console.print(table)
