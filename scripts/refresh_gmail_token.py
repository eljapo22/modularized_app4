"""
Script to refresh Gmail OAuth2 token
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json
from pathlib import Path

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def refresh_token(credentials_path: str):
    """Refresh Gmail OAuth token"""
    creds = None
    # Save in the app directory's .streamlit folder
    streamlit_dir = Path('../app/.streamlit')
    token_path = streamlit_dir / 'secrets.toml'

    # Create .streamlit directory if it doesn't exist
    streamlit_dir.mkdir(parents=True, exist_ok=True)

    # Load client config
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Get token info
    token_info = {
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'refresh_token': creds.refresh_token,
        'token_uri': 'https://oauth2.googleapis.com/token'
    }

    # Create secrets.toml content with proper JSON escaping
    token_json = json.dumps(token_info, separators=(',', ':'))  # Compact JSON
    secrets_content = f"""# Gmail configuration
GMAIL_TOKEN = '{token_json}'
DEFAULT_RECIPIENT = "jhnapo2213@gmail.com"
"""

    # Save to .streamlit/secrets.toml
    with open(token_path, 'w') as f:
        f.write(secrets_content)

    print(f"\nToken refreshed and saved to {token_path.absolute()}")
    
    # Verify the token was saved correctly
    try:
        with open(token_path, 'r') as f:
            saved_content = f.read()
            if 'GMAIL_TOKEN' in saved_content and 'DEFAULT_RECIPIENT' in saved_content:
                print("Token file created successfully!")
            else:
                print("Warning: Token file may not be properly formatted")
    except Exception as e:
        print(f"Error verifying token file: {str(e)}")

if __name__ == "__main__":
    # Get credentials file path
    credentials_file = input("Enter the path to your credentials.json file: ")
    if not os.path.exists(credentials_file):
        print(f"Error: File not found: {credentials_file}")
        exit(1)

    refresh_token(credentials_file)
