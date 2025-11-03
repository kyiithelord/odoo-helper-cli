import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import re
import ast
from typing import Dict, List, Optional

app = typer.Typer()
console = Console()


@app.command("plan")
def plan(frm: int = typer.Option(..., "--from"), to: int = typer.Option(..., "--to")):
    """Generate a migration checklist with common breaking areas between versions."""
    items_by_version = {
        (14, 15): [
            "Python 3.8 baseline, review deprecated APIs in mail, website.",
            "ORM: check compute/store fields definitions; onchange API cleanup.",
            "JS/QWeb: Owl adoption starts; legacy widgets may break.",
        ],
        (15, 16): [
            "Discussed mail/thread refactors; check chatter overrides.",
            "Accounting changes; report templates adjustments.",
            "New assets pipeline; verify web/assets bundle names.",
        ],
        (16, 17): [
            "Owl v2 widespread; legacy qweb widgets removal.",
            "HTTP controllers typing; check request.params usages.",
            "Models cleanup: deprecated fields/APIs removed.",
        ],
    }
    table = Table(title=f"Migration Checklist {frm} → {to}")
    table.add_column("Area")
    table.add_column("Notes", overflow="fold")

    for (f, t), notes in items_by_version.items():
        if frm <= f and to >= t:
            table.add_row(f"{f} → {t}", "\n".join(f"- {n}" for n in notes))

    if len(table.rows) == 0:
        console.print("[yellow]No predefined notes for this version range. Use --from/--to within 14–17.")
    else:
        console.print(table)


@app.command("scan")
def scan(
    path: Path = typer.Option(..., exists=True, file_okay=False, help="Module directory"),
    odoo_version: Optional[int] = typer.Option(None, help="Target Odoo version"),
):
    """Static scan for _inherit/_name conflicts, manifest depends, and deprecated patterns."""
    root = Path(path)
    issues: List[str] = []

    # Manifest parsing
    manifest_file = None
    for cand in (root / "__manifest__.py", root / "__openerp__.py"):
        if cand.exists():
            manifest_file = cand
            break
    depends: List[str] = []
    name = root.name
    if manifest_file:
        try:
            data = manifest_file.read_text(encoding="utf-8")
            obj = ast.literal_eval(compile(data, str(manifest_file), 'eval'))
            depends = list(obj.get('depends', [])) if isinstance(obj, dict) else []
        except Exception as e:
            issues.append(f"Failed to parse manifest: {manifest_file.name}: {e}")
    else:
        issues.append("Manifest file not found (__manifest__.py).")

    # Python model scan
    model_defs: Dict[str, Dict] = {}
    for py in root.rglob("*.py"):
        try:
            code = py.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            tree = ast.parse(code)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # look for assignments _name/_inherit
                _name = None
                _inherit = None
                for assign in [n for n in node.body if isinstance(n, ast.Assign)]:
                    for t in assign.targets:
                        if isinstance(t, ast.Name) and t.id in {"_name", "_inherit"}:
                            try:
                                val = ast.literal_eval(assign.value)
                            except Exception:
                                val = None
                            if t.id == "_name":
                                _name = val
                            else:
                                _inherit = val
                if _name or _inherit:
                    model_defs[node.name] = {"_name": _name, "_inherit": _inherit, "file": str(py.relative_to(root))}

    # Analyze model conflicts
    for cls, d in model_defs.items():
        if d["_name"] and d["_inherit"]:
            issues.append(f"Class {cls} defines both _name ({d['_name']}) and _inherit ({d['_inherit']}). Ensure this is intended (new model vs extension).")
        if not d["_name"] and not d["_inherit"]:
            issues.append(f"Class {cls} in {d['file']} lacks _name/_inherit; if it's a model, define one.")

    # Simple deprecated patterns
    deprecated_rx = [
        re.compile(r"@api\.(multi)\b"),
        re.compile(r"@api\.(v7|v8)\b"),
    ]
    for py in root.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        for rx in deprecated_rx:
            if rx.search(text):
                issues.append(f"Deprecated API usage in {py.relative_to(root)}: pattern {rx.pattern}")

    # Output report
    console.print(f"Scanning module: [bold]{name}[/bold]")
    table = Table(title="Findings")
    table.add_column("Type")
    table.add_column("Detail", overflow="fold")

    if depends:
        table.add_row("depends", ", ".join(depends))
    else:
        table.add_row("depends", "(none)")

    if issues:
        for it in issues:
            table.add_row("issue", it)
    else:
        table.add_row("info", "No obvious issues found.")

    if odoo_version:
        table.add_row("target", f"Odoo {odoo_version}")

    console.print(table)
