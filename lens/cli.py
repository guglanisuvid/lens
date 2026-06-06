"""Interactive REPL for Lens — enter `lens` to start."""
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

console = Console()

HELP_TEXT = """
[bold cyan]Lens[/bold cyan] — task-based document intelligence

[bold]Commands:[/bold]
  [green]/upload[/green] [dim]<path>[/dim]      Index a PDF/txt file or folder
  [green]/ask[/green] [dim]<question>[/dim]     Ask a question against indexed docs
  [green]/task[/green] [dim]<description>[/dim] Run a structured task across docs
  [green]/docs[/green]               List all indexed documents
  [green]/remove[/green] [dim]<name>[/dim]      Remove a document from the index
  [green]/clear[/green]              Wipe the entire index
  [green]/help[/green]               Show this help
  [green]/exit[/green]               Exit Lens

[dim]Tip: type /ask what is the refund policy? — no quotes needed[/dim]
"""


def _check_ollama():
    from lens.embedder import check_ollama
    if not check_ollama():
        console.print("[bold red]Ollama is not running or nomic-embed-text is not installed.[/bold red]")
        console.print("  Run: [bold]ollama pull nomic-embed-text[/bold]")
        return False
    return True


def _cmd_upload(args: list[str]):
    if not args:
        console.print("[yellow]Usage: /upload <path>[/yellow]")
        return
    if not _check_ollama():
        return

    from lens.parser import parse_file
    from lens.embedder import embed_chunks
    from lens.indexer import add_chunks, list_sources, source_exists
    from lens.formatter import print_upload_progress, print_error

    path = args[0]
    if os.path.isdir(path):
        files = [
            os.path.join(root, f)
            for root, _, filenames in os.walk(path)
            for f in filenames
            if f.lower().endswith((".pdf", ".txt"))
        ]
    elif os.path.isfile(path):
        files = [path]
    else:
        console.print(f"[red]Path not found:[/red] {path}")
        return

    if not files:
        console.print("[yellow]No .pdf or .txt files found.[/yellow]")
        return

    console.print(f"\n[bold blue]Indexing {len(files)} file(s)...[/bold blue]\n")

    for file in files:
        source_path = os.path.abspath(file)
        if source_exists(source_path):
            console.print(f"  [yellow]↷[/yellow] [dim]{os.path.basename(file)} — already indexed, skipping[/dim]")
            continue

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            progress.add_task(f"Processing {os.path.basename(file)}...")
            try:
                chunks = parse_file(file)
                texts = [c["text"] for c in chunks]
                embeddings = embed_chunks(texts)
                add_chunks(chunks, embeddings)
                print_upload_progress(os.path.basename(file), len(chunks))
            except Exception as e:
                console.print(f"[red]Error:[/red] {os.path.basename(file)}: {e}")

    console.print(f"\n[dim]Total indexed documents: {len(list_sources())}[/dim]\n")


def _cmd_ask(args: list[str]):
    if not args:
        console.print("[yellow]Usage: /ask <question>[/yellow]")
        return
    if not _check_ollama():
        return

    from lens.task import ask_question
    from lens.formatter import print_answer

    question = args[0]
    console.print(f"\n[bold green]Question:[/bold green] {question}\n")

    with Progress(SpinnerColumn(), TextColumn("Searching..."), transient=True) as progress:
        progress.add_task("")
        try:
            result = ask_question(question)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return

    print_answer(result["answer"], result["sources"])


def _cmd_task(args: list[str]):
    if not args:
        console.print("[yellow]Usage: /task <description>[/yellow]")
        return
    if not _check_ollama():
        return

    from lens.task import run_task
    from lens.formatter import print_output

    description = args[0]
    console.print(f"\n[bold blue]Task:[/bold blue] {description}\n")

    with Progress(SpinnerColumn(), TextColumn("Thinking..."), transient=True) as progress:
        progress.add_task("")
        try:
            result = run_task(description)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return

    print_output(result["output"], result["sources"])


def _cmd_docs(_args: list[str]):
    from lens.indexer import list_sources
    from lens.formatter import print_sources_list
    print_sources_list(list_sources())


def _cmd_remove(args: list[str]):
    if not args:
        console.print("[yellow]Usage: /remove <filename or partial path>[/yellow]")
        return

    from lens.indexer import list_sources, remove_source

    query = args[0].lower()
    all_sources = list_sources()
    matches = [s for s in all_sources if query in s.lower()]

    if not matches:
        console.print(f"[yellow]No indexed document matches:[/yellow] {args[0]}")
        return

    if len(matches) > 1:
        console.print(f"[yellow]Multiple matches — be more specific:[/yellow]")
        for m in matches:
            console.print(f"  [dim]{m}[/dim]")
        return

    source = matches[0]
    console.print(f"Remove [bold]{os.path.basename(source)}[/bold] from index?")
    confirm = console.input("[bold]Type 'yes' to confirm:[/bold] ").strip().lower()
    if confirm == "yes":
        removed = remove_source(source)
        console.print(f"[green]Removed[/green] {os.path.basename(source)} — {removed} chunks deleted")
    else:
        console.print("[dim]Cancelled.[/dim]")


def _cmd_clear(_args: list[str]):
    from lens.indexer import list_sources, clear_index
    sources = list_sources()
    if not sources:
        console.print("[dim]Index is already empty.[/dim]")
        return

    console.print(f"[yellow]This will delete {len(sources)} indexed document(s).[/yellow]")
    confirm = console.input("[bold]Type 'yes' to confirm:[/bold] ").strip().lower()
    if confirm == "yes":
        clear_index()
        console.print("[bold red]Index cleared.[/bold red]")
    else:
        console.print("[dim]Cancelled.[/dim]")


COMMANDS = {
    "/upload": _cmd_upload,
    "/ask":    _cmd_ask,
    "/task":   _cmd_task,
    "/docs":   _cmd_docs,
    "/remove": _cmd_remove,
    "/clear":  _cmd_clear,
}


def run_repl():
    console.print(HELP_TEXT)

    while True:
        try:
            raw = console.input("[bold cyan]lens>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye.[/dim]")
            break

        if not raw:
            continue

        if raw in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Bye.[/dim]")
            break

        if raw in ("/help", "help"):
            console.print(HELP_TEXT)
            continue

        parts = raw.split(None, 1)
        cmd = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""
        args = [remainder] if remainder else []

        if cmd not in COMMANDS:
            console.print(f"[yellow]Unknown command:[/yellow] {cmd}  (type [bold]/help[/bold] for commands)")
            continue

        COMMANDS[cmd](args)
