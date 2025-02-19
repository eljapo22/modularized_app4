"""
Configuration for cloud services with local development support
"""
import os
import json
import streamlit as st
from typing import Optional, Dict, Any

def use_motherduck() -> bool:
    """Check if MotherDuck should be used"""
    # Always use MotherDuck if token is available
    return bool(st.secrets.get('MOTHERDUCK_TOKEN'))

def is_local_dev() -> bool:
    """Check if running in local development mode"""
    return not (os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING'))

class EmailConfig:
    """Configuration for email service with local development support"""
    
    @staticmethod
    def get_smtp_settings() -> Dict[str, Any]:
        """Get SMTP settings with local development fallback"""
        if is_local_dev():
            # Local development settings
            return {
                'host': 'localhost',
                'port': 1025,  # Default port for Python's debugging server
                'username': None,
                'password': None
            }
            
        # Production settings
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets'):
                settings = {}
                
                # Get SMTP host
                if 'SMTP_HOST' in st.secrets:
                    settings['host'] = st.secrets['SMTP_HOST']
                else:
                    settings['host'] = 'email-smtp.us-east-1.amazonaws.com'
                    
                # Get SMTP port
                if 'SMTP_PORT' in st.secrets:
                    settings['port'] = st.secrets['SMTP_PORT']
                else:
                    settings['port'] = 587
                    
                # Get credentials
                if 'SMTP_USERNAME' in st.secrets and 'SMTP_PASSWORD' in st.secrets:
                    settings['username'] = st.secrets['SMTP_USERNAME']
                    settings['password'] = st.secrets['SMTP_PASSWORD']
                else:
                    # Fall back to environment variables
                    settings['username'] = os.getenv('SMTP_USERNAME')
                    settings['password'] = os.getenv('SMTP_PASSWORD')
                    
                if settings.get('username') and settings.get('password'):
                    return settings
            
            st.warning("SMTP credentials not found. Using local development mode.")
            return EmailConfig.get_smtp_settings()  # Fallback to local settings
            
        except Exception as e:
            st.error(f"Error getting SMTP settings: {str(e)}")
            return EmailConfig.get_smtp_settings()  # Fallback to local settings
            
    @staticmethod
    def get_sender() -> str:
        """Get sender email with local development fallback"""
        if is_local_dev():
            return "dev@localhost"
            
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'SENDER_EMAIL' in st.secrets:
                return st.secrets['SENDER_EMAIL']
                
            # Fall back to environment variable
            sender = os.getenv('SENDER_EMAIL')
            if sender:
                return sender
                
            # Fallback to local development
            st.warning("Sender email not found. Using local development address.")
            return EmailConfig.get_sender()
            
        except Exception as e:
            st.error(f"Error getting sender email: {str(e)}")
            return EmailConfig.get_sender()
            
    @staticmethod
    def get_recipient() -> str:
        """Get default recipient with local development fallback"""
        if is_local_dev():
            return "test@localhost"
            
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'DEFAULT_RECIPIENT' in st.secrets:
                return st.secrets['DEFAULT_RECIPIENT']
                
            # Fall back to environment variable
            recipient = os.getenv('DEFAULT_RECIPIENT')
            if recipient:
                return recipient
                
            # Fallback to local development
            st.warning("Default recipient not found. Using local development address.")
            return EmailConfig.get_recipient()
            
        except Exception as e:
            st.error(f"Error getting default recipient: {str(e)}")
            return EmailConfig.get_recipient()
            
    @staticmethod
    def is_configured() -> bool:
        """Check if email configuration is complete"""
        # Always return True for local development
        if is_local_dev():
            return True
            
        settings = EmailConfig.get_smtp_settings()
        return (
            settings.get('username') is not None and
            settings.get('password') is not None and
            EmailConfig.get_sender() is not None and
            EmailConfig.get_recipient() is not None
        )
