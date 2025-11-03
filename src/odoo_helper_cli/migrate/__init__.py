import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command("plan")
def plan(frm: int = typer.Option(..., "--from"), to: int = typer.Option(..., "--to")):
    """Generate migration checklist (placeholder)."""
    console.print(f"Migration plan from Odoo {frm} -> {to} (MVP placeholder)")


@app.command("scan")
def scan(path: str = typer.Option(..., help="Module directory"), odoo_version: int = typer.Option(None, help="Target Odoo version")):
    """Static scan for _inherit/_name conflicts and depends issues (placeholder)."""
    console.print(f"Scanning {path} for common issues (MVP placeholder)")
