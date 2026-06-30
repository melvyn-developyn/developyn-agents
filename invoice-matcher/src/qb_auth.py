import json
import os
import http.server
import threading
import urllib.parse
import secrets
import webbrowser
from datetime import datetime

import requests


def authenticate_quickbooks():
    client_id = os.getenv('QB_CLIENT_ID')
    client_secret = os.getenv('QB_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: QB_CLIENT_ID and QB_CLIENT_SECRET must be set in .env")
        return False
    
    redirect_uri = 'http://localhost:3001/callback'
    state = secrets.token_urlsafe(16)
    
    scopes = [
        'com.intuit.quickbooks.accounting',
        'openid',
        'profile',
        'email',
    ]
    
    auth_url = (
        f'https://appcenter.intuit.com/connect/oauth2?'
        f'client_id={client_id}'
        f'&response_type=code'
        f'&scope={urllib.parse.quote(" ".join(scopes))}'
        f'&redirect_uri={urllib.parse.quote(redirect_uri, safe="")}'
        f'&state={state}'
    )
    
    print("\n=== QuickBooks OAuth ===")
    print("Opening browser to connect to QuickBooks...")
    print("If the browser doesn't open, visit this URL:")
    print(auth_url)
    print()
    
    auth_code = None
    received_state = None
    realm_id = None
    
    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code, received_state, realm_id
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            
            if 'code' in params and 'state' in params:
                auth_code = params['code'][0]
                received_state = params['state'][0]
                realm_id = params.get('realmId', [None])[0]
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'<h1>QuickBooks connected!</h1><p>You can close this tab.</p>')
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                msg = urllib.parse.parse_qs(parsed.query).get('error', ['unknown'])[0]
                self.wfile.write(f'<h1>OAuth error</h1><p>{msg}</p>'.encode())
            
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        
        def log_message(self, format, *args):
            pass
    
    server = http.server.HTTPServer(('localhost', 3001), CallbackHandler)
    webbrowser.open(auth_url)
    server.serve_forever()
    
    if received_state != state:
        print("Error: State mismatch. Possible CSRF attack.")
        return False
    
    if not auth_code:
        print("Error: No authorization code received.")
        return False
    
    print("\nExchanging authorization code for tokens...")
    
    token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    response = requests.post(token_url, data=data, headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    })
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
    
    token_data = response.json()
    token_data['expires_at'] = int(datetime.now().timestamp() * 1000) + (token_data.get('expires_in', 3600) * 1000) - 60000
    token_data['realm_id'] = realm_id
    
    os.makedirs('credentials', exist_ok=True)
    with open('credentials/qb_token.json', 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print(f"\n✓ QuickBooks connected!")
    print(f"  Company ID (realmId): {realm_id}")
    print(f"  Token saved to credentials/qb_token.json")
    
    if realm_id:
        env_path = '.env'
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('QB_REALM_ID='):
                    lines[i] = f'QB_REALM_ID={realm_id}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'QB_REALM_ID={realm_id}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            print(f"  Updated .env with QB_REALM_ID={realm_id}")
    
    return True


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    authenticate_quickbooks()
