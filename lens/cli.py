import os
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app     = typer.Typer(help="Lens — task-based document intelligence.")
console = Console()


def _check_ollama():
    from lens.embedder import check_ollama
    if not check_ollama():
        console.print("[bold red]Ollama is not running or nomic-embed-text is not installed.[/bold red]")
        console.print("Run: [bold]ollama pull nomic-embed-text[/bold]")
        raise typer.Exit(1)


@app.command()
def upload(path: str = typer.Argument(..., help="PDF/txt file or folder to index")):
    """Parse and embed documents into the local index."""
    from lens.parser    import parse_file
    from lens.embedder  import embed_chunks
    from lens.indexer   import add_chunks, list_sources
    from lens.formatter import print_upload_progress, print_error

    _check_ollama()

    # Collect files
    if os.path.isdir(path):
        files = [
            os.path.join(path, f) for f in os.listdir(path)
            if f.lower().endswith((".pdf", ".txt"))
        ]
    elif os.path.isfile(path):
        files = [path]
    else:
        print_error(f"Path not found: {path}")
        raise typer.Exit(1)

    if not files:
        print_error("No .pdf or .txt files found.")
        raise typer.Exit(1)

    console.print(f"\n[bold blue]Indexing {len(files)} file(s)...[/bold blue]\n")

    for file in files:
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            progress.add_task(f"Processing {os.path.basename(file)}...")
            try:
                chunks     = parse_file(file)
                texts      = [c["text"] for c in chunks]
                embeddings = embed_chunks(texts)
                add_chunks(chunks, embeddings)
                print_upload_progress(os.path.basename(file), len(chunks))
            except Exception as e:
                print_error(f"{os.path.basename(file)}: {e}")

    console.print(f"\n[dim]Total indexed documents: {len(list_sources())}[/dim]")


@app.command()
def task(description: str = typer.Argument(..., help="Task to run against indexed documents")):
    """Run a task across all indexed documents and return structured output."""
    from lens.task      import run_task
    from lens.formatter import print_output, print_error

    _check_ollama()

    console.print(f"\n[bold blue]Task:[/bold blue] {description}\n")

    with Progress(SpinnerColumn(), TextColumn("Thinking..."), transient=True) as progress:
        progress.add_task("")
        try:
            result = run_task(description)
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

    print_output(result["output"], result["sources"])


@app.command()
def ask(question: str = typer.Argument(..., help="Question to ask against indexed documents")):
    """Ask a question and get a cited answer."""
    from lens.task      import ask_question
    from lens.formatter import print_answer, print_error

    _check_ollama()

    console.print(f"\n[bold green]Question:[/bold green] {question}\n")

    with Progress(SpinnerColumn(), TextColumn("Searching..."), transient=True) as progress:
        progress.add_task("")
        try:
            result = ask_question(question)
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

    print_answer(result["answer"], result["sources"])


@app.command(name="list")
def list_docs():
    """List all indexed documents."""
    from lens.indexer   import list_sources
    from lens.formatter import print_sources_list
    print_sources_list(list_sources())


@app.command()
def clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Wipe the entire document index."""
    from lens.indexer import clear_index

    if not confirm:
        typer.confirm("This will delete all indexed documents. Continue?", abort=True)

    clear_index()
    console.print("[bold red]Index cleared.[/bold red]")
