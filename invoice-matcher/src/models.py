from dataclasses import dataclass
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


@dataclass
class Invoice:
    invoice_number: Optional[str]
    amount: Optional[Decimal]
    invoice_date: Optional[date]
    vendor_name: Optional[str]
    attachment_path: str
    email_message_id: str
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[str] = None
    net_amount: Optional[Decimal] = None
    vat_type: Optional[str] = None
