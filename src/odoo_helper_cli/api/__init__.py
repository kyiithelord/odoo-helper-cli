import json
import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, Dict, Any, List

app = typer.Typer()
console = Console()


@app.command("call")
def call(
    method: str = typer.Option(..., help="HTTP method"),
    url: str = typer.Option(None, help="URL for single call (ignored in batch mode)"),
    data: str = typer.Option(None, help="Inline JSON payload string for single call"),
    data_file: Optional[Path] = typer.Option(None, help="Path to JSON payload file for single call"),
    headers_file: Optional[Path] = typer.Option(None, help="Path to JSON headers file"),
    bearer: str = typer.Option(None, help="Bearer token"),
    retry: int = typer.Option(0, help="Retry count on failure"),
    timeout: float = typer.Option(30.0, help="Request timeout in seconds"),
    batch_file: Optional[Path] = typer.Option(None, help="Path to JSON or JSONL file describing a list of requests"),
):
    """REST client with retries, headers/payload from files, and batch mode.

    Batch file format:
    - JSON array: [{"method":"POST","url":"...","headers":{...},"json":{...}}]
    - JSONL: one JSON object per line with the same fields as above
    """
    import httpx
    from tenacity import retry as tenacity_retry, stop_after_attempt, wait_exponential, retry_if_exception_type

    def load_json_file(p: Optional[Path]) -> Optional[Any]:
        if not p:
            return None
        text = p.read_text(encoding="utf-8")
        try:
            return json.loads(text)
        except Exception as e:
            console.print(f"[red]Failed to parse JSON file {p}: {e}")
            raise typer.Exit(code=2)

    base_headers: Dict[str, str] = load_json_file(headers_file) or {}
    if bearer:
        base_headers["Authorization"] = f"Bearer {bearer}"

    # Single call path
    if not batch_file:
        if not url:
            console.print("[red]--url is required for single call")
            raise typer.Exit(code=2)
        payload = load_json_file(data_file) if data_file else (json.loads(data) if data else None)

        @tenacity_retry(
            reraise=True,
            stop=stop_after_attempt(max(1, retry + 1)),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type(Exception),
        )
        def do_request() -> httpx.Response:
            with httpx.Client(timeout=timeout) as client:
                return client.request(method.upper(), url, headers=base_headers, json=payload)

        try:
            resp = do_request()
            console.print(f"Status: {resp.status_code}")
            ctype = resp.headers.get("content-type", "")
            if "application/json" in ctype:
                try:
                    console.print_json(data=resp.json())
                except Exception:
                    console.print(resp.text[:4000])
            else:
                console.print(resp.text[:4000])
        except Exception as e:
            console.print(f"[red]HTTP error:[/red] {e}")
            raise typer.Exit(code=1)
        return

    # Batch path
    # Accept JSON array or JSONL (per-line JSON objects)
    batch_text = batch_file.read_text(encoding="utf-8")
    try:
        # Try JSON array first
        batch_items = json.loads(batch_text)
        if not isinstance(batch_items, list):
            raise ValueError
    except Exception:
        # Try JSONL
        batch_items = []
        for line in batch_text.splitlines():
            line = line.strip()
            if not line:
                continue
            batch_items.append(json.loads(line))

    successes = 0
    failures = 0
    for item in batch_items:
        imethod = (item.get("method") or method).upper()
        iurl = item.get("url") or url
        iheaders = {**base_headers, **(item.get("headers") or {})}
        ipayload = item.get("json") if "json" in item else item.get("data")

        if not iurl:
            console.print("[yellow]Skipping item without URL")
            failures += 1
            continue

        @tenacity_retry(
            reraise=True,
            stop=stop_after_attempt(max(1, retry + 1)),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type(Exception),
        )
        def do_item() -> httpx.Response:
            with httpx.Client(timeout=timeout) as client:
                return client.request(imethod, iurl, headers=iheaders, json=ipayload)

        try:
            resp = do_item()
            console.print(f"[bold]{imethod} {iurl}[/bold] -> [green]{resp.status_code}[/green]")
            successes += 1
        except Exception as e:
            console.print(f"[bold]{imethod} {iurl}[/bold] -> [red]ERROR[/red]: {e}")
            failures += 1

    console.print(f"Done. Successes: {successes}, Failures: {failures}")
