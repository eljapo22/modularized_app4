"""
Cloud-specific configuration settings
"""

import os
import streamlit as st
from pathlib import Path

# Gmail configuration
GMAIL_CREDENTIALS = st.secrets.get("GMAIL_CREDENTIALS", None)
GMAIL_TOKEN = st.secrets.get("GMAIL_TOKEN", None)
DEFAULT_RECIPIENT = st.secrets.get("DEFAULT_RECIPIENT", None)

# Data paths
def get_cloud_data_path():
    """Get the base path for data files in cloud environment"""
    return Path(__file__).parent.parent.parent / "processed_data"

DATA_DIR = "/mount/src/modularized_app4/data"
EXCEL_FILE = os.path.join(DATA_DIR, "transformer_data.xlsx")

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
