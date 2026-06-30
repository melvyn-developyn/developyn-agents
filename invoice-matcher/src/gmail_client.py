import base64
import json
import os
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClient:
    """Minimal Gmail client: authenticate, search, read emails, download attachments."""

    def __init__(self, config: dict):
        self.credentials_file = config.get('credentials_file', 'credentials/gmail_credentials.json')
        self.token_file = config.get('token_file', 'credentials/gmail_token.json')
        self.attachments_path = Path(config.get('attachments_path', 'data/attachments/'))
        self.attachments_path.mkdir(parents=True, exist_ok=True)
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

    def search(self, query: str, max_results: int = 20) -> List[dict]:
        """Search Gmail and return message summaries.

        Each result dict: {id, threadId, subject, from, date, snippet,
                           has_attachment, attachment_filenames}
        """
        if not self.service:
            self.authenticate()

        results = self.service.users().messages().list(
            userId='me', q=query, maxResults=max_results
        ).execute()

        summaries = []
        for msg_info in results.get('messages', []):
            msg = self.service.users().messages().get(
                userId='me', id=msg_info['id'], format='full'
            ).execute()

            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            has_attachment = False
            attachment_filenames = []
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part.get('filename'):
                        has_attachment = True
                        attachment_filenames.append(part['filename'])

            summaries.append({
                'id': msg['id'],
                'threadId': msg['threadId'],
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'date': headers.get('Date', ''),
                'snippet': msg.get('snippet', ''),
                'has_attachment': has_attachment,
                'attachment_filenames': attachment_filenames,
            })

        return summaries

    def get_message(self, message_id: str) -> dict:
        """Get full message with payload including text parts."""
        if not self.service:
            self.authenticate()

        return self.service.users().messages().get(
            userId='me', id=message_id, format='full'
        ).execute()

    def get_body_text(self, message_id: str) -> Optional[str]:
        """Extract plain text body from a message."""
        msg = self.get_message(message_id)
        payload = msg['payload']

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8', errors='replace')
        elif payload.get('mimeType') == 'text/plain':
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8', errors='replace')

        return None

    def download_attachment(self, message_id: str, attachment_id: str, filename: str) -> str:
        """Download a single attachment. Returns the local file path."""
        if not self.service:
            self.authenticate()

        att = self.service.users().messages().attachments().get(
            userId='me', messageId=message_id, id=attachment_id
        ).execute()

        file_data = base64.urlsafe_b64decode(att['data'].encode('UTF-8'))
        filepath = self.attachments_path / filename

        with open(filepath, 'wb') as f:
            f.write(file_data)

        return str(filepath)

    def get_attachments(self, message_id: str) -> List[dict]:
        """List all attachments for a message. Each: {attachment_id, filename, mime_type}."""
        msg = self.get_message(message_id)
        attachments = []

        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part.get('filename') and part.get('body', {}).get('attachmentId'):
                    attachments.append({
                        'attachment_id': part['body']['attachmentId'],
                        'filename': part['filename'],
                        'mime_type': part['mimeType'],
                    })

        return attachments

    def download_all_attachments(self, message_id: str, prefix: str = '') -> List[str]:
        """Download all PDF attachments from a message. Returns list of local paths."""
        paths = []
        for att in self.get_attachments(message_id):
            if att['mime_type'] == 'application/pdf':
                fn = f"{prefix}_{att['filename']}" if prefix else att['filename']
                path = self.download_attachment(message_id, att['attachment_id'], fn)
                paths.append(path)
        return paths
