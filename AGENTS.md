# Developyn Admin Agents

## Repo Overview

This repo contains admin automation tools for Developyn Ltd (software development consultancy). Currently: `invoice-matcher/`.

## invoice-matcher

### What It Does

Transaction-first invoice matching:
1. Pulls unreconciled ("For Review") transactions from QuickBooks via the **web session** (internal banking API), or CSV/OAuth fallbacks
2. Searches Gmail for matching invoice emails using transaction data (amount, date, payee)
3. Parses PDF attachments, extracts VAT info
4. Scores matches, presents CLI review
5. On approval: sets VAT tax code in QB, uploads PDF, categorizes, reconciles

### Commands (always use `python3`)

```bash
cd invoice-matcher
python3 -m src.cli init              # Create SQLite DB
python3 -m src.cli web-auth          # Import QBO browser session from "Copy as cURL" (see below)
python3 -m src.cli web-test          # Test web session — prints current "For Review" count
python3 -m src.cli qb-auth           # OAuth2 with QuickBooks (legacy — app must be in Production mode)
python3 -m src.cli run               # Full workflow: fetch → search → review (one command)
python3 -m src.cli fetch-transactions  # Pull "For Review" transactions (web mode by default)
python3 -m src.cli search-invoices     # Search Gmail, parse PDFs, score matches
python3 -m src.cli review              # Interactive approve/reject/skip
python3 -m src.cli matched             # Show matched transactions with PDF paths
python3 -m src.cli reconcile           # Set VAT code, upload PDF, categorize, reconcile in QB
python3 -m src.cli reconcile --auto    # Non-interactive reconcile
python3 -m src.cli status              # Summary counts
```

### Key Architecture Facts

- **Transaction-first**: Starts with QB "For Review" transactions, searches Gmail for each. Not invoice-first.
- **Web session mode (default)**: Fetches live "For Review" bank transactions via Intuit's internal `accounting-txn-svcs` API using browser session cookies. Works against the production company without needing the Intuit app in Production mode. Session stored in `credentials/qbo_web_session.json`.
- **CSV fallback**: If `quickbooks.csv_path` is set in `config.yaml`, reads from a CSV instead. Used historically during development.
- **OAuth fallback**: `qb-auth` uses Intuit OAuth2. Only works when the Intuit app is in Production mode (otherwise it connects to a sandbox with demo data only).
- **No web UI yet**: CLI only. Web UI is planned.
- **SQLite for state**: Tracks processed transactions and match results. DB at `data/invoice_matcher.db` (gitignored). Re-fetching transactions preserves existing `matched`/`reconciled` status.
- **VAT detection**: Parses PDFs for reverse charge, zero-rated, exempt, standard (20%), reduced (5%). Maps to QB tax codes: T1 (standard), T2 (zero), T3 (exempt), T8 (reverse charge), T9 (no VAT).

### Refreshing the web session

The browser cookies expire (typically days to weeks). When `web-test` or `fetch-transactions` returns 0 or fails with an auth error, refresh:

1. Open `https://qbo.intuit.com/app/banking` in Chrome (must be logged in)
2. DevTools → Network → filter `Fetch/XHR` → reload
3. Find the `getTransactions?accountId=57&...` request (JSON response)
4. Right-click → Copy → Copy as cURL (bash)
5. Run: `pbpaste | python3 -m src.cli web-auth`

The realm_id, user_id, apikey, CSRF tokens, and cookies are parsed from the cURL and saved to `credentials/qbo_web_session.json`. The session's realm_id is authoritative — it overrides `QB_REALM_ID` in `.env` (which may point at a sandbox from `qb-auth`).

### Credential Setup

- Gmail: `credentials/gmail_credentials.json` (OAuth2 desktop app) + `credentials/gmail_token.json` (auto-generated on first auth)
- QuickBooks (web mode, default): `credentials/qbo_web_session.json` (imported via `web-auth` from a "Copy as cURL"). No `.env` keys required for web mode — realm/user/apikey live inside the session file.
- QuickBooks (OAuth, fallback): `.env` with `QB_CLIENT_ID`, `QB_CLIENT_SECRET`, `QB_REALM_ID` + `credentials/qb_token.json` (auto-generated via `qb-auth`)
- **Redirect URI for QB OAuth**: `http://localhost:3001/callback` — must match Intuit Developer app config
- All credentials are gitignored

### Matching Config (`config.yaml`)

Current tuned values (adjust if too strict/loose):
- `amount_tolerance: 1.00` — allows £1 difference for rounding
- `date_window_days: 14` — searches ±14 days from transaction date
- `vendor_name_similarity: 0.60` — fuzzy match threshold
- `min_confidence_score: 30` — minimum score to present as candidate

### Common Pitfalls

- **Always use `python3`**, not `python` (system defaults to Python 2.7)
- **Web session returns 0**: Cookies expired. Re-run `web-auth` with a fresh "Copy as cURL" from `qbo.intuit.com/app/banking` (see "Refreshing the web session" above).
- **QB OAuth 403 errors**: The Intuit app is in Development mode. `qb-auth` will only connect to a sandbox company (demo data). Use `web-auth` for live data instead.
- **`QB_REALM_ID` mismatch**: `qb-auth` overwrites `QB_REALM_ID` in `.env` with the sandbox realm. The web client ignores this and uses the realm from `qbo_web_session.json`.
- **Gmail token format**: The token file needs `client_id` and `client_secret` fields — the code auto-injects these from `gmail_credentials.json` if missing
- **CSV mode bypasses QB**: When `csv_path` is set, `reconcile` only updates local DB status, not QuickBooks. Remove `csv_path` to use real QB API.

### Dependencies

Python 3.11+. Install with `pip install -r requirements.txt`.
Note: Some pinned versions conflict with other system packages (click 8.1.7, rich 13.7.0) but work fine in isolation.
