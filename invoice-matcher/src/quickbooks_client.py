import csv
import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

import requests
from dotenv import load_dotenv

from .models import Transaction

load_dotenv()

QB_BASE = 'https://quickbooks.api.intuit.com'


class QuickBooksClient:
    def __init__(self, config: dict):
        self.client_id = os.getenv('QB_CLIENT_ID')
        self.client_secret = os.getenv('QB_CLIENT_SECRET')
        self.realm_id = os.getenv('QB_REALM_ID')
        self.environment = config.get('environment', 'production')
        self.sandbox = config.get('sandbox', False)
        self.csv_path = config.get('csv_path')
        self.token = None
        
        if self.sandbox:
            global QB_BASE
            QB_BASE = 'https://sandbox-quickbooks.api.intuit.com'

    def authenticate(self):
        if self.csv_path:
            return
        
        token_file = 'credentials/qb_token.json'
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                self.token = json.load(f)
            
            if self.token.get('realm_id'):
                self.realm_id = self.token['realm_id']
            
            if self._is_token_expired():
                self._refresh_token()
        else:
            raise Exception("QuickBooks token not found. Run 'qb-auth' first.")

    def _is_token_expired(self) -> bool:
        expires_at = self.token.get('expires_at', 0)
        return datetime.now().timestamp() * 1000 >= expires_at - 60000

    def _refresh_token(self):
        url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.token['refresh_token'],
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        response = requests.post(url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        })
        
        if response.status_code == 200:
            new_token = response.json()
            new_token['expires_at'] = int(datetime.now().timestamp() * 1000) + (new_token.get('expires_in', 3600) * 1000) - 60000
            
            token_file = 'credentials/qb_token.json'
            with open(token_file, 'w') as f:
                json.dump(new_token, f, indent=2)
            
            self.token = new_token
        else:
            raise Exception(f"Failed to refresh token: {response.text}")

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.token["access_token"]}',
            'Accept': 'application/json',
        }

    def _query(self, query: str):
        url = f'{QB_BASE}/v3/company/{self.realm_id}/query'
        response = requests.get(url, headers=self._get_headers(), params={'query': query})
        response.raise_for_status()
        return response.json()

    def get_unreconciled_transactions(self, days_back: int = 90) -> List[Transaction]:
        if self.csv_path:
            return self._read_from_csv(days_back)
        
        if not self.token:
            self.authenticate()

        start_date = date.today() - timedelta(days=days_back)
        start_date_str = start_date.isoformat()

        transactions = []

        try:
            result = self._query(f"""
                SELECT * FROM Purchase
                WHERE TxnDate >= '{start_date_str}'
                ORDERBY TxnDate DESC
            """)
            
            purchases = result.get('QueryResponse', {}).get('Purchase', [])
            for purchase in purchases:
                txn = self._normalize_transaction(purchase, 'Purchase')
                if txn:
                    transactions.append(txn)
        except Exception as e:
            print(f"Error fetching purchases: {e}")

        try:
            result = self._query(f"""
                SELECT * FROM Payment
                WHERE TxnDate >= '{start_date_str}'
                ORDERBY TxnDate DESC
            """)
            
            payments = result.get('QueryResponse', {}).get('Payment', [])
            for payment in payments:
                txn = self._normalize_transaction(payment, 'Payment')
                if txn:
                    transactions.append(txn)
        except Exception as e:
            print(f"Error fetching payments: {e}")

        return transactions

    def _read_from_csv(self, days_back: int) -> List[Transaction]:
        if not os.path.exists(self.csv_path):
            raise Exception(f"CSV file not found: {self.csv_path}")
        
        transactions = []
        start_date = date.today() - timedelta(days=days_back)
        
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                date_str = row.get('Date', '')
                if not date_str:
                    continue
                
                try:
                    txn_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    continue
                
                if txn_date < start_date:
                    continue
                
                spent = row.get('Spent', '').replace('£', '').replace(',', '').strip()
                if not spent:
                    continue
                
                amount = Decimal(spent)
                description = row.get('Bank description', '')
                from_to = row.get('From/To', '')
                
                txn = Transaction(
                    id=f'csv_{i}_{txn_date.isoformat()}',
                    date=txn_date,
                    amount=amount,
                    payee_name=from_to or description[:50],
                    memo=description,
                    account_name='Bank',
                    status='unmatched'
                )
                transactions.append(txn)
        
        return transactions

    def _normalize_transaction(self, raw: dict, txn_type: str) -> Transaction:
        line = raw.get('Line', [{}])[0] if raw.get('Line') else {}
        detail = line.get('AccountBasedExpenseLineDetail') if line.get('DetailType') == 'AccountBasedExpenseLineDetail' else None
        
        description = line.get('Description') or raw.get('PrivateNote') or ''
        total_amt = abs(raw.get('TotalAmt') or line.get('Amount') or 0)
        
        payee = raw.get('EntityRef', {}).get('name') or raw.get('VendorRef', {}).get('name') or ''
        
        return Transaction(
            id=raw.get('Id'),
            date=datetime.fromisoformat(raw.get('TxnDate')).date() if raw.get('TxnDate') else date.today(),
            amount=Decimal(str(total_amt)),
            payee_name=payee,
            memo=description,
            account_name=txn_type,
            status='unmatched'
        )

    def mark_as_reconciled(self, transaction_id: str) -> bool:
        if not self.token:
            self.authenticate()

        try:
            url = f'{QB_BASE}/v3/company/{self.realm_id}/purchase/{transaction_id}'
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            purchase = response.json().get('Purchase', {})
            
            purchase['Reconciled'] = True
            
            update_url = f'{QB_BASE}/v3/company/{self.realm_id}/purchase'
            update_response = requests.post(update_url, headers=self._get_headers(), json=purchase)
            update_response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error marking transaction as reconciled: {e}")
            return False

    def upload_attachment(self, transaction_id: str, file_path: str, file_name: str, txn_type: str = 'Purchase') -> bool:
        if not self.token:
            self.authenticate()

        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            import base64
            body = {
                'file_name': file_name,
                'file_content_type': 'application/pdf',
                'file_content': base64.b64encode(file_content).decode('utf-8'),
                'attachable': {
                    'Note': 'Attached by invoice-matcher',
                    'AttachableRef': [{
                        'EntityRef': {'type': txn_type, 'value': transaction_id},
                    }],
                },
            }
            
            url = f'{QB_BASE}/v3/company/{self.realm_id}/upload'
            response = requests.post(url, headers=self._get_headers(), json=body)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error uploading attachment: {e}")
            return False

    def get_transaction_with_category(self, transaction_id: str, txn_type: str = 'Purchase') -> dict:
        if not self.token:
            self.authenticate()

        try:
            url = f'{QB_BASE}/v3/company/{self.realm_id}/{txn_type.lower()}/{transaction_id}'
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get(txn_type, {})
        except Exception as e:
            print(f"Error fetching transaction: {e}")
            return {}

    def update_transaction_category(self, transaction_id: str, account_id: str, txn_type: str = 'Purchase') -> bool:
        if not self.token:
            self.authenticate()

        try:
            url = f'{QB_BASE}/v3/company/{self.realm_id}/{txn_type.lower()}/{transaction_id}'
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            transaction = response.json().get(txn_type, {})
            
            if 'Line' in transaction and transaction['Line']:
                for line in transaction['Line']:
                    if 'AccountBasedExpenseLineDetail' in line:
                        line['AccountBasedExpenseLineDetail']['AccountRef'] = {'value': account_id}
            
            update_url = f'{QB_BASE}/v3/company/{self.realm_id}/{txn_type.lower()}'
            update_response = requests.post(update_url, headers=self._get_headers(), json=transaction)
            update_response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error updating category: {e}")
            return False

    def update_transaction_tax_code(self, transaction_id: str, tax_code: str, txn_type: str = 'Purchase') -> bool:
        if not self.token:
            self.authenticate()

        try:
            url = f'{QB_BASE}/v3/company/{self.realm_id}/{txn_type.lower()}/{transaction_id}'
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            transaction = response.json().get(txn_type, {})
            
            if 'Line' in transaction and transaction['Line']:
                for line in transaction['Line']:
                    if 'DetailType' in line and line['DetailType'] == 'AccountBasedExpenseLineDetail':
                        if 'AccountBasedExpenseLineDetail' in line:
                            line['AccountBasedExpenseLineDetail']['TaxCodeRef'] = {'value': tax_code}
            
            update_url = f'{QB_BASE}/v3/company/{self.realm_id}/{txn_type.lower()}'
            update_response = requests.post(update_url, headers=self._get_headers(), json=transaction)
            update_response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Error updating tax code: {e}")
            return False

    def get_accounts(self) -> List[dict]:
        if not self.token:
            self.authenticate()

        try:
            result = self._query("SELECT * FROM Account WHERE AccountType IN ('Expense', 'Cost of Goods Sold') ORDERBY Name")
            return result.get('QueryResponse', {}).get('Account', [])
        except Exception as e:
            print(f"Error fetching accounts: {e}")
            return []

    def create_categorized_expense(self, txn_date: str, amount: float, vendor_name: str, account_id: str, tax_code: str = 'T1', attachment_path: str = None) -> dict:
        if not self.token:
            self.authenticate()

        try:
            vendors = self._query(f"SELECT * FROM Vendor WHERE DisplayName = '{vendor_name}'")
            vendor_list = vendors.get('QueryResponse', {}).get('Vendor', [])
            
            if vendor_list:
                vendor_id = vendor_list[0]['Id']
            else:
                vendor_id = None
            
            expense = {
                'TxnDate': txn_date,
                'PaymentType': 'Cash',
                'AccountRef': {'value': '1'},
                'TotalAmt': amount,
                'Line': [{
                    'Amount': amount,
                    'DetailType': 'AccountBasedExpenseLineDetail',
                    'AccountBasedExpenseLineDetail': {
                        'AccountRef': {'value': account_id},
                        'TaxCodeRef': {'value': tax_code},
                    },
                }],
            }
            
            if vendor_id:
                expense['EntityRef'] = {'type': 'Vendor', 'value': vendor_id}
            
            url = f'{QB_BASE}/v3/company/{self.realm_id}/purchase'
            response = requests.post(url, headers=self._get_headers(), json=expense)
            response.raise_for_status()
            
            result = response.json()
            purchase_id = result.get('Purchase', {}).get('Id')
            
            if attachment_path and os.path.exists(attachment_path) and purchase_id:
                self.upload_attachment(purchase_id, attachment_path, os.path.basename(attachment_path), 'Purchase')
            
            return result
        except Exception as e:
            print(f"Error creating expense: {e}")
            return None
