from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    id: str
    date: date
    amount: Decimal
    payee_name: str
    memo: str
    account_name: str
    status: str = "unmatched"
    matched_invoice_id: Optional[str] = None
    matched_invoice_number: Optional[str] = None
    processed_at: Optional[datetime] = None


@dataclass
class Invoice:
    invoice_number: Optional[str]
    amount: Optional[Decimal]
    invoice_date: Optional[date]
    vendor_name: Optional[str]
    attachment_path: str
    email_message_id: str
    confidence_score: float = 0.0
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[str] = None
    net_amount: Optional[Decimal] = None
    vat_type: Optional[str] = None


@dataclass
class Match:
    transaction: Transaction
    invoice: Invoice
    score: int
    reasons: list = field(default_factory=list)
    approved: bool = False
    created_at: datetime = field(default_factory=datetime.now)
