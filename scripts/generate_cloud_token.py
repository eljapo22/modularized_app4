"""
Generate a fresh Gmail API token for Streamlit Cloud
"""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def generate_cloud_token():
    """Generate a fresh token and format it for Streamlit Cloud"""
    creds = None
    credentials_path = Path(__file__).parent.parent / 'app' / 'config' / 'credentials.json'
    token_path = Path(__file__).parent.parent / 'app' / 'config' / 'token.json'

    # Load existing token if present
    if token_path.exists():
        with open(token_path, 'r') as token_file:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

    # Format token for Streamlit Cloud
    token_info = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    # Save formatted token
    cloud_token_path = Path(__file__).parent.parent / 'app' / 'config' / 'cloud_token.json'
    with open(cloud_token_path, 'w') as f:
        json.dump(token_info, f, indent=2)
    
    print(f"\nCloud token generated at: {cloud_token_path}")
    print("\nToken contents (copy this to Streamlit Cloud secrets):")
    print(json.dumps(token_info))

if __name__ == '__main__':
    generate_cloud_token()
