"""
Cloud-specific configuration settings
"""

import streamlit as st
import json

# Gmail configuration
try:
    # Get token from secrets and ensure it's a dictionary
    token_info = st.secrets["GMAIL_TOKEN"]
    if isinstance(token_info, str):
        token_info = json.loads(token_info)
    
    # Get default recipient
    DEFAULT_RECIPIENT = st.secrets["DEFAULT_RECIPIENT"]
    
    # These paths should be None in cloud environment
    CREDENTIALS_PATH = None
    TOKEN_PATH = None
    
except Exception as e:
    st.error(f"Error loading Gmail configuration: {str(e)}")
    token_info = None
    DEFAULT_RECIPIENT = None
    CREDENTIALS_PATH = None
    TOKEN_PATH = None

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
