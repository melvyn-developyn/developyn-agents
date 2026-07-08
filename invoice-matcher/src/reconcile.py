import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import yaml

from .gmail_client import GmailClient
from .pdf_parser import PDFParser

TRANSACTIONS = [
    {"date": "2026-06-29", "amount": "46.32", "payee": "Merlin", "aliases": ["merlin", "getmerlin"]},
    {"date": "2026-06-26", "amount": "47.27", "payee": "Merlin", "aliases": ["merlin", "getmerlin"]},
    {"date": "2026-06-08", "amount": "14.21", "payee": "ClickUp", "aliases": ["clickup"]},
    {"date": "2026-05-27", "amount": "47.40", "payee": "TC Payroll", "aliases": ["TC Payroll", "tide payroll"]},
]


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_query(payee_aliases, txn_date, expected_amount):
    """Build smart Gmail search queries from broad to specific."""
    after = (txn_date - timedelta(days=14)).strftime("%Y/%m/%d")
    before = (txn_date + timedelta(days=14)).strftime("%Y/%m/%d")

    alias_terms = " OR ".join(a.lower() for a in payee_aliases)

    queries = [
        # Invoice-related emails from or about this vendor
        f"after:{after} before:{before} ({alias_terms}) (subject:invoice OR subject:receipt OR subject:billing OR subject:payment OR filename:pdf)",
        # Broader: any email mentioning vendor in date range
        f"after:{after} before:{before} ({alias_terms})",
        # Self-sent (user may have emailed invoice to themselves)
        f"from:me after:{after} before:{before} ({alias_terms})",
    ]

    return queries


def main():
    config = load_config()
    gmail = GmailClient(config.get("gmail", {}))
    gmail.authenticate()

    parser = PDFParser()
    attachments_dir = Path(config["gmail"]["attachments_path"])
    attachments_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for txn in TRANSACTIONS:
        txn_date = date.fromisoformat(txn["date"])
        expected_amount = Decimal(txn["amount"])
        payee = txn["payee"]
        aliases = txn["aliases"]

        print(f"\n{'='*60}")
        print(f"Searching: {payee} — £{expected_amount} on {txn_date}")
        print(f"{'='*60}")

        queries = build_query(aliases, txn_date, expected_amount)

        found_match = None
        found_email = None
        found_pdf_paths = []
        found_vat_info = None
        found_invoice_number = None

        for qi, query in enumerate(queries):
            if found_match:
                break
            print(f"\n  Query {qi+1}: {query}")
            try:
                messages = gmail.search(query, max_results=10)
                print(f"  Results: {len(messages)} messages")
            except Exception as e:
                print(f"  Search error: {e}")
                continue

            for msg in messages:
                subject = msg.get("subject", "")
                snippet = msg.get("snippet", "").lower()
                has_attachment = msg.get("has_attachment", False)
                attachments = msg.get("attachment_filenames", [])

                # Check if this looks like an invoice
                is_invoice = any(kw in subject.lower() for kw in ["invoice", "receipt", "billing", "payment", "charged", "subscription"])
                has_pdf = any(f.endswith(".pdf") for f in attachments)

                # Also check if the amount appears in snippet
                amount_strs = [f"£{expected_amount}", f"${expected_amount}", f"£{expected_amount:.2f}", str(expected_amount)]
                amount_in_snippet = any(a in snippet for a in amount_strs)

                print(f"    [{msg['id']}] {subject[:80]}")
                print(f"        Attachments: {attachments}")
                print(f"        Invoice-like: {is_invoice}, Has PDF: {has_pdf}, Amount match: {amount_in_snippet}")

                if is_invoice or has_pdf:
                    found_email = msg
                elif amount_in_snippet:
                    found_email = msg

                if found_email:
                    # Try to download PDFs
                    try:
                        pdf_paths = gmail.download_all_attachments(
                            found_email["id"],
                            prefix=payee.lower().replace(" ", "_")
                        )
                        found_pdf_paths = pdf_paths
                    except Exception as e:
                        print(f"        Download error: {e}")

                    # Parse PDFs
                    for pdf_path in found_pdf_paths:
                        print(f"        Parsing: {pdf_path}")
                        try:
                            invoice = parser.parse_invoice(pdf_path, found_email["id"], expected_amount)
                            found_vat_info = {
                                "vat_type": invoice.vat_type,
                                "vat_amount": invoice.vat_amount,
                                "vat_rate": invoice.vat_rate,
                                "net_amount": invoice.net_amount,
                            }
                            found_invoice_number = invoice.invoice_number
                            print(f"        Invoice #: {invoice.invoice_number}, VAT: {invoice.vat_type}")
                            if invoice.amount:
                                print(f"        PDF Amount: £{invoice.amount} (Expected: £{expected_amount})")
                        except Exception as e:
                            print(f"        Parse error: {e}")

                    found_match = True
                    break

        # If no match found, try searching without date range
        if not found_match:
            print(f"\n  Trying without date range...")
            alias_terms = " OR ".join(a.lower() for a in aliases)
            try:
                messages = gmail.search(f"({alias_terms}) (subject:invoice OR receipt)", max_results=5)
                for msg in messages:
                    print(f"    [{msg['id']}] {msg.get('subject', '')[:80]}")
            except Exception as e:
                print(f"  Error: {e}")

        results.append({
            "date": txn["date"],
            "amount": txn["amount"],
            "payee": payee,
            "found": bool(found_match),
            "invoice_number": found_invoice_number,
            "pdf_paths": found_pdf_paths,
            "vat_info": found_vat_info,
            "email_id": found_email["id"] if found_email else None,
            "email_subject": found_email["subject"] if found_email else None,
            "notes": "",
        })

    # Print report
    print("\n\n" + "="*120)
    print("RECONCILIATION REPORT")
    print("="*120)
    print(f"{'Date':>12} | {'Amount':>8} | {'Payee':<14} | {'Found':>5} | {'Invoice #':<15} | {'PDF Path':<40} | {'VAT Type':<16} | Notes")
    print("-"*120)

    for r in results:
        pdf_path = (r["pdf_paths"][0] if r["pdf_paths"] else "-")[:40]
        inv_num = (r["invoice_number"] or "-")[:15]
        vat_type = (r["vat_info"]["vat_type"] if r["vat_info"] else "-") or "-"
        found = "Yes" if r["found"] else "No"
        notes = r.get("notes", "")
        if r["email_subject"]:
            notes = f"Email: {r['email_subject'][:40]}"

        print(f"{r['date']:>12} | £{r['amount']:>7} | {r['payee']:<14} | {found:>5} | {inv_num:<15} | {pdf_path:<40} | {vat_type:<16} | {notes}")

    print("\n\nInstructions:")
    print("In QuickBooks → Banking → For Review, find each transaction and upload the matching PDF.")
    print("Set the VAT tax code as listed above.")
    return results


if __name__ == "__main__":
    main()
