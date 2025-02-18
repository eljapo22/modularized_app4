"""
Cloud-specific configuration for the Transformer Loading Analysis Application
"""

import os
from pathlib import Path

# Gmail API configuration for cloud
GMAIL_CREDENTIALS = os.getenv('GMAIL_CREDENTIALS')
GMAIL_TOKEN = os.getenv('GMAIL_TOKEN')
DEFAULT_RECIPIENT = os.getenv('DEFAULT_RECIPIENT', 'jhnapo2213@gmail.com')

# Data paths
def get_cloud_data_path():
    """Get the base path for data files in cloud environment"""
    return Path(__file__).parent.parent.parent / "processed_data"

# Scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
