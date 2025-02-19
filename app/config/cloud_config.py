"""
Configuration for cloud services with local development support
"""
import os
import json
import streamlit as st
from typing import Optional, Dict, Any

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def use_motherduck() -> bool:
    """Check if MotherDuck should be used"""
    # Always use MotherDuck if token is available
    return bool(st.secrets.get('MOTHERDUCK_TOKEN'))

def is_local_dev() -> bool:
    """Check if running in local development mode"""
    return not (os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING'))

class GmailConfig:
    """Configuration for Gmail service with local development support"""
    
    @staticmethod
    def get_token() -> Optional[Dict[str, Any]]:
        """Get Gmail token with local development fallback"""
        try:
            if hasattr(st, 'secrets') and 'GMAIL_TOKEN' in st.secrets:
                token_str = st.secrets['GMAIL_TOKEN']
                if isinstance(token_str, str):
                    return json.loads(token_str)
                return token_str
        except Exception as e:
            st.error(f"Failed to get Gmail token: {str(e)}")
        return None
        
    @staticmethod
    def get_recipient() -> Optional[str]:
        """Get default email recipient"""
        if hasattr(st, 'secrets'):
            return st.secrets.get('DEFAULT_RECIPIENT')
        return None
