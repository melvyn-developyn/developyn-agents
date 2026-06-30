import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Invoice, Match, Transaction


class Database:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_transactions (
                qb_transaction_id TEXT PRIMARY KEY,
                date DATE,
                amount REAL,
                payee_name TEXT,
                memo TEXT,
                account_name TEXT,
                processed_at TIMESTAMP,
                status TEXT DEFAULT 'unmatched'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qb_transaction_id TEXT,
                email_message_id TEXT,
                attachment_path TEXT,
                invoice_number TEXT,
                invoice_amount REAL,
                invoice_date DATE,
                vendor_name TEXT,
                confidence_score INTEGER,
                approved BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                vat_amount REAL,
                vat_rate TEXT,
                net_amount REAL,
                vat_type TEXT,
                FOREIGN KEY (qb_transaction_id) REFERENCES processed_transactions(qb_transaction_id)
            )
        """)
        
        self.conn.commit()

    def save_transaction(self, transaction: Transaction):
        cursor = self.conn.cursor()
        # Insert only if new; preserve existing status so re-fetching
        # doesn't wipe 'matched'/'reconciled' progress.
        cursor.execute("""
            INSERT INTO processed_transactions
            (qb_transaction_id, date, amount, payee_name, memo, account_name, processed_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(qb_transaction_id) DO UPDATE SET
                date=excluded.date,
                amount=excluded.amount,
                payee_name=excluded.payee_name,
                memo=excluded.memo,
                account_name=excluded.account_name,
                processed_at=excluded.processed_at
        """, (
            transaction.id,
            transaction.date.isoformat(),
            float(transaction.amount),
            transaction.payee_name,
            transaction.memo,
            transaction.account_name,
            datetime.now().isoformat(),
            transaction.status
        ))
        self.conn.commit()

    def get_unprocessed_transactions(self) -> List[Transaction]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM processed_transactions
            WHERE status = 'unmatched'
            ORDER BY date DESC
        """)
        
        rows = cursor.fetchall()
        transactions = []
        for row in rows:
            from decimal import Decimal
            transactions.append(Transaction(
                id=row['qb_transaction_id'],
                date=datetime.fromisoformat(row['date']).date(),
                amount=Decimal(str(row['amount'])),
                payee_name=row['payee_name'],
                memo=row['memo'],
                account_name=row['account_name'],
                status=row['status']
            ))
        return transactions

    def save_match(self, match: Match):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO matches
            (qb_transaction_id, email_message_id, attachment_path, invoice_number,
             invoice_amount, invoice_date, vendor_name, confidence_score, approved, created_at,
             vat_amount, vat_rate, net_amount, vat_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.transaction.id,
            match.invoice.email_message_id,
            match.invoice.attachment_path,
            match.invoice.invoice_number,
            float(match.invoice.amount) if match.invoice.amount else None,
            match.invoice.invoice_date.isoformat() if match.invoice.invoice_date else None,
            match.invoice.vendor_name,
            match.score,
            match.approved,
            match.created_at.isoformat(),
            float(match.invoice.vat_amount) if match.invoice.vat_amount else None,
            match.invoice.vat_rate,
            float(match.invoice.net_amount) if match.invoice.net_amount else None,
            match.invoice.vat_type
        ))
        self.conn.commit()

    def get_matches_for_transaction(self, transaction_id: str) -> List[Match]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, t.date, t.amount, t.payee_name, t.memo, t.account_name
            FROM matches m
            JOIN processed_transactions t ON m.qb_transaction_id = t.qb_transaction_id
            WHERE m.qb_transaction_id = ?
            ORDER BY m.confidence_score DESC
        """, (transaction_id,))
        
        rows = cursor.fetchall()
        matches = []
        for row in rows:
            from decimal import Decimal
            transaction = Transaction(
                id=row['qb_transaction_id'],
                date=datetime.fromisoformat(row['date']).date(),
                amount=Decimal(str(row['amount'])),
                payee_name=row['payee_name'],
                memo=row['memo'],
                account_name=row['account_name']
            )
            invoice = Invoice(
                invoice_number=row['invoice_number'],
                amount=Decimal(str(row['invoice_amount'])) if row['invoice_amount'] else None,
                invoice_date=datetime.fromisoformat(row['invoice_date']).date() if row['invoice_date'] else None,
                vendor_name=row['vendor_name'],
                attachment_path=row['attachment_path'],
                email_message_id=row['email_message_id'],
                confidence_score=row['confidence_score']
            )
            matches.append(Match(
                transaction=transaction,
                invoice=invoice,
                score=row['confidence_score'],
                approved=bool(row['approved'])
            ))
        return matches

    def get_all_unreviewed_matches(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, t.date as txn_date, t.amount as txn_amount, 
                   t.payee_name, t.memo, t.account_name
            FROM matches m
            JOIN processed_transactions t ON m.qb_transaction_id = t.qb_transaction_id
            WHERE m.approved = 0
            ORDER BY t.date DESC, m.confidence_score DESC
        """)
        return cursor.fetchall()

    def get_approved_matches_for_reconciliation(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.*, t.date as txn_date, t.amount as txn_amount, 
                   t.payee_name, t.memo, t.account_name, t.status as txn_status
            FROM matches m
            JOIN processed_transactions t ON m.qb_transaction_id = t.qb_transaction_id
            WHERE m.approved = 1 AND t.status != 'reconciled'
            ORDER BY t.date DESC, m.confidence_score DESC
        """)
        return cursor.fetchall()

    def update_match_approval(self, match_id: int, approved: bool):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE matches SET approved = ? WHERE id = ?
        """, (approved, match_id))
        self.conn.commit()

    def update_transaction_status(self, transaction_id: str, status: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE processed_transactions SET status = ? WHERE qb_transaction_id = ?
        """, (status, transaction_id))
        self.conn.commit()

    def get_all_matches_detail(self) -> List[sqlite3.Row]:
        """Returns all matches joined with their transactions, ordered by date."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.id, m.approved,
                   t.qb_transaction_id, t.date as txn_date, t.amount as txn_amount,
                   t.payee_name, t.memo,
                   m.invoice_number, m.invoice_amount, m.invoice_date,
                   m.vendor_name, m.confidence_score,
                   m.vat_type, m.vat_rate, m.vat_amount, m.net_amount,
                   m.attachment_path
            FROM matches m
            JOIN processed_transactions t ON m.qb_transaction_id = t.qb_transaction_id
            ORDER BY t.date DESC, m.confidence_score DESC
        """)
        return cursor.fetchall()

    def get_status_summary(self) -> dict:
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM processed_transactions")
        total_transactions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_transactions WHERE status = 'unmatched'")
        unmatched = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_transactions WHERE status = 'matched'")
        matched = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_transactions WHERE status = 'reconciled'")
        reconciled = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM matches WHERE approved = 1")
        approved_matches = cursor.fetchone()[0]
        
        return {
            'total_transactions': total_transactions,
            'unmatched': unmatched,
            'matched': matched,
            'reconciled': reconciled,
            'approved_matches': approved_matches
        }

    def close(self):
        self.conn.close()
