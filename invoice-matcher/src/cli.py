import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def load_config():
    config_path = Path('config.yaml')
    if not config_path.exists():
        console.print("[red]Error: config.yaml not found[/red]")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@click.group()
def cli():
    """QuickBooks Invoice Finder — fetch transactions and find matching invoices."""
    pass


@cli.command(name='web-auth')
def web_auth():
    """Import a QuickBooks web session from a 'Copy as cURL' string.

    Capture the getTransactions request in Chrome DevTools on
    qbo.intuit.com/app/banking, 'Copy as cURL (bash)', and either:
      - pipe via stdin:  pbpaste | python3 -m src.cli web-auth
      - or paste at the prompt
    """
    from .qbo_web_client import parse_curl_to_session, SESSION_FILE

    console.print("[blue]Paste the cURL (from 'Copy as cURL' on the getTransactions request),[/blue]")
    console.print("[blue]then a blank line (press Enter twice) to finish:[/blue]\n")

    lines = []
    if not sys.stdin.isatty():
        for line in sys.stdin:
            lines.append(line)
            if not line.strip():
                break
    else:
        while True:
            try:
                line = input()
            except EOFError:
                break
            if not line.strip():
                if lines:
                    break
                continue
            lines.append(line)

    curl_text = ''.join(lines)
    if not curl_text.strip():
        console.print("[red]No input received.[/red]")
        sys.exit(1)

    session = parse_curl_to_session(curl_text)
    if not session.get('realm_id') or not session.get('cookies'):
        console.print("[red]Could not parse realm_id or cookies from the cURL.[/red]")
        console.print("[dim]Make sure you copied the getTransactions request.[/dim]")
        sys.exit(1)

    import os
    os.makedirs('credentials', exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        import json
        json.dump(session, f, indent=2)

    console.print(f"[green]✓ Saved web session[/green]")
    console.print(f"  Realm: {session['realm_id']}")
    console.print(f"  User:  {session.get('user_id')}")
    console.print(f"  Cookies: {len(session['cookies'])}")
    console.print(f"  File:  {SESSION_FILE}")
    console.print(f"\n[green]✓ Next:[/green] python3 -m src.cli fetch-transactions")


@cli.command(name='web-test')
def web_test():
    """Test the QuickBooks web session by fetching current For Review count."""
    from .qbo_web_client import QBOWebClient
    config = load_config()
    try:
        client = QBOWebClient(config.get('quickbooks') or {})
        client.authenticate()
        txns = client.fetch_all_for_review()
        console.print(f"[green]✓ Web session works — {len(txns)} 'For Review' transactions[/green]")
        for t in txns[:10]:
            console.print(f"  {t.date}  £{t.amount:>8}  {t.payee_name[:30]}")
    except Exception as e:
        console.print(f"[red]Web session test failed: {e}[/red]")
        console.print("[dim]Re-run `python3 -m src.cli web-auth` with a fresh cURL.[/dim]")
        sys.exit(1)


@cli.command(name='fetch-transactions')
def fetch_transactions():
    """Fetch unreconciled 'For Review' transactions from QuickBooks (web session)."""
    from .qbo_web_client import QBOWebClient
    config = load_config()

    console.print("[blue]Fetching 'For Review' transactions via QBO web session...[/blue]")

    try:
        client = QBOWebClient(config.get('quickbooks') or {})
        client.authenticate()
        transactions = client.fetch_all_for_review()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Web session failed: {e}[/red]")
        console.print("[dim]Re-run `python3 -m src.cli web-auth` with a fresh cURL.[/dim]")
        sys.exit(1)

    console.print(f"[green]✓ Fetched {len(transactions)} transactions[/green]")

    if transactions:
        table = Table(title="Unreconciled Transactions (For Review)")
        table.add_column("Date", style="cyan")
        table.add_column("Amount", style="magenta")
        table.add_column("Payee", style="green")
        table.add_column("Memo", style="dim")

        for txn in transactions[:20]:
            table.add_row(
                str(txn.date),
                f"£{txn.amount:.2f}",
                txn.payee_name[:40] if txn.payee_name else "(none)",
                txn.memo[:60] if txn.memo else "",
            )

        console.print(table)

        if len(transactions) > 20:
            console.print(f"[dim]... and {len(transactions) - 20} more[/dim]")

    return transactions


if __name__ == '__main__':
    cli()
