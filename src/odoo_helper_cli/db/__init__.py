import os
import typer
from rich.console import Console
from typing import Optional

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
def health(
    dsn: str = typer.Option(None, help="Postgres DSN"),
    long_tx_threshold: str = typer.Option("5 minutes", help="Report transactions running longer than this interval"),
):
    """Run basic DB health checks: version, active/idle sessions, long-running queries, locks, Odoo table presence."""
    try:
        import psycopg
        from rich.table import Table
        conn = psycopg.connect(dsn) if dsn else psycopg.connect()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]

            cur.execute("""
                SELECT
                  sum((state = 'active')::int) AS active,
                  sum((state = 'idle')::int)   AS idle,
                  count(*)                      AS total
                FROM pg_stat_activity
                WHERE pid <> pg_backend_pid();
            """)
            active, idle, total = cur.fetchone()

            cur.execute(
                """
                SELECT pid, now() - query_start AS duration, coalesce(left(query, 140), '')
                FROM pg_stat_activity
                WHERE state = 'active' AND now() - query_start > %s::interval
                ORDER BY duration DESC
                LIMIT 10
                """,
                (long_tx_threshold,),
            )
            long_running = cur.fetchall()

            cur.execute("SELECT count(*) FROM pg_locks WHERE NOT granted;")
            waiting_locks = cur.fetchone()[0]

            # Odoo table presence
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'ir_model_data'
                )
                """
            )
            has_imd = cur.fetchone()[0]

        console.print(f"[bold]Postgres[/bold]: {version}")

        table = Table(title="Sessions")
        table.add_column("Active", justify="right")
        table.add_column("Idle", justify="right")
        table.add_column("Total", justify="right")
        table.add_row(str(active or 0), str(idle or 0), str(total or 0))
        console.print(table)

        if waiting_locks:
            console.print(f"[yellow]Waiting locks:[/yellow] {waiting_locks}")
        else:
            console.print("[green]No waiting locks detected.")

        if long_running:
            lr = Table(title="Long running queries (> " + long_tx_threshold + ")")
            lr.add_column("pid", justify="right")
            lr.add_column("duration")
            lr.add_column("query", overflow="fold")
            for pid, duration, query in long_running:
                lr.add_row(str(pid), str(duration), query)
            console.print(lr)
        else:
            console.print("[green]No long running queries.")

        if has_imd:
            console.print("[green]Odoo table detected:[/green] public.ir_model_data")
        else:
            console.print("[yellow]public.ir_model_data not found. This may not be an Odoo DB or schema is not 'public'.")

    except Exception as e:
        console.print(f"[red]Health check error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("slow-queries")
def slow_queries(
    dsn: str = typer.Option(None, help="Postgres DSN"),
    limit: int = typer.Option(50, help="Limit results"),
    order_by: str = typer.Option("total_time", help="Order by one of total_time, mean_time, calls"),
):
    """List top queries from pg_stat_statements if available."""
    valid_order = {"total_time", "mean_time", "calls"}
    if order_by not in valid_order:
        console.print(f"[yellow]Invalid order_by. Using total_time")
        order_by = "total_time"

    try:
        import psycopg
        from rich.table import Table
        conn = psycopg.connect(dsn) if dsn else psycopg.connect()
        conn.autocommit = True
        with conn.cursor() as cur:
            # Check extension
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements'")
            if not cur.fetchone():
                console.print("[yellow]pg_stat_statements is not enabled. Enable it to use this command.")
                raise typer.Exit(code=1)

            # Columns differ across versions; fetch columns present
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pg_stat_statements'")
            cols = {r[0] for r in cur.fetchall()}
            mean_col = 'mean_time' if 'mean_time' in cols else None

            if mean_col:
                cur.execute(
                    f"""
                    SELECT query, calls, total_time, {mean_col}
                    FROM pg_stat_statements
                    ORDER BY {order_by} DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                table = Table(title="Top queries (pg_stat_statements)")
                table.add_column("calls", justify="right")
                table.add_column("total_time ms", justify="right")
                table.add_column("mean_time ms", justify="right")
                table.add_column("query", overflow="fold")
                for q, calls, total_time, mean_time in rows:
                    table.add_row(str(calls), f"{total_time:.2f}", f"{mean_time:.2f}", (q or "")[:2000])
                console.print(table)
            else:
                # Older versions: compute mean on the fly
                cur.execute(
                    """
                    SELECT query, calls, total_time, CASE WHEN calls>0 THEN total_time/calls ELSE 0 END AS mean_time
                    FROM pg_stat_statements
                    ORDER BY total_time DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                table = Table(title="Top queries (pg_stat_statements)")
                table.add_column("calls", justify="right")
                table.add_column("total_time ms", justify="right")
                table.add_column("mean_time ms", justify="right")
                table.add_column("query", overflow="fold")
                for q, calls, total_time, mean_time in rows:
                    table.add_row(str(calls), f"{total_time:.2f}", f"{mean_time:.2f}", (q or "")[:2000])
                console.print(table)
    except Exception as e:
        console.print(f"[red]slow-queries error:[/red] {e}")
        raise typer.Exit(code=1)
