import os
import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command("ping")
def ping(dsn: str = typer.Option(None, help="Postgres DSN")):
    """Quick connectivity check to Postgres."""
    try:
        import psycopg
        conn = psycopg.connect(dsn) if dsn else psycopg.connect()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            one = cur.fetchone()
        console.print(f"[green]DB OK[/green] {one}")
    except Exception as e:
        console.print(f"[red]DB error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("health")
def health(dsn: str = typer.Option(None, help="Postgres DSN")):
    """Basic sanity checks (placeholder)."""
    console.print("Running basic checks (MVP placeholder)...")


@app.command("slow-queries")
def slow_queries(
    dsn: str = typer.Option(None, help="Postgres DSN"),
    min_duration: str = typer.Option("200ms", help="Minimum duration"),
    limit: int = typer.Option(50, help="Limit results"),
):
    """Inspect pg_stat_statements (placeholder)."""
    console.print(f"Scan slow queries >= {min_duration} (MVP placeholder)... limit={limit}")
