import typer
from rich.console import Console
from pathlib import Path

app = typer.Typer()
console = Console()


@app.command("scaffold")
def scaffold(
    type: str = typer.Option(..., "--type", help="xlsx or pdf"),
    name: str = typer.Option(..., help="Report name"),
    module: str = typer.Option(..., help="Module name"),
    dest: Path = typer.Option(Path("."), help="Destination directory"),
):
    """Generate a minimal report module skeleton (placeholder)."""
    console.print(f"Scaffolding report {name} ({type}) under module {module} in {dest} (MVP placeholder)")
