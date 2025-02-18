"""
Cloud-specific configuration settings
"""

import os
import streamlit as st
from pathlib import Path
import json

# Gmail configuration
try:
    token_info = st.secrets["GMAIL_TOKEN"]
    if isinstance(token_info, str):
        token_info = json.loads(token_info)
    DEFAULT_RECIPIENT = st.secrets["DEFAULT_RECIPIENT"]
except Exception as e:
    st.error(f"Error loading Gmail configuration: {str(e)}")
    token_info = None
    DEFAULT_RECIPIENT = None

# Data paths
def get_cloud_data_path():
    """Get the base path for data files in cloud environment"""
    return Path(__file__).parent.parent.parent / "processed_data"

DATA_DIR = "/mount/src/modularized_app4/data"
EXCEL_FILE = os.path.join(DATA_DIR, "transformer_data.xlsx")

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
