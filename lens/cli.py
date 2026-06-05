import typer
from rich.console import Console

app = typer.Typer(help="Lens — task-based document intelligence.")
console = Console()


@app.command()
def upload(path: str = typer.Argument(..., help="File or folder to index")):
    """Parse and embed documents into the local index."""
    console.print(f"[bold blue]Uploading:[/bold blue] {path}")
    # TODO: implement


@app.command()
def task(description: str = typer.Argument(..., help="Task to run against indexed documents")):
    """Run a task across all indexed documents and return structured output."""
    console.print(f"[bold blue]Running task:[/bold blue] {description}")
    # TODO: implement


@app.command()
def ask(question: str = typer.Argument(..., help="Question to ask against indexed documents")):
    """Ask a single question and get a cited answer."""
    console.print(f"[bold blue]Asking:[/bold blue] {question}")
    # TODO: implement


@app.command()
def list():
    """List all indexed documents."""
    console.print("[bold blue]Indexed documents:[/bold blue]")
    # TODO: implement


@app.command()
def clear():
    """Wipe the entire document index."""
    console.print("[bold red]Clearing index...[/bold red]")
    # TODO: implement
