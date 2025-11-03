import typer
from rich.console import Console
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import re

app = typer.Typer()
console = Console()


@app.command("analyze")
def analyze(
    path: Path = typer.Option(..., exists=True, readable=True, help="Path to odoo.log"),
    since: str = typer.Option(None, help="Start time (e.g., '2025-01-01 00:00:00')"),
    until: str = typer.Option(None, help="End time"),
    group: bool = typer.Option(True, help="Group repeated tracebacks"),
    suggest: bool = typer.Option(True, help="Show Odoo-specific hints"),
    output: str = typer.Option("rich", help="Output format: rich|json"),
):
    """Analyze Odoo server logs and surface errors with actionable hints."""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        console.print(f"[red]Failed to read log: {e}")
        raise typer.Exit(code=1)

    ts_re = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d{3})?)")
    def parse_ts(line: str) -> Optional[datetime]:
        m = ts_re.match(line)
        if not m:
            return None
        raw = m.group("ts").replace(",", ".")
        fmts = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"]
        for f in fmts:
            try:
                return datetime.strptime(raw, f)
            except Exception:
                continue
        return None

    def parse_user_ts(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, f)
            except Exception:
                continue
        return None

    since_dt = parse_user_ts(since)
    until_dt = parse_user_ts(until)

    # Collect traceback blocks with metadata
    blocks: List[Dict] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if "Traceback (most recent call last):" in line:
            # Backtrack to nearest timestamp for this block
            ts = None
            for j in range(i, max(-1, i - 5), -1):
                ts = parse_ts(lines[j]) or ts
                if ts:
                    break
            block = [line]
            i += 1
            while i < n:
                block.append(lines[i])
                # Stop if we hit a new timestamped log line (likely next record)
                if ts_re.match(lines[i]) and i != len(block) - 1:
                    block.pop()  # don't include the next record header
                    break
                # Heuristic end: blank line separating records
                if lines[i].strip() == "" and len(block) > 1:
                    break
                i += 1
            # Extract exception line (usually the last non-empty line)
            exc_line = next((l for l in reversed(block) if l.strip()), "")
            m = re.match(r"^(?P<exc>[A-Za-z_][\w.]*)(?::\s*(?P<msg>.*))?", exc_line.strip())
            exc = m.group("exc") if m else "UnknownException"
            msg = (m.group("msg") or "").strip() if m else exc_line.strip()

            # Time filter
            if since_dt or until_dt:
                ts_ok = True
                if since_dt and (not ts or ts < since_dt):
                    ts_ok = False
                if until_dt and (not ts or ts > until_dt):
                    ts_ok = False
                if not ts_ok:
                    i += 1
                    continue

            blocks.append({
                "timestamp": ts.isoformat() if ts else None,
                "exception": exc,
                "message": msg,
                "snippet": "\n".join(block[-20:]),
            })
        else:
            i += 1

    # Grouping
    if group:
        groups: Dict[str, Dict] = {}
        for b in blocks:
            key = f"{b['exception']}|{(b['message'] or '')[:120]}"
            g = groups.setdefault(key, {
                "exception": b["exception"],
                "message": b["message"],
                "count": 0,
                "first_ts": b["timestamp"],
                "examples": [],
            })
            g["count"] += 1
            if not g["first_ts"] and b["timestamp"]:
                g["first_ts"] = b["timestamp"]
            if len(g["examples"]) < 3:
                g["examples"].append(b["snippet"])

        results = list(groups.values())
    else:
        results = [{
            "exception": b["exception"],
            "message": b["message"],
            "timestamp": b["timestamp"],
            "snippet": b["snippet"],
            "count": 1,
        } for b in blocks]

    # Hints
    hint_rules = [
        (re.compile(r"External ID|xmlid|No matching record found for external id", re.I),
         "External ID not found. Check ir.model.data, data XML load order, and module dependency sequence."),
        (re.compile(r"duplicate key value violates unique constraint|UniqueViolation", re.I),
         "Unique constraint violation. Identify offending records; consider cleanup SQL and ensure data XML doesn't insert duplicates."),
        (re.compile(r"psycopg\..*OperationalError|could not connect to server|connection refused", re.I),
         "Database connectivity issue. Verify DSN, service availability, and locks during migrations."),
        (re.compile(r"QWebException|Could not render|view architecture.*error|XPath|has no field", re.I),
         "View/QWeb error. Inspect the mentioned XML/view, ensure fields exist and XPath targets match after updates."),
        (re.compile(r"KeyError: '.*' in.*ir\.ui\.view|render", re.I),
         "Template key error. Check context variables and t-foreach/t-as names in QWeb."),
        (re.compile(r"cache miss|missing dependency|_inherit.*not found", re.I),
         "Model inheritance conflict. Ensure module dependencies and load order; verify _name vs _inherit correctness."),
        (re.compile(r'relation ".*" does not exist|column ".*" does not exist', re.I),
         "Broken DB schema after update. Run -u for impacted modules and validate migrations/ORM field definitions."),
    ]

    def mk_hints(text: str) -> List[str]:
        out = []
        for rx, hint in hint_rules:
            if rx.search(text or ""):
                out.append(hint)
        return out

    if suggest:
        for r in results:
            joined = f"{r.get('exception','')} {r.get('message','')}\n{''.join(r.get('examples', []))}"
            r["hints"] = mk_hints(joined)

    # Output
    if output == "json":
        console.print_json(data=results)
        return

    # Rich output
    if not results:
        console.print("[green]No tracebacks found in the selected range.")
        return

    from rich.table import Table
    table = Table(title="Tracebacks")
    table.add_column("Count", justify="right")
    table.add_column("Exception")
    table.add_column("Message", overflow="fold")
    table.add_column("First Seen", no_wrap=True)
    table.add_column("Hints", overflow="fold")

    for r in sorted(results, key=lambda x: x.get("count", 1), reverse=True):
        hints = "\n- " + "\n- ".join(r.get("hints", [])) if r.get("hints") else ""
        table.add_row(
            str(r.get("count", 1)),
            r.get("exception", ""),
            (r.get("message") or "").strip()[:200],
            (r.get("first_ts") or r.get("timestamp") or "")[:23],
            hints.strip(),
        )
    console.print(table)
