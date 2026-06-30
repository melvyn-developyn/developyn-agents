from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher
from typing import List, Optional
import re

from .models import Invoice, Match, Transaction


class Matcher:
    def __init__(self, config: dict):
        self.amount_tolerance = Decimal(str(config.get('amount_tolerance', 0.01)))
        self.date_window_days = config.get('date_window_days', 7)
        self.vendor_name_similarity = config.get('vendor_name_similarity', 0.75)
        self.min_confidence_score = config.get('min_confidence_score', 60)

    def match_transaction_to_invoice(
        self,
        transaction: Transaction,
        invoice: Invoice
    ) -> Match:
        score = 0
        reasons = []

        # 1. GBP amount match
        if invoice.amount and transaction.amount:
            amount_diff = abs(transaction.amount - invoice.amount)
            if amount_diff <= self.amount_tolerance:
                score += 50
                reasons.append("Exact amount match")
            elif amount_diff <= Decimal('1.00'):
                score += 25
                reasons.append(f"Amount within £1 (diff: £{amount_diff:.2f})")

        # 2. Foreign currency amount match
        foreign_amount = self._extract_foreign_amount(transaction.memo)
        if foreign_amount and invoice.amount:
            foreign_diff = abs(invoice.amount - foreign_amount)
            if foreign_diff <= self.amount_tolerance:
                score += 45
                reasons.append(f"Foreign amount match (£{foreign_amount})")
            elif foreign_diff <= Decimal('1.00'):
                score += 20
                reasons.append(f"Foreign amount within £1 (£{foreign_amount}, diff: £{foreign_diff:.2f})")

        # 3. Date match
        if invoice.invoice_date and transaction.date:
            days_diff = abs((transaction.date - invoice.invoice_date).days)
            if days_diff <= 3:
                score += 30
                reasons.append(f"Date within 3 days ({days_diff}d diff)")
            elif days_diff <= self.date_window_days:
                score += 20
                reasons.append(f"Date within {self.date_window_days} days ({days_diff}d diff)")

        # 4. Invoice number in memo
        if invoice.invoice_number and transaction.memo:
            if invoice.invoice_number.upper() in transaction.memo.upper():
                score += 20
                reasons.append("Invoice # in reference")

        # 5. Vendor name similarity (invoice vendor vs transaction payee)
        if invoice.vendor_name and transaction.payee_name:
            similarity = self._calculate_similarity(invoice.vendor_name, transaction.payee_name)
            if similarity >= self.vendor_name_similarity:
                score += 15
                reasons.append(f"Vendor name match ({similarity:.0%})")
            elif similarity >= 0.4:
                score += 5
                reasons.append(f"Partial vendor name match ({similarity:.0%})")

        # 6. Vendor name in transaction memo (bank description)
        if invoice.vendor_name and transaction.memo:
            memo_lower = transaction.memo.lower()
            vendor_lower = invoice.vendor_name.lower()
            if vendor_lower in memo_lower:
                score += 10
                reasons.append("Vendor name in transaction description")

        return Match(
            transaction=transaction,
            invoice=invoice,
            score=score,
            reasons=reasons
        )

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _extract_foreign_amount(self, text: str) -> Optional[Decimal]:
        """Extract foreign currency amount from bank description.

        e.g., 'DKK 143.20' → Decimal('143.20')
              'USD 18.94' → Decimal('18.94')
        """
        if not text:
            return None
        match = re.search(
            r'(?:DKK|USD|EUR|SEK|NOK|AUD|CAD|JPY|CHF)\s+(\d+\.\d{2})',
            text, re.I
        )
        if match:
            return Decimal(match.group(1))
        return None

    def filter_matches(self, matches: List[Match]) -> List[Match]:
        return [m for m in matches if m.score >= self.min_confidence_score]
