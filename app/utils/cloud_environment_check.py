"""
Utility functions to validate and debug cloud environment settings
"""

import os
import json
import streamlit as st
from typing import Dict, Optional, List, Tuple
from pathlib import Path

def validate_cloud_secrets() -> Tuple[bool, List[str]]:
    """
    Validate that all required Streamlit secrets are present and properly formatted.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list of error messages)
    """
    errors = []
    
    # Check if we're actually in cloud environment
    if not (os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING')):
        return False, ["Not running in Streamlit Cloud environment"]
    
    # Required secrets
    required_secrets = {
        "GMAIL_TOKEN": "Gmail API token for sending alerts",
        "DEFAULT_RECIPIENT": "Default email recipient for alerts",
        "MOTHERDUCK_TOKEN": "MotherDuck database access token"
    }
    
    # Optional secrets
    optional_secrets = {}
    
    # Check each required secret
    for secret_name, description in required_secrets.items():
        if secret_name not in st.secrets:
            errors.append(f"Missing required secret: {secret_name} ({description})")
            continue
            
        # Special validation for GMAIL_TOKEN
        if secret_name == "GMAIL_TOKEN":
            token = st.secrets[secret_name]
            if isinstance(token, str):
                try:
                    token_dict = json.loads(token)
                    required_fields = ["client_id", "client_secret", "refresh_token", "token_uri"]
                    missing_fields = [field for field in required_fields if field not in token_dict]
                    if missing_fields:
                        errors.append(f"GMAIL_TOKEN missing required fields: {', '.join(missing_fields)}")
                except json.JSONDecodeError:
                    errors.append("GMAIL_TOKEN is not valid JSON")
            else:
                errors.append("GMAIL_TOKEN must be a JSON string")
    
    # Check optional secrets and log warnings
    for secret_name, description in optional_secrets.items():
        if secret_name not in st.secrets:
            st.info(f"Optional secret not set: {secret_name} ({description})")
    
    return len(errors) == 0, errors

def debug_cloud_environment() -> Dict[str, str]:
    """
    Gather debug information about the cloud environment.
    
    Returns:
        Dict[str, str]: Dictionary of debug information
    """
    debug_info = {
        "Environment": "Streamlit Cloud" if (os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING')) else "Local",
        "Python Path": str(Path(__file__).resolve()),
        "Available Secrets": ", ".join(st.secrets.keys()) if hasattr(st, 'secrets') else "No secrets available",
        "Environment Variables": ", ".join(
            [f"{k}={'[HIDDEN]' if 'TOKEN' in k or 'SECRET' in k else v}" 
             for k, v in os.environ.items() 
             if k.startswith(('STREAMLIT_', 'USE_'))]
        )
    }
    
    # Check Gmail token format
    if "GMAIL_TOKEN" in st.secrets:
        token = st.secrets["GMAIL_TOKEN"]
        if isinstance(token, str):
            try:
                token_dict = json.loads(token)
                debug_info["Gmail Token Format"] = "Valid JSON with fields: " + ", ".join(token_dict.keys())
            except json.JSONDecodeError:
                debug_info["Gmail Token Format"] = "Invalid JSON"
        else:
            debug_info["Gmail Token Format"] = f"Unexpected type: {type(token)}"
    
    return debug_info

def display_environment_status():
    """Display environment status in the Streamlit UI"""
    st.write("### Cloud Environment Status")
    
    # Validate environment
    is_valid, errors = validate_cloud_secrets()
    
    if is_valid:
        st.success("✅ Cloud environment is properly configured")
    else:
        st.error("❌ Cloud environment has configuration issues")
        for error in errors:
            st.warning(error)
    
    # Show debug information
    st.markdown("### Debug Information")
    debug_info = debug_cloud_environment()
    for key, value in debug_info.items():
        st.text(f"{key}: {value}")
        
    st.info("""
    If you're seeing issues:
    1. Check that all required secrets are set in Streamlit Cloud
    2. Verify the Gmail token format
    3. Ensure environment variables are correctly set
    """)

def is_cloud_ready() -> bool:
    """
    Quick check if cloud environment is ready for use.
    
    Returns:
        bool: True if cloud environment is properly configured
    """
    is_valid, _ = validate_cloud_secrets()
    return is_valid and (os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING')) is not None
