import base64
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .models import Transaction

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailSearcher:
    def __init__(self, config: dict):
        self.credentials_file = config.get('credentials_file', 'credentials/gmail_credentials.json')
        self.token_file = config.get('token_file', 'credentials/gmail_token.json')
        self.attachments_path = Path(config.get('attachments_path', 'data/attachments/'))
        self.attachments_path.mkdir(parents=True, exist_ok=True)
        self.date_window_days = config.get('date_window_days', 14)
        self.max_results = config.get('max_results', 10)
        self.service = None

    def authenticate(self):
        creds = None
        
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
            
            if 'client_id' not in token_data:
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    client_id = creds_data.get('installed', {}).get('client_id') or creds_data.get('web', {}).get('client_id')
                    client_secret = creds_data.get('installed', {}).get('client_secret') or creds_data.get('web', {}).get('client_secret')
                
                token_data['client_id'] = client_id
                token_data['client_secret'] = client_secret
                
                with open(self.token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
            
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)

    def search_for_invoice(self, transaction: Transaction) -> List[dict]:
        if not self.service:
            self.authenticate()

        query = self._build_search_query(transaction)

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
            ).execute()

            messages = results.get('messages', [])

            candidates = []
            for msg_info in messages:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_info['id'],
                    format='full'
                ).execute()

                candidate = self._extract_email_metadata(message)
                candidates.append(candidate)

            return candidates
        except Exception as e:
            print(f"Error searching Gmail: {e}")
            return []

    def _build_search_query(self, transaction: Transaction) -> str:
        queries = []

        window = self.date_window_days
        start_date = transaction.date - timedelta(days=window)
        end_date = transaction.date + timedelta(days=window)
        queries.append(f"after:{start_date:%Y/%m/%d}")
        queries.append(f"before:{end_date:%Y/%m/%d}")

        queries.append("subject:(invoice OR invoices OR receipt OR receipts OR statement OR statements OR bill OR bills)")
        queries.append("has:attachment")

        # Extract keywords from both payee_name AND memo
        keywords = self._extract_all_keywords(transaction)

        # Extract foreign currency amount from memo (e.g., "DKK 143.20")
        foreign_amount = self._extract_foreign_amount(transaction.memo)

        if keywords or foreign_amount:
            terms = [f'"{kw}"' for kw in keywords]
            if foreign_amount:
                terms.append(f'"{foreign_amount}"')
            queries.append(f"({' OR '.join(terms)})")

        return " ".join(queries)

    def _extract_all_keywords(self, transaction: Transaction) -> List[str]:
        """Extract vendor keywords from both payee_name and memo."""
        all_keywords = set()

        if transaction.payee_name:
            for kw in self._extract_vendor_keywords(transaction.payee_name):
                all_keywords.add(kw)

        if transaction.memo:
            for kw in self._extract_vendor_keywords(transaction.memo):
                all_keywords.add(kw)

        # Extract domain-like tokens from memo (anoma.ly, getmerlin.in)
        if transaction.memo:
            for domain in self._extract_domains(transaction.memo):
                all_keywords.add(domain)

        # Limit to avoid Gmail query length issues
        return list(all_keywords)[:6]

    def _extract_vendor_keywords(self, text: str) -> List[str]:
        vendor_aliases = {
            "openai": ["openai", "chatgpt"],
            "chatgpt": ["openai", "chatgpt"],
            "youtube": ["youtube", "google"],
            "google": ["google", "youtube", "gcp"],
            "clickup": ["clickup"],
            "merlin": ["merlin", "getmerlin"],
            "anomaly": ["anomaly", "anoma.ly"],
            "amazon web services": ["amazon", "aws"],
            "amazon": ["amazon", "aws"],
            "github": ["github"],
            "microsoft": ["microsoft", "azure"],
            "apple": ["apple"],
            "uber": ["uber"],
            "anthropic": ["anthropic"],
        }

        text_lower = text.lower()

        for canonical, aliases in vendor_aliases.items():
            if canonical in text_lower:
                return aliases

        # No alias match — extract meaningful words from the text
        banking_stop_words = {
            "ltd", "limited", "uk", "the", "co", "company", "services",
            "solutions", "int", "l", "non", "sterling", "transaction",
            "fee", "fees", "visa", "rate", "card", "xx", "xxxxxx",
            "dkk", "usd", "gbp", "eur", "sek", "nok", "aud", "cad",
            "jpy", "payroll", "paid", "bank", "banking", "international",
            "xx", "xxx",
        }

        # Remove masked card numbers, exchange rates, and long digit sequences
        cleaned = re.sub(r'x{2,}', ' ', text_lower)
        cleaned = re.sub(r'@\s*\d+\.?\d*', ' ', cleaned)
        cleaned = re.sub(r'\b\d{4,}\b', ' ', cleaned)

        words = re.findall(r'[a-z][a-z0-9.]+', cleaned)
        keywords = [w for w in words if w not in banking_stop_words and len(w) > 2]

        return keywords[:4]

    def _extract_domains(self, text: str) -> List[str]:
        """Extract domain-like tokens from text (e.g., anoma.ly, getmerlin.in)."""
        domains = re.findall(r'\b([a-z0-9]+\.[a-z]{2,4})\b', text.lower())
        noise = {'visa.rate', 'msbill.info'}
        return [d for d in domains if d not in noise]

    def _extract_foreign_amount(self, text: str) -> Optional[str]:
        """Extract foreign currency amount from bank description.

        e.g., 'DKK 143.20' → '143.20'
              'USD 18.94' → '18.94'
        """
        if not text:
            return None
        match = re.search(
            r'(?:DKK|USD|EUR|SEK|NOK|AUD|CAD|JPY|CHF)\s+(\d+\.\d{2})',
            text, re.I
        )
        if match:
            return match.group(1)
        return None

    def _extract_email_metadata(self, message: dict) -> dict:
        headers = message['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        attachments = []
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['filename']:
                    attachments.append({
                        'attachment_id': part['body'].get('attachmentId'),
                        'filename': part['filename'],
                        'mime_type': part['mimeType']
                    })
        
        return {
            'message_id': message['id'],
            'subject': subject,
            'sender': sender,
            'date': date_str,
            'attachments': attachments
        }

    def download_attachments(self, message_id: str, attachments: List[dict], transaction: Transaction) -> List[str]:
        if not self.service:
            self.authenticate()

        downloaded_files = []
        
        for attachment in attachments:
            if attachment['mime_type'] == 'application/pdf':
                try:
                    att = self.service.users().messages().attachments().get(
                        userId='me',
                        messageId=message_id,
                        id=attachment['attachment_id']
                    ).execute()
                    
                    data = att['data']
                    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    
                    safe_payee = re.sub(r'[^\w\-]', '-', transaction.payee_name.lower())
                    filename = f"{transaction.date}_{transaction.amount}_{safe_payee}_{attachment['filename']}"
                    filepath = self.attachments_path / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    
                    downloaded_files.append(str(filepath))
                except Exception as e:
                    print(f"Error downloading attachment {attachment['filename']}: {e}")
        
        return downloaded_files
