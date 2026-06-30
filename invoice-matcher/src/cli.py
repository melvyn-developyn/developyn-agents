import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from .database import Database
from .gmail_searcher import GmailSearcher
from .matcher import Matcher
from .models import Invoice, Match
from .pdf_parser import PDFParser
from .quickbooks_client import QuickBooksClient
from .reconciler import Reconciler

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
    """Invoice to Bank Transaction Matcher"""
    pass


@cli.command()
def init():
    """Initialize the database"""
    config = load_config()
    db = Database(config['database']['path'])
    console.print("[green]✓ Database initialized[/green]")
    db.close()


@cli.command()
def qb_auth():
    """Authenticate with QuickBooks via OAuth2"""
    from .qb_auth import authenticate_quickbooks
    success = authenticate_quickbooks()
    if not success:
        sys.exit(1)


@cli.command(name='web-auth')
def web_auth():
    """Import a QuickBooks web session from a 'Copy as cURL' string.

    Capture the getTransactions request in Chrome DevTools on
    qbo.intuit.com/app/banking, 'Copy as cURL (bash)', and either:
      - pipe via stdin:  pbpaste | python3 -m src.cli web-auth
      - or paste at the prompt
    """
    import sys as _sys
    from .qbo_web_client import parse_curl_to_session, SESSION_FILE
    import os

    console.print("[blue]Paste the cURL (from 'Copy as cURL' on the getTransactions request),[/blue]")
    console.print("[blue]then a blank line (press Enter twice) to finish:[/blue]\n")

    lines = []
    if not _sys.stdin.isatty():
        for line in _sys.stdin:
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
        _sys.exit(1)

    session = parse_curl_to_session(curl_text)
    if not session.get('realm_id') or not session.get('cookies'):
        console.print("[red]Could not parse realm_id or cookies from the cURL.[/red]")
        console.print("[dim]Make sure you copied the getTransactions request.[/dim]")
        _sys.exit(1)

    os.makedirs('credentials', exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        import json
        json.dump(session, f, indent=2)

    console.print(f"[green]✓ Saved web session[/green]")
    console.print(f"  Realm: {session['realm_id']}")
    console.print(f"  User:  {session.get('user_id')}")
    console.print(f"  Cookies: {len(session['cookies'])}")
    console.print(f"  File:  {SESSION_FILE}")
    console.print(f"\n[green]✓ Now run:[/green] python3 -m src.cli fetch-transactions")


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


@cli.command()
def fetch_transactions():
    """Fetch unreconciled transactions from QuickBooks"""
    config = load_config()
    db = Database(config['database']['path'])
    try:
        _fetch_transactions(config, db)
    finally:
        db.close()


def _fetch_transactions(config: dict, db: Database) -> int:
    """Fetch transactions and save to DB. Returns count fetched."""
    qb_config = config.get('quickbooks') or {}
    use_web = config.get('qbo_web', {}).get('enabled', True) and not qb_config.get('csv_path')

    if use_web:
        console.print("[blue]Fetching 'For Review' transactions via QBO web session...[/blue]")
        from .qbo_web_client import QBOWebClient
        try:
            client = QBOWebClient(qb_config)
            client.authenticate()
            transactions = client.fetch_all_for_review()
        except FileNotFoundError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Web session failed: {e}[/red]")
            console.print("[dim]Re-run `python3 -m src.cli web-auth` with a fresh cURL.[/dim]")
            sys.exit(1)
    else:
        console.print("[blue]Fetching unreconciled transactions from QuickBooks...[/blue]")
        qb = QuickBooksClient(qb_config)
        qb.authenticate()
        transactions = qb.get_unreconciled_transactions(days_back=90)

    for txn in transactions:
        db.save_transaction(txn)

    console.print(f"[green]✓ Fetched {len(transactions)} transactions[/green]")

    if transactions:
        table = Table(title="Unreconciled Transactions")
        table.add_column("Date", style="cyan")
        table.add_column("Amount", style="magenta")
        table.add_column("Payee", style="green")
        table.add_column("Account", style="blue")

        for txn in transactions[:10]:
            table.add_row(
                str(txn.date),
                f"£{txn.amount:.2f}",
                txn.payee_name[:40],
                txn.account_name
            )

        console.print(table)

        if len(transactions) > 10:
            console.print(f"[dim]... and {len(transactions) - 10} more[/dim]")

    return len(transactions)


@cli.command()
def search_invoices():
    """Search Gmail for invoices matching unreconciled transactions"""
    config = load_config()
    db = Database(config['database']['path'])
    try:
        _search_invoices(config, db)
    finally:
        db.close()


def _search_invoices(config: dict, db: Database) -> int:
    """Search Gmail and save matches. Returns match count."""
    transactions = db.get_unprocessed_transactions()

    if not transactions:
        console.print("[yellow]No unreconciled transactions found. Run 'fetch-transactions' first.[/yellow]")
        return 0

    console.print(f"[blue]Found {len(transactions)} unreconciled transactions[/blue]")
    console.print("[blue]Searching Gmail for invoices...[/blue]")

    gmail_config = {**config['gmail'], 'date_window_days': config['matching']['date_window_days']}
    gmail = GmailSearcher(gmail_config)
    gmail.authenticate()

    parser = PDFParser()
    matcher = Matcher(config['matching'])

    total_matches = 0

    for txn in transactions:
        console.print(f"\n[cyan]Searching for: {txn.date} | £{txn.amount:.2f} | {txn.payee_name}[/cyan]")

        candidates = gmail.search_for_invoice(txn)

        if not candidates:
            console.print("[yellow]  No invoice emails found[/yellow]")
            continue

        console.print(f"  Found {len(candidates)} candidate email(s)")

        for candidate in candidates:
            if candidate['attachments']:
                downloaded_files = gmail.download_attachments(
                    candidate['message_id'],
                    candidate['attachments'],
                    txn
                )

                for filepath in downloaded_files:
                    invoice = parser.parse_invoice(filepath, candidate['message_id'], txn.amount)
                    match = matcher.match_transaction_to_invoice(txn, invoice)

                    if match.score >= config['matching']['min_confidence_score']:
                        db.save_match(match)
                        db.update_transaction_status(txn.id, 'matched')
                        total_matches += 1
                        console.print(f"  [green]✓ Match found (score: {match.score})[/green]")

    console.print(f"\n[green]✓ Found {total_matches} potential matches[/green]")
    return total_matches


@cli.command()
def review():
    """Review and approve matches"""
    config = load_config()
    db = Database(config['database']['path'])
    try:
        _review(config, db)
    finally:
        db.close()


def _review(config: dict, db: Database) -> None:
    """Interactive approve/reject/skip for pending matches."""
    matches = db.get_all_unreviewed_matches()

    if not matches:
        console.print("[yellow]No matches to review. Run 'search-invoices' first.[/yellow]")
        return

    console.print(f"[blue]Found {len(matches)} matches to review[/blue]\n")

    current_txn_id = None

    for match_row in matches:
        if match_row['qb_transaction_id'] != current_txn_id:
            current_txn_id = match_row['qb_transaction_id']
            console.print("=" * 70)
            console.print(f"[cyan]Transaction: {match_row['txn_date']} | £{match_row['txn_amount']:.2f} | {match_row['payee_name']}[/cyan]")
            console.print()

        console.print(f"Match (score: {match_row['confidence_score']}):")
        console.print(f"  Invoice: {match_row['invoice_number'] or 'N/A'}")
        console.print(f"  Amount: £{match_row['invoice_amount']:.2f}" if match_row['invoice_amount'] else "  Amount: N/A")
        console.print(f"  Date: {match_row['invoice_date']}" if match_row['invoice_date'] else "  Date: N/A")
        if match_row['vat_type']:
            console.print(f"  VAT: {match_row['vat_type']} ({match_row['vat_rate'] or 'N/A'})")
            if match_row['vat_amount']:
                console.print(f"  VAT Amount: £{match_row['vat_amount']:.2f}")
        console.print(f"  File: {Path(match_row['attachment_path']).name}")
        console.print()

        choice = click.prompt("Approve this match? [y/n/skip]", type=str, default='y')

        if choice.lower() == 'y':
            db.update_match_approval(match_row['id'], True)
            console.print("[green]✓ Approved[/green]\n")
        elif choice.lower() == 'n':
            console.print("[red]✗ Rejected[/red]\n")
        else:
            console.print("[yellow]→ Skipped[/yellow]\n")

    console.print("[green]✓ Review complete[/green]")


@cli.command()
def run():
    """Run the full workflow: fetch-transactions → search-invoices → review"""
    config = load_config()
    db = Database(config['database']['path'])
    try:
        console.print("[bold blue]═══ Step 1/3: Fetch transactions ═══[/bold blue]\n")
        fetched = _fetch_transactions(config, db)

        console.print("\n[bold blue]═══ Step 2/3: Search invoices ═══[/bold blue]\n")
        if fetched == 0:
            console.print("[yellow]No transactions to search. Exiting.[/yellow]")
            return
        matched = _search_invoices(config, db)

        console.print("\n[bold blue]═══ Step 3/3: Review matches ═══[/bold blue]\n")
        if matched == 0:
            console.print("[yellow]No matches to review. Done.[/yellow]")
            return
        _review(config, db)

        console.print("\n[bold green]✓ Workflow complete.[/bold green]")
        console.print("[bold]═══ Matched transactions summary ═══[/bold]\n")
        _print_matched_summary(db)
        console.print("\n[dim]Run 'reconcile' to push to QuickBooks, or 'matched' to see this summary again.[/dim]")
    finally:
        db.close()


@cli.command()
@click.option('--auto', is_flag=True, help='Skip interactive category review')
def reconcile(auto):
    """Mark approved matches as reconciled in QuickBooks"""
    config = load_config()
    
    console.print("[blue]Reconciling approved matches in QuickBooks...[/blue]")
    
    try:
        qb = QuickBooksClient(config['quickbooks'])
        qb.authenticate()
        
        db = Database(config['database']['path'])
        reconciler = Reconciler(qb, db)
        
        summary = reconciler.reconcile_approved_matches(interactive=not auto)
        
        db.close()
        
        console.print(f"\n[green]✓ Reconciled: {summary['reconciled']}[/green]")
        console.print(f"[cyan]✓ PDFs uploaded: {summary['uploaded']}[/cyan]")
        console.print(f"[magenta]✓ Categories updated: {summary['categories_updated']}[/magenta]")
        console.print(f"[red]✗ Failed: {summary['failed']}[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Show summary of transactions and matches"""
    config = load_config()
    db = Database(config['database']['path'])

    summary = db.get_status_summary()

    table = Table(title="Invoice Matcher Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")

    table.add_row("Total Transactions", str(summary['total_transactions']))
    table.add_row("Unmatched", str(summary['unmatched']))
    table.add_row("Matched", str(summary['matched']))
    table.add_row("Reconciled", str(summary['reconciled']))
    table.add_row("Approved Matches", str(summary['approved_matches']))

    console.print(table)

    db.close()


@cli.command()
def matched():
    """Show matched transactions with invoice PDF paths for manual reconciliation"""
    config = load_config()
    db = Database(config['database']['path'])
    _print_matched_summary(db)
    db.close()


def _print_matched_summary(db: Database) -> None:
    """Print matched transactions with full PDF paths for manual reconciliation."""
    matches = db.get_all_matches_detail()

    if not matches:
        console.print("[yellow]No matches found. Run 'search-invoices' or 'run' first.[/yellow]")
        return

    console.print(f"[bold]Matched Transactions ({len(matches)})[/bold]\n")

    approved_count = 0
    for i, m in enumerate(matches, 1):
        pdf_path = str(Path(m['attachment_path'])) if m['attachment_path'] else 'N/A'
        pdf_name = Path(m['attachment_path']).name if m['attachment_path'] else 'N/A'

        inv_amt = f"£{m['invoice_amount']:.2f}" if m['invoice_amount'] else 'N/A'
        payee = m['payee_name'][:30] if m['payee_name'] else '(no payee)'

        vat_str = 'N/A'
        if m['vat_type']:
            vat_str = m['vat_type']
            if m['vat_rate']:
                vat_str += f" ({m['vat_rate']})"
            if m['vat_amount']:
                vat_str += f" — £{m['vat_amount']:.2f}"

        if m['approved']:
            status_str = "[green]✓ Approved[/green]"
            approved_count += 1
        else:
            status_str = "[dim]Pending[/dim]"

        console.print(f"[cyan]{i}.[/cyan] [bold]{m['txn_date']}[/bold] | [magenta]£{m['txn_amount']:.2f}[/magenta] | {payee}")
        console.print(f"   Invoice: [white]{m['invoice_number'] or 'N/A'}[/white] | Amount: [yellow]{inv_amt}[/yellow] | VAT: [blue]{vat_str}[/blue] | Score: {m['confidence_score']} | {status_str}")
        console.print(f"   [dim]PDF: {pdf_path}[/dim]")
        console.print()

    console.print(f"[green]Approved: {approved_count}[/green]  [dim]Pending review: {len(matches) - approved_count}[/dim]")
    console.print("[dim]In QuickBooks → Banking → For Review, find the transaction and upload the matching PDF.[/dim]")


if __name__ == '__main__':
    cli()
