# Developyn Admin Agents

## Repo Overview

This repo contains admin automation tools for Developyn Ltd (software development consultancy). Currently: `invoice-matcher/`, `aws-to-do-migration/`.

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

- Gmail: `credentials/gmail_credentials.json` (OAuth2 client secrets) + `credentials/gmail_token.json` (auto-generated on first auth) + `credentials/gmail_token.json.bak` (backup)
- QuickBooks OAuth2 (unused, legacy): `credentials/qb_token.json`
- QuickBooks web session: `credentials/qbo_web_session.json` (imported via `web-auth` from a "Copy as cURL")
- All credentials are gitignored

### Data & Config

- `config.yaml` — Gmail paths and QuickBooks settings (env vars via `${QB_*}`)
- `.env` / `.env.example` — QuickBooks OAuth env vars (Client ID, Secret, Realm ID)
- `data/attachments/` — Downloaded PDF invoice attachments (gitignored)
- `credentials/` — API credential files (gitignored at runtime)

### Design Patterns

- **Agent-first**: Code provides capabilities; the LLM agent decides how to use them
- **Ephemeral sessions**: QBO web session expires in days/weeks — documented refresh procedure
- **Credential isolation**: All secrets in `credentials/` and `data/`, all gitignored
- **Decimal arithmetic**: All monetary values use `Decimal` (no floats)
- **Rich table output**: Terminal-formatted tables via the `rich` library

### Common Pitfalls

- **Always use `python3`**, not `python`
- **Web session returns 0 or errors**: Cookies expired. Re-run `web-auth`.
- **Gmail search tips**: `subject:invoice` does NOT match "invoices" — use plurals too. `has:attachment` only matches files. `from:me` finds self-sent emails. Some vendors (YouTube, OpenAI, ClickUp) don't email invoices — user must download from their platform and email to themselves.

### Dependencies

Python 3.11+. Install with `pip install -r requirements.txt`.

### Project Structure

```
invoice-matcher/
├── config.yaml                        # Gmail + QuickBooks config
├── requirements.txt                   # Python dependencies
├── .env / .env.example                # QBO OAuth env vars (gitignored)
├── .gitignore                         # Excludes credentials/, data/
├── credentials/                       # OAuth tokens (gitignored at runtime)
│   ├── gmail_credentials.json         # OAuth2 client secrets
│   ├── gmail_token.json              # Auto-generated refresh token
│   ├── gmail_token.json.bak          # Backup token
│   ├── qb_token.json                 # Legacy QuickBooks OAuth (unused)
│   └── qbo_web_session.json          # Intuit banking session
├── data/attachments/                  # Downloaded PDFs (gitignored)
└── src/                               # Python source package
    ├── cli.py                         # CLI: web-auth, web-test, fetch-transactions
    ├── qbo_web_client.py              # QBO web session client (Intuit API)
    ├── gmail_client.py               # Gmail API client (search, read, download, draft)
    ├── pdf_parser.py                 # PDF text extraction + VAT detection
    ├── models.py                      # Transaction + Invoice dataclasses
    └── reconcile.py                  # Standalone demo with hardcoded transactions
```

### Key Modules

**`src/cli.py`** — Click-based CLI entry point
- `web-auth`: Parses Chrome "Copy as cURL" output, saves to `credentials/qbo_web_session.json`
- `web-test`: Loads session, fetches transactions, prints first 10
- `fetch-transactions`: Loads session, fetches, prints Rich table of up to 20

**`src/qbo_web_client.py`** — QuickBooks web session client (263 lines)
- Wraps Intuit's internal `accounting-txn-svcs` API (not the official SDK)
- `authenticate()`: Loads `credentials/qbo_web_session.json`, overrides `realm_id` from session (authoritative, even if `QB_REALM_ID` env var points at sandbox)
- `fetch_all_for_review()`: Iterates all configured account_ids (supports int/list/comma-str), fetches via `GET /v1/company/{realm}/banking/getTransactions?reviewState=PENDING&sort=-txnDate`
- `_normalize()`: Prefers `origDescription` (untruncated, includes domain names and foreign currencies) over `description`
- `parse_curl_to_session()`: Parses Chrome DevTools cURL with regex for cookies, apikey, CSRF tokens, realm_id

