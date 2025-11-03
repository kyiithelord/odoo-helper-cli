# odoo-helper-cli

CLI tools for Odoo developers: log analysis, DB/migration helpers, performance hints, report scaffolding, and API utilities.

## Install

```bash
pipx install .
# or
pip install .
```

## Quickstart

```bash
odoo-helper --help               # show top-level help
odoo-helper logs analyze --path ./odoo.log --group --suggest
odoo-helper db ping --dsn postgresql://user:pass@localhost:5432/odoo
```

## Command reference

- **logs analyze**
  - Usage:
    ```bash
    odoo-helper logs analyze \
      --path /var/log/odoo/odoo.log \
      [--since "2025-01-01 00:00:00"] [--until "2025-01-02 00:00:00"] \
      [--group/--no-group] [--suggest/--no-suggest] [--output rich|json]
    ```
  - Notes:
    - Groups repeated tracebacks and adds Odoo-specific hints (External IDs, QWeb, DB schema, etc.).

- **db ping**
  - Usage:
    ```bash
    odoo-helper db ping --dsn postgresql://user:pass@host:5432/dbname
    ```

- **db health**
  - Usage:
    ```bash
    odoo-helper db health --dsn postgresql://user:pass@host:5432/dbname \
      --long_tx_threshold "5 minutes"
    ```
  - Shows Postgres version, active/idle sessions, long-running queries, waiting locks, and checks for `public.ir_model_data`.

- **db slow-queries**
  - Usage:
    ```bash
    odoo-helper db slow-queries --dsn postgresql://user:pass@host:5432/dbname \
      [--limit 50] [--order_by total_time|mean_time|calls]
    ```
  - Requires `pg_stat_statements` extension enabled.
    - Enable example (server config may vary):
      1) In `postgresql.conf`: `shared_preload_libraries = 'pg_stat_statements'`
      2) Restart Postgres
      3) `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;`

- **migrate plan**
  - Usage:
    ```bash
    odoo-helper migrate plan --from 14 --to 17
    ```
  - Prints a checklist of common breaking areas across the version range.

- **migrate scan**
  - Usage:
    ```bash
    odoo-helper migrate scan --path addons/my_module [--odoo_version 17]
    ```
  - Scans for `_name`/`_inherit` conflicts, manifest `depends`, and deprecated `@api.multi/v7/v8` usages.

- **report scaffold**
  - Usage:
    ```bash
    odoo-helper report scaffold --type xlsx|pdf --name report_name \
      --module my_report_module --dest ./out
    ```
  - Creates `__manifest__.py`, `report/<name>.py`, `data/report.xml`, and `views/<name>_template.xml` (for PDF).
  - XLSX uses `report_xlsx` (requires `report_xlsx` module installed).

- **api call**
  - Single request:
    ```bash
    odoo-helper api call --method POST --url https://httpbin.org/post \
      --data '{"hello":"world"}' --retry 2 --timeout 30
    ```
  - From files:
    ```bash
    odoo-helper api call --method POST --url https://httpbin.org/post \
      --headers_file headers.json --data_file body.json
    ```
  - Batch (JSON array or JSONL):
    ```bash
    # batch.json
    [
      {"method":"GET","url":"https://httpbin.org/get"},
      {"method":"POST","url":"https://httpbin.org/post","json":{"a":1}}
    ]
    odoo-helper api call --method GET --batch_file batch.json
    ```

## Examples

- Logs analyze
  - Group and suggest: `odoo-helper logs analyze --path /var/log/odoo/odoo.log --group --suggest`
  - Time window and JSON: `odoo-helper logs analyze --path ./odoo.log --since "2025-01-01 00:00:00" --output json`

- DB utils
  - Ping: `odoo-helper db ping --dsn postgresql://user:pass@localhost:5432/odoo`
  - Health: `odoo-helper db health --dsn postgresql://user:pass@localhost:5432/odoo --long_tx_threshold "2 minutes"`
  - Slow queries: `odoo-helper db slow-queries --dsn postgresql://user:pass@localhost:5432/odoo --limit 20 --order_by total_time`
    - Requires `pg_stat_statements` extension enabled.

- Migration helpers
  - Plan: `odoo-helper migrate plan --from 14 --to 17`
  - Scan module: `odoo-helper migrate scan --path addons/my_module`

- Report scaffold
  - XLSX: `odoo-helper report scaffold --type xlsx --name sales_report --module my_sales_report --dest ./out`
  - PDF: `odoo-helper report scaffold --type pdf --name partner_report --module my_partner_report --dest ./out`

- API helper
  - Single: `odoo-helper api call --method POST --url https://httpbin.org/post --data '{"hello":"world"}' --retry 2`
  - Files: `odoo-helper api call --method POST --url https://httpbin.org/post --headers_file headers.json --data_file body.json`
  - Batch (JSON list or JSONL): `odoo-helper api call --method GET --batch_file batch.json`

## Release

Build and publish (adjust credentials and repository as needed):

```bash
python -m pip install --upgrade build twine
python -m build
twine upload dist/*  # or: twine upload --repository testpypi dist/*
```

## License

MIT
