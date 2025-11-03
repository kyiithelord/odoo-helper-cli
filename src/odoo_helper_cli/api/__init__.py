import json
import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command("call")
def call(
    method: str = typer.Option(..., help="HTTP method"),
    url: str = typer.Option(..., help="URL"),
    data: str = typer.Option(None, help="JSON payload string"),
    bearer: str = typer.Option(None, help="Bearer token"),
    retry: int = typer.Option(0, help="Retry count"),
):
    """Simple REST call (MVP placeholder)."""
    import httpx

    headers = {}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    payload = json.loads(data) if data else None

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.request(method.upper(), url, headers=headers, json=payload)
            console.print(f"Status: {resp.status_code}")
            console.print(resp.text[:2000])
    except Exception as e:
        console.print(f"[red]HTTP error:[/red] {e}")
        raise typer.Exit(code=1)
