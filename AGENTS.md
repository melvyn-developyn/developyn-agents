# Developyn Admin Agents

## Repo Overview

This repo contains admin automation tools for Developyn Ltd (software development consultancy). Currently: `invoice-matcher/`.

## invoice-matcher

### What It Does

Agent-assisted invoice matching:
1. The agent pulls unreconciled ("For Review") transactions from QuickBooks via the **web session** (internal banking API)
2. The agent searches Gmail using its own intelligence (not rigid scripts) for matching invoice emails
3. The agent reads email bodies, downloads PDF attachments, parses VAT info
4. The agent produces a reconciliation report for manual upload to QuickBooks

### Commands

```bash
cd invoice-matcher
python3 -m src.cli web-auth            # Import QBO browser session from "Copy as cURL"
python3 -m src.cli web-test            # Test web session
python3 -m src.cli fetch-transactions   # Pull "For Review" transactions (web mode)
```

### Skill

Run the `/find-quickbooks-invoices` skill. The agent will:
1. Ask for the QuickBooks web session token (Copy as cURL from Chrome DevTools)
2. Authenticate and fetch transactions
3. Search Gmail for each transaction's invoice (using LLM intelligence, not rigid queries)
4. Download PDFs, parse VAT
5. Produce a reconciliation report

### Architecture

- **Agent-driven matching**: The LLM agent searches Gmail flexibly for each transaction, reading email bodies and understanding context. No fixed scoring or rigid search queries.
- **Web session mode**: Fetches live "For Review" bank transactions via Intuit's internal `accounting-txn-svcs` API using browser session cookies.
- **No database**: The agent handles state and matching directly. No local DB needed.
- **Key modules**: `qbo_web_client.py` (QB fetch), `gmail_client.py` (Gmail API), `pdf_parser.py` (VAT extraction), `cli.py` (web-auth, fetch-transactions)

### Refreshing the web session

The browser cookies expire (typically days to weeks). When `web-test` or `fetch-transactions` fails:

1. Open `https://qbo.intuit.com/app/banking` in Chrome (must be logged in)
2. DevTools → Network → filter `Fetch/XHR` → reload
3. Find the `getTransactions?accountId=57&...` request (JSON response)
4. Right-click → Copy → Copy as cURL (bash)
5. Run: `pbpaste | python3 -m src.cli web-auth`

The realm_id, user_id, apikey, CSRF tokens, and cookies are parsed from the cURL and saved to `credentials/qbo_web_session.json`.

### Credential Setup

- Gmail: `credentials/gmail_credentials.json` (OAuth2 desktop app) + `credentials/gmail_token.json` (auto-generated on first auth)
- QuickBooks (web mode): `credentials/qbo_web_session.json` (imported via `web-auth` from a "Copy as cURL")
- All credentials are gitignored

### Common Pitfalls

- **Always use `python3`**, not `python`
- **Web session returns 0 or errors**: Cookies expired. Re-run `web-auth`.
- **Gmail search tips**: `subject:invoice` does NOT match "invoices" — use plurals too. `has:attachment` only matches files. `from:me` finds self-sent emails. Some vendors (YouTube, OpenAI, ClickUp) don't email invoices — user must download from their platform and email to themselves.

### Dependencies

Python 3.11+. Install with `pip install -r requirements.txt`.
