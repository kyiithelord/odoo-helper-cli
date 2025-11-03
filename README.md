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

## License

MIT
