import typer
from rich.console import Console
from pathlib import Path
import os
from textwrap import dedent

app = typer.Typer()
console = Console()


@app.command("scaffold")
def scaffold(
    type: str = typer.Option(..., "--type", help="xlsx or pdf"),
    name: str = typer.Option(..., help="Report name"),
    module: str = typer.Option(..., help="Module name"),
    dest: Path = typer.Option(Path("."), help="Destination directory"),
):
    """Generate a minimal report module skeleton for XLSX or PDF."""
    rtype = type.lower()
    if rtype not in {"xlsx", "pdf"}:
        console.print("[red]--type must be 'xlsx' or 'pdf'")
        raise typer.Exit(code=2)

    base = dest / module
    paths = {
        "module": base,
        "report_py": base / "report" / f"{name}.py",
        "report_init": base / "report" / "__init__.py",
        "manifest": base / "__manifest__.py",
        "module_init": base / "__init__.py",
        "data_xml": base / "data" / "report.xml",
        "views_xml": base / "views" / f"{name}_template.xml",
        "static": base / "static",
    }

    # Create directories
    for key, p in paths.items():
        if key in {"module", "static"}:
            p.mkdir(parents=True, exist_ok=True)
    (base / "report").mkdir(parents=True, exist_ok=True)
    (base / "data").mkdir(parents=True, exist_ok=True)
    (base / "views").mkdir(parents=True, exist_ok=True)

    # __init__ files
    if not paths["module_init"].exists():
        paths["module_init"].write_text("from . import report\n", encoding="utf-8")
    if not paths["report_init"].exists():
        paths["report_init"].write_text("\n", encoding="utf-8")

    # Manifest
    dep = "report_xlsx" if rtype == "xlsx" else "base"
    manifest = dedent(f"""
    {{
        'name': '{module}: {name}',
        'version': '16.0.1.0.0',
        'summary': 'Auto-generated {rtype.upper()} report {name}',
        'depends': ['{dep}'],
        'data': [
            'data/report.xml',
            'views/{name}_template.xml',
        ],
        'installable': True,
        'license': 'LGPL-3',
        'application': False,
    }}
    """)
    paths["manifest"].write_text(manifest, encoding="utf-8")

    # Report python
    if rtype == "xlsx":
        report_py = dedent(f"""
        from odoo import models

        class {name.title().replace('_','')}Xlsx(models.AbstractModel):
            _name = 'report.{module}.{name}_xlsx'
            _inherit = 'report.report_xlsx.abstract'

            def generate_xlsx_report(self, workbook, data, objects):
                sheet = workbook.add_worksheet('Report')
                sheet.write(0, 0, 'Hello from {name} XLSX')
        """)
    else:
        report_py = dedent(f"""
        from odoo import models, api

        class {name.title().replace('_','')}Pdf(models.AbstractModel):
            _name = 'report.{module}.{name}_pdf'

            @api.model
            def _get_report_values(self, docids, data=None):
                return {{'doc_ids': docids, 'doc_model': 'res.partner', 'data': data or {{}}}}
        """)
    paths["report_py"].write_text(report_py, encoding="utf-8")

    # XMLs
    if rtype == "xlsx":
        data_xml = dedent(f"""
        <odoo>
          <report id="{name}_xlsx"
                  model="res.partner"
                  string="{name} XLSX"
                  report_type="xlsx"
                  name="{module}.{name}_xlsx"
                  file="{name}_xlsx"
                  print_report_name="'{name}_xlsx'"/>
        </odoo>
        """)
        template_xml = dedent(f"""
        <odoo>
          <!-- XLSX uses Python generator; no QWeb template required -->
        </odoo>
        """)
    else:
        data_xml = dedent(f"""
        <odoo>
          <report id="{name}_pdf"
                  model="res.partner"
                  string="{name} PDF"
                  report_type="qweb-pdf"
                  name="{module}.{name}_pdf"
                  file="{name}_pdf"
                  print_report_name="'{name}_pdf'"/>
        </odoo>
        """)
        template_xml = dedent(f"""
        <odoo>
          <template id="{name}_template">
            <t t-name="{module}.{name}_pdf">
              <t t-foreach="docs" t-as="d">
                <div>Hello from {name} PDF for <t t-esc="d.display_name"/></div>
              </t>
            </t>
          </template>
        </odoo>
        """)

    paths["data_xml"].write_text(data_xml.strip() + "\n", encoding="utf-8")
    paths["views_xml"].write_text(template_xml.strip() + "\n", encoding="utf-8")

    console.print(f"[green]Scaffolded[/green] {rtype.upper()} report module at {base}")
