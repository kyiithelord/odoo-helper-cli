from typing import Optional
import typer
from rich.console import Console
from . import __version__

from .logs import app as logs_app
from .db import app as db_app
from .migrate import app as migrate_app
from .report import app as report_app
from .api import app as api_app

console = Console()
app = typer.Typer(help="Odoo Helper CLI")

app.add_typer(logs_app, name="logs", help="Log analysis tools")
app.add_typer(db_app, name="db", help="Database utilities")
app.add_typer(migrate_app, name="migrate", help="Migration helpers")
app.add_typer(report_app, name="report", help="Report scaffolding")
app.add_typer(api_app, name="api", help="API helpers")


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", help="Show version and exit", callback=None, is_eager=True
    ),
):
    """Top-level callback; prints version when requested."""
    if version:
        console.print(f"odoo-helper-cli {__version__}")
        raise typer.Exit()
