"""
Cloud-specific configuration settings
"""

import streamlit as st
import json

class GmailConfig:
    @staticmethod
    def get_token():
        """Get and parse Gmail token from Streamlit secrets"""
        try:
            token = st.secrets["GMAIL_TOKEN"]
            return json.loads(token) if isinstance(token, str) else token
        except Exception as e:
            st.error(f"Error loading Gmail token: {str(e)}")
            return None
            
    @staticmethod
    def get_recipient():
        """Get default recipient from Streamlit secrets"""
        try:
            return st.secrets["DEFAULT_RECIPIENT"]
        except Exception as e:
            st.error(f"Error loading default recipient: {str(e)}")
            return None

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
