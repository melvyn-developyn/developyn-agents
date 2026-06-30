"""
QuickBooks Online - Banking page web client.

Fetches the "For Review" bank-feed transactions via Intuit's internal
accounting-txn-svcs API, authenticated with browser session cookies.

Session credentials are stored in credentials/qbo_web_session.json
(copied from "Copy as cURL" in DevTools on the /app/banking page).

To refresh: see AGENTS.md "Refreshing web session".
"""

import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import List

import requests

from .models import Transaction

QBO_TXN_SVCS = 'https://accounting-txn-svcs.api.intuit.com/v1'
QBO_WEB_HOST = 'https://qbo.intuit.com'

SESSION_FILE = 'credentials/qbo_web_session.json'


class QBOWebClient:
    """
    Wraps the internal Intuit banking endpoint that powers the
    "For Review" list on qbo.intuit.com/app/banking.
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.realm_id = os.getenv('QB_REALM_ID') or self.config.get('realm_id')
        self.accounts_to_scan = self._expand_account_ids()
        self.session_data = None

    def _expand_account_ids(self) -> List[str]:
        """
        Accepts a single int, list, or comma-separated string under
        config['qbo_web']['account_ids']. Defaults to ['57'].
        """
        raw = self.config.get('qbo_web', {}).get('account_ids', '57')
        if isinstance(raw, int):
            return [str(raw)]
        if isinstance(raw, list):
            return [str(a) for a in raw]
        return [s.strip() for s in str(raw).split(',') if s.strip()] or ['57']

    def authenticate(self) -> bool:
        if not os.path.exists(SESSION_FILE):
            raise FileNotFoundError(
                f"Missing {SESSION_FILE}. Run `python3 -m src.cli web-auth` and "
                "follow the prompts, or see AGENTS.md 'Refreshing web session'."
            )
        with open(SESSION_FILE, 'r') as f:
            self.session_data = json.load(f)
        # The session's realm_id is authoritative (production company);
        # it differs from QB_REALM_ID in .env which may point at a sandbox.
        realm = self.session_data.get('realm_id')
        if realm:
            self.realm_id = realm
        return True

    def fetch_for_review_transactions(self, account_id: str = None) -> List[Transaction]:
        """Fetches PENDING ('For Review') transactions for the given account."""
        if not self.session_data:
            self.authenticate()

        account_id = account_id or self.accounts_to_scan[0]
        url = f'{QBO_TXN_SVCS}/company/{self.realm_id}/banking/getTransactions'
        params = {
            'accountId': account_id,
            'sort': '-txnDate',
            'reviewState': 'PENDING',
            'ignoreMatching': 'false',
        }

        response = requests.get(url, params=params, headers=self._build_headers(session=self.session_data))
        response.raise_for_status()
        data = response.json()

        items = data.get('items', [])
        return [self._normalize(item) for item in items]

    def fetch_all_for_review(self) -> List[Transaction]:
        """Fetches PENDING transactions across every configured account_id."""
        if not self.session_data:
            self.authenticate()

        all_txns: List[Transaction] = []
        for account_id in self.accounts_to_scan:
            url = f'{QBO_TXN_SVCS}/company/{self.realm_id}/banking/getTransactions'
            params = {
                'accountId': account_id,
                'sort': '-txnDate',
                'reviewState': 'PENDING',
                'ignoreMatching': 'false',
            }
            response = requests.get(
                url, params=params,
                headers=self._build_headers(self.session_data),
            )
            if response.status_code == 401:
                raise Exception(
                    "Web session expired (401). Re-run: "
                    "pbpaste | python3 -m src.cli web-auth"
                )
            if response.status_code != 200:
                raise Exception(
                    f"QBO banking API error ({response.status_code}): "
                    f"{response.text[:200]}"
                )
            for item in response.json().get('items', []):
                all_txns.append(self._normalize(item))
        return all_txns

    def _normalize(self, raw: dict) -> Transaction:
        amount_raw = raw.get('amount', 0) or 0
        amount = abs(Decimal(str(amount_raw)))

        olb_date = raw.get('olbTxnDate', '')
        if olb_date:
            try:
                txn_date = datetime.fromisoformat(olb_date).date()
            except ValueError:
                txn_date = datetime.now().date()
        else:
            txn_date = datetime.now().date()

        payee_name = (
            raw.get('merchantName')
            or raw.get('payeeDescription')
            or ''
        )

        # Prefer origDescription — it has the full untruncated bank text
        # including foreign currency amounts (DKK 143.20, USD 18.94)
        # and domain names (anoma.ly, getmerlin.in)
        description = (
            raw.get('origDescription')
            or raw.get('description')
            or ''
        )

        return Transaction(
            id=f"web_{raw.get('olbTxnId', raw.get('id',''))}",
            date=txn_date,
            amount=amount,
            payee_name=payee_name,
            memo=description,
            account_name='Bank (For Review)',
            status='unmatched',
        )

    def _build_headers(self, session: dict) -> dict:
        """Reconstruct the headers Intuit's banking endpoint expects."""
        apikey = session.get('apikey')
        realm = self.realm_id or session.get('realm_id')
        user_id = session.get('user_id', '')

        auth = (
            f'Intuit_APIKey '
            f'intuit_apikey={apikey},'
            f'intuit_apikey_version=1.0,'
            f'intuit_realmid={realm},'
            f'intuit_userid={user_id}'
        ) if apikey else None

        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.9',
            'authorization': auth,
            'authtype': 'browser_auth',
            'content-type': 'application/json',
            'origin': QBO_WEB_HOST,
            'referer': f'{QBO_WEB_HOST}/',
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/149.0.0.0 Safari/537.36'
            ),
        }

        if realm:
            headers['intuit-company-id'] = realm
        headers['intuit_appid'] = 'Intuit.sbe.salsa.platform'

        if session.get('csrf_token'):
            headers['csrftoken'] = session['csrf_token']
        if session.get('x_csrf_token'):
            headers['x-csrf-token'] = session['x_csrf_token']

        cookie_pairs = session.get('cookies') or {}
        if cookie_pairs:
            headers['Cookie'] = '; '.join(
                f'{k}={v}' for k, v in cookie_pairs.items()
            )
        return headers


