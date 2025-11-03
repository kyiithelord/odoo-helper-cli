# odoo-helper-cli

CLI tools for Odoo developers: log analysis, DB/migration helpers, performance hints, report scaffolding, and API utilities.

## Install

```bash
pipx install .
# or
pip install .
```

## Usage

```bash
odoo-helper --help
odoo-helper logs analyze --path ./odoo.log --group --suggest
odoo-helper db ping --dsn postgresql://user:pass@localhost:5432/odoo
```

## Commands

- logs analyze
- db ping | health | slow-queries
- migrate plan | scan
- report scaffold
- api call

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
