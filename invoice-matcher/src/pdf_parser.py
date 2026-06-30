import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Optional, Tuple

import pdfplumber
from dateutil import parser as date_parser

from .models import Invoice


class PDFParser:
    INVOICE_NUMBER_PATTERNS = [
        r'Invoice\s*(?:#|Number|No|Ref)[:\s]*([A-Z0-9\-]+)',
        r'Inv(?:oice)?\.?\s*(?:#|No)?[:\s]*([A-Z0-9\-]+)',
        r'Reference[:\s]*([A-Z0-9\-]+)',
        r'Bill\s*(?:#|Number|No)?[:\s]*([A-Z0-9\-]+)',
    ]

    AMOUNT_PATTERNS = [
        r'Total\s*\(including\s*(?:Tax|VAT)\)[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Total\s*Amount[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Amount\s*Due[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Grand\s*Total[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Balance\s*Due[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Total\s*Due[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Total[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'£([0-9,]+\.[0-9]{2})',
    ]

    DATE_PATTERNS = [
        r'Invoice\s*Date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'Date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'Dated[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'Issue[d]?\s*Date[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
    ]

    VAT_PATTERNS = [
        r'VAT\s*(?:Amount|Due|Total)?[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'Tax\s*(?:Amount|Due|Total)?[:\s]*£?([0-9,]+\.[0-9]{2})',
        r'VAT\s*@\s*(\d+)%',
        r'(?:Reverse\s*Charge|RC\s*VAT|VAT\s*Reverse)',
        r'(?:Zero\s*Rated|Zero\s*Rate|0%\s*VAT)',
        r'(?:Exempt|VAT\s*Exempt|No\s*VAT)',
    ]

    REVERSE_CHARGE_PATTERNS = [
        r'reverse\s*charge',
        r'RC\s*VAT',
        r'VAT\s*reverse',
        r'customer\s*to\s*account\s*for\s*VAT',
        r'VAT\s*act\s*reverse\s*charge',
    ]

    ZERO_RATED_PATTERNS = [
        r'zero\s*rated',
        r'0%\s*VAT',
        r'VAT\s*@\s*0%',
        r'zero\s*rate',
    ]

    EXEMPT_PATTERNS = [
        r'exempt',
        r'VAT\s*exempt',
        r'no\s*VAT',
        r'outside\s*scope',
    ]

    def extract_text(self, pdf_path: str) -> str:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def parse_invoice(self, pdf_path: str, email_message_id: str, expected_amount: Optional[Decimal] = None) -> Invoice:
        text = self.extract_text(pdf_path)
        
        if not text:
            return Invoice(
                invoice_number=None,
                amount=None,
                invoice_date=None,
                vendor_name=None,
                attachment_path=pdf_path,
                email_message_id=email_message_id,
                confidence_score=0.0
            )
        
        invoice_number = self._extract_field(text, self.INVOICE_NUMBER_PATTERNS)
        amount_str = self._extract_field(text, self.AMOUNT_PATTERNS)
        date_str = self._extract_field(text, self.DATE_PATTERNS)
        
        amount = self._parse_amount(amount_str) if amount_str else None
        invoice_date = self._parse_date(date_str) if date_str else None
        
        vat_info = self._detect_vat(text, amount)
        
        confidence_score = self._calculate_confidence(
            invoice_number, amount, invoice_date, expected_amount
        )
        
        return Invoice(
            invoice_number=invoice_number,
            amount=amount,
            invoice_date=invoice_date,
            vendor_name=None,
            attachment_path=pdf_path,
            email_message_id=email_message_id,
            confidence_score=confidence_score,
            vat_amount=vat_info['vat_amount'],
            vat_rate=vat_info['vat_rate'],
            net_amount=vat_info['net_amount'],
            vat_type=vat_info['vat_type']
        )

    def _detect_vat(self, text: str, total_amount: Optional[Decimal]) -> dict:
        text_lower = text.lower()
        
        vat_type = None
        vat_rate = None
        vat_amount = None
        net_amount = None
        
        if any(re.search(p, text_lower) for p in self.REVERSE_CHARGE_PATTERNS):
            vat_type = 'reverse_charge'
            vat_rate = 'RC'
        elif any(re.search(p, text_lower) for p in self.ZERO_RATED_PATTERNS):
            vat_type = 'zero_rated'
            vat_rate = '0%'
        elif any(re.search(p, text_lower) for p in self.EXEMPT_PATTERNS):
            vat_type = 'exempt'
            vat_rate = 'Exempt'
        else:
            vat_amount_str = self._extract_field(text, [
                r'Tax\s*(?:Amount|Due|Total)?[:\s]*£?([0-9,]+\.[0-9]{2})',
                r'VAT\s*(?:Amount|Due|Total)?[:\s]*£?([0-9,]+\.[0-9]{2})',
            ])
            if vat_amount_str:
                vat_amount = self._parse_amount(vat_amount_str)
                if vat_amount and total_amount:
                    net_amount = total_amount - vat_amount
                    if net_amount > 0:
                        rate = (vat_amount / net_amount * 100).quantize(Decimal('1'))
                        vat_rate = f'{rate}%'
                        if rate == 20:
                            vat_type = 'standard'
                        elif rate == 5:
                            vat_type = 'reduced'
                        else:
                            vat_type = 'custom'
                else:
                    vat_type = 'unknown'
            else:
                vat_rate_str = self._extract_field(text, [
                    r'(\d+\.?\d*)%\s*(?:VAT|Tax)',
                    r'VAT\s*@\s*(\d+\.?\d*)%',
                    r'Tax\s*Rate[:\s]*(\d+\.?\d*)%',
                ])
                if vat_rate_str:
                    rate = Decimal(vat_rate_str)
                    vat_rate = f'{rate}%'
                    if rate == 20:
                        vat_type = 'standard'
                    elif rate == 5:
                        vat_type = 'reduced'
                    elif rate == 0:
                        vat_type = 'zero_rated'
                    else:
                        vat_type = 'custom'
                else:
                    vat_type = 'no_vat'
        
        return {
            'vat_type': vat_type,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'net_amount': net_amount
        }

    def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        try:
            cleaned = amount_str.replace(',', '')
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        try:
            return date_parser.parse(date_str, dayfirst=True).date()
        except (ValueError, TypeError):
            return None

    def _calculate_confidence(
        self,
        invoice_number: Optional[str],
        amount: Optional[Decimal],
        invoice_date: Optional[datetime.date],
        expected_amount: Optional[Decimal]
    ) -> float:
        score = 0.0
        
        if invoice_number:
            score += 25.0
        
        if amount:
            score += 25.0
            if expected_amount and abs(amount - expected_amount) <= Decimal('0.01'):
                score += 30.0
            elif expected_amount and abs(amount - expected_amount) <= Decimal('1.00'):
                score += 15.0
        
        if invoice_date:
            score += 20.0
        
        return score