**`src/gmail_client.py`** — Gmail API client (219 lines)
- `authenticate()`: OAuth2 flow — tries `from_authorized_user_file()` with refresh, falls back to `InstalledAppFlow.run_local_server(port=0)`
- `search()`: Lists messages, gets full format for each, extracts headers, checks for PDF attachments
- `get_body_text()`: Extracts base64-decoded `text/plain` body (handles multipart)
- `download_attachment()`: Gets attachment via `users().messages().attachments().get()`, base64-decodes, writes to disk
- `download_all_attachments()`: Downloads only PDFs, prepends prefix to filename
- `create_draft()`: RFC 822 message with `\r\n` line endings, base64-encodes as `raw` field; supports `threadId` + `in_reply_to` for reply threading

**`src/pdf_parser.py`** — PDF parser + VAT detection (226 lines)
- `extract_text()`: Uses `pdfplumber` — `page.extract_text()` returns None if no text layer
- `parse_invoice()`: Main entry — extracts text, calls helper methods, builds `Invoice` dataclass
- **VAT detection priority**: reverse_charge → zero_rated → exempt → standard/rate-based
- Derives rate from `vat_amount/net_amount` using Decimal arithmetic
- Confidence scoring method exists but is unused in current code path

**`src/models.py`** — Data structures (28 lines)
- `Transaction`: id, date, amount (Decimal), payee_name, memo (origDescription), account_name
- `Invoice`: invoice_number, amount, invoice_date, vendor_name (not extracted), attachment_path, email_message_id, vat_amount, vat_rate, net_amount, vat_type

**`src/reconcile.py`** — Standalone demo (188 lines, not wired into CLI)
- Hardcoded `TRANSACTIONS` list with date/amount/payee/aliases
- `build_query()`: Generates 3 Gmail search queries (broad→specific) with date ranges (±14 days)
- Full flow: iterate → search Gmail with fallbacks → download PDFs → parse → print report

**`config.yaml`** — Configuration
- `gmail.credentials_file`, `gmail.token_file`, `gmail.attachments_path`
- `quickbooks.client_id`, `quickbooks.client_secret`, `quickbooks.realm_id` (env vars `${QB_CLIENT_ID}`, `${QB_CLIENT_SECRET}`, `${QB_REALM_ID}`)
- `quickbooks.environment: "sandbox"`, `quickbooks.sandbox: true`, `quickbooks.csv_path: ""` (not yet implemented)

---

## aws-to-do-migration

### What It Does

Operational documentation for migrating 12 AWS-hosted WordPress EC2 sites onto a Docker-based DigitalOcean host, then safely upgrading and decommissioning AWS resources.

### Status

- **DigitalOcean host**: `root@142.93.41.146` (Ubuntu 24.04.3 LTS, 4 vCPU, 8 GB RAM, London)
- **AWS account**: `630423658649`, IAM user: `arn:aws:iam::630423658649:user/Melvyn`
- **Stack**: Docker Compose (13 WordPress containers + MariaDB), Caddy reverse proxy with auto-HTTPS, Beszel monitoring

### Sites by Status

| Status | Sites |
|--------|-------|
| **Cut over (DNS changed)** | `acesectionsltd.co.uk`, `bradleygasservices.co.uk`, `pedmoreroofing.com` |
| **Staged (on DigitalOcean, DNS unchanged)** | `oakhilloptical.co.uk`, `meirglobal.org`, `aps-ltd.com`, `telehandlers.co.uk`, `ledgability.co.uk`, `venturema.co.uk`, `nationalhiresolutions.co.uk`, `igs-uk.org`, `developyn.com` |
| **Upgraded & verified** | Ace (PHP 7.4→8.1, WP 5.7→7.0), Bradley (PHP 7.4→8.1, WP 6.1→7.0) |

### Notable Details

- **`developyn.com`**: High-risk — Route 53 zone has ~153 records including Google/Zoho mail, SES DKIM, ACM, CloudFront aliases
- **`meirglobal.org`**: WordPress 5.6.17 (very old) with PHP 7.4
- **`igs-uk.org`**: Required PHP memory limit raise from 15M to 256M to avoid PHP fatals
- **`Oakhill`**: DNS is at One.com, not AWS
- **`ace-modern-mockup/index.html`**: Standalone HTML/CSS mockup for the Ace Sections website redesign

### Project Structure

```
aws-to-do-migration/
├── AGENTS.md                          # Detailed migration tracking
├── summary.txt                        # Condensed copy of AGENTS.md
└── ace-modern-mockup/index.html       # Ace Sections website mockup
```
