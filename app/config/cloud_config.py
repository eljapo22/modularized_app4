"""
Cloud-specific configuration for the Transformer Loading Analysis Application
"""

import os
import streamlit as st
from pathlib import Path

# Gmail API configuration for cloud
GMAIL_CREDENTIALS = st.secrets["GMAIL_CREDENTIALS"]
GMAIL_TOKEN = st.secrets["GMAIL_TOKEN"]
DEFAULT_RECIPIENT = st.secrets.get("DEFAULT_RECIPIENT", "jhnapo2213@gmail.com")

# Data paths
def get_cloud_data_path():
    """Get the base path for data files in cloud environment"""
    return Path(__file__).parent.parent.parent / "processed_data"

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
