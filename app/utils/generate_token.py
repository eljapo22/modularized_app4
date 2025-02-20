"""
Utility script to generate a fresh Gmail API token
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_token():
    """Generate a fresh Gmail API token using OAuth flow"""
    config_dir = Path(__file__).parent.parent / 'config'
    credentials_path = config_dir / 'credentials.json'
    token_path = config_dir / 'token.json'
    
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {credentials_path}\n"
            "Please download OAuth credentials from Google Cloud Console and save as credentials.json"
        )
    
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save token
    token_json = creds.to_json()
    with open(token_path, 'w') as f:
        f.write(token_json)
        
    print(f"\nToken successfully generated and saved to {token_path}")
    print("\nFor Streamlit Cloud deployment, add this to your secrets.toml:")
    print("\n[secrets]")
    print(f'GMAIL_TOKEN = {json.dumps(json.loads(token_json))}')

if __name__ == '__main__':
    try:
        generate_token()
    except Exception as e:
        print(f"Error generating token: {str(e)}")