def parse_curl_to_session(curl_text: str) -> dict:
    """
    Parse a "Copy as cURL (bash)" string from Chrome DevTools
    (the getTransactions request) into a session dict.
    """
    session = {
        'realm_id': None,
        'user_id': None,
        'apikey': None,
        'csrf_token': None,
        'x_csrf_token': None,
        'cookies': {},
        'created_at': datetime.now().isoformat(),
    }

    # Cookies from -b '...'
    cookie_match = re.search(r"-b\s+'(.*?)'", curl_text, re.S)
    if cookie_match:
        cookie_str = cookie_match.group(1)
        for pair in cookie_str.split(';'):
            pair = pair.strip()
            if '=' in pair:
                k, v = pair.split('=', 1)
                session['cookies'][k.strip()] = v.strip()

    # apikey (appears twice: as -H 'apikey: ...' and inside authorization)
    apikey_match = re.search(r"-H\s+'apikey:\s*([^']+)'", curl_text)
    if apikey_match:
        session['apikey'] = apikey_match.group(1).strip()

    # Authorization header carries realmid + userid
    auth_match = re.search(
        r"-H\s+'authorization:\s*Intuit_APIKey\s+(.*?)'",
        curl_text, re.I
    )
    if auth_match:
        auth_body = auth_match.group(1)
        realm_match = re.search(r'intuit_realmid=(\d+)', auth_body)
        user_match = re.search(r'intuit_userid=(\d+)', auth_body)
        if realm_match:
            session['realm_id'] = realm_match.group(1)
        if user_match:
            session['user_id'] = user_match.group(1)

    # CSRF tokens
    csrf_match = re.search(r"-H\s+'csrftoken:\s*([^']+)'", curl_text)
    if csrf_match:
        session['csrf_token'] = csrf_match.group(1).strip()

    xcsrf_match = re.search(r"-H\s+'x-csrf-token:\s*([^']+)'", curl_text)
    if xcsrf_match:
        session['x_csrf_token'] = xcsrf_match.group(1).strip()

    # Realm can also appear in URL
    url_match = re.search(r"curl\s+'https://[^/]+/v1/company/(\d+)/", curl_text)
    if url_match and not session['realm_id']:
        session['realm_id'] = url_match.group(1)

    return session