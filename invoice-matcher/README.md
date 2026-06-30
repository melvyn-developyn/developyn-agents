# Invoice Matcher

Automated invoice-to-bank-transaction matching system for Developyn.

Pulls unreconciled transactions from QuickBooks, searches Gmail for matching invoices, and helps reconcile them.

## Setup

### 1. Install Dependencies

```bash
cd invoice-matcher
pip install -r requirements.txt
```

### 2. Configure API Credentials

#### Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "Invoice Matcher"
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials JSON
6. Save as `credentials/gmail_credentials.json`

#### QuickBooks API

1. Go to [Intuit Developer Portal](https://developer.intuit.com/)
2. Create a new app (QuickBooks Online and Payments)
3. Get your Client ID, Client Secret, and Realm ID
4. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your QuickBooks credentials.

### 3. Initialize Database

```bash
python -m src.cli init
```

## Usage

### Fetch Unreconciled Transactions

```bash
python -m src.cli fetch-transactions
```

Pulls unreconciled bank/credit card transactions from QuickBooks (last 90 days).

### Search for Invoices

```bash
python -m src.cli search-invoices
```

For each unreconciled transaction, searches Gmail for matching invoices and downloads PDF attachments.

### Review Matches

```bash
python -m src.cli review
```

Interactive review of matched invoices. Approve, reject, or skip matches.

### Reconcile in QuickBooks

```bash
python -m src.cli reconcile
```

Marks approved matches as reconciled in QuickBooks.

### Show Status

```bash
python -m src.cli status
```

Shows summary of processed transactions and matches.

## Workflow

1. Run `fetch-transactions` to get unreconciled transactions from QuickBooks
2. Run `search-invoices` to find matching invoices in Gmail
3. Run `review` to review and approve matches
4. Run `reconcile` to mark approved matches as reconciled in QuickBooks

## Configuration

Edit `config.yaml` to adjust:

- Matching thresholds (amount tolerance, date window, vendor similarity)
- Gmail search parameters
- QuickBooks settings
- Database and attachment paths

## Project Structure

```
invoice-matcher/
├── config.yaml              # Configuration
├── requirements.txt         # Python dependencies
├── .env                     # API credentials (not in git)
├── src/
│   ├── quickbooks_client.py # QuickBooks API integration
│   ├── gmail_searcher.py    # Gmail search and download
│   ├── pdf_parser.py        # PDF invoice extraction
│   ├── matcher.py           # Matching algorithm
│   ├── reconciler.py        # QuickBooks reconciliation
│   ├── models.py            # Data models
│   ├── database.py          # SQLite database layer
│   └── cli.py               # CLI interface
├── credentials/             # API credentials (not in git)
└── data/
    ├── invoice_matcher.db   # SQLite database
    └── attachments/         # Downloaded invoice PDFs
```
