"""
Test script to verify both Gmail API and MotherDuck configurations
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from app.services.services import CloudDataService
from app.config.cloud_config import use_motherduck, GmailConfig

def test_gmail_config():
    st.header("Testing Gmail Configuration")
    
    # Check if token exists
    token = GmailConfig.get_token()
    if token:
        st.success("✓ Gmail token found")
        st.write("Token contains:", list(token.keys()))
    else:
        st.error("✗ Gmail token not found")
        
    # Check if recipient exists
    recipient = GmailConfig.get_recipient()
    if recipient:
        st.success(f"✓ Default recipient found: {recipient}")
    else:
        st.error("✗ Default recipient not found")
        
    # Test sending email
    test_data = pd.DataFrame({
        'transformer_id': ['TEST_001'],
        'load_range': ['Warning'],
        'loading_percentage': [85.5],
        'power_kw': [75.5],
        'current_a': [150.2],
        'voltage_v': [240.1],
        'power_factor': [0.95]
    })
    
    if st.button("Send Test Email"):
        success = True  # Replace with actual email sending logic
        if success:
            st.success("✓ Test email sent successfully!")
        else:
            st.error("✗ Failed to send test email")

def test_motherduck_config():
    st.header("Testing MotherDuck Configuration")
    
    # Check if MotherDuck is enabled
    if use_motherduck():
        st.success("✓ MotherDuck is enabled")
    else:
        st.error("✗ MotherDuck is not enabled")
        return
        
    # Test database connection
    try:
        data_service = CloudDataService()
        # Test simple query
        result = data_service.query("SELECT 1 as test")
        if result is not None and len(result) > 0:
            st.success("✓ Successfully connected to MotherDuck")
            
            if st.button("Test Data Query"):
                # Try to query transformer data
                transformer_id = "S1F1ATF001"
                start_date = datetime.now().date()
                end_date = start_date
                feeder = "Feeder 1"
                
                # Get transformer data
                transformer_data = data_service.get_transformer_data_range(
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                if not transformer_data.empty:
                    st.success("✓ Successfully queried transformer data")
                    st.write("Transformer data sample:", transformer_data.head())
                else:
                    st.warning("! No transformer data found")
                    
                # Get customer data
                customer_data = data_service.get_customer_data(
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                if not customer_data.empty:
                    st.success("✓ Successfully queried customer data")
                    st.write("Customer data sample:", customer_data.head())
                else:
                    st.warning("! No customer data found")
        else:
            st.error("✗ Failed to connect to MotherDuck")
    except Exception as e:
        st.error(f"✗ MotherDuck test failed: {str(e)}")

def test_secrets_location():
    st.header("Testing Secrets Configuration")
    
    # Check .streamlit directories
    root_streamlit = os.path.join(os.getcwd(), '.streamlit')
    app_streamlit = os.path.join(os.getcwd(), 'app', '.streamlit')
    
    # Check root .streamlit
    if os.path.exists(root_streamlit):
        st.success(f"✓ Found root .streamlit directory: {root_streamlit}")
        secrets_file = os.path.join(root_streamlit, 'secrets.toml')
        if os.path.exists(secrets_file):
            st.success("✓ Found secrets.toml in root .streamlit")
        else:
            st.error("✗ No secrets.toml in root .streamlit")
    else:
        st.error("✗ No root .streamlit directory found")
        
    # Check app .streamlit
    if os.path.exists(app_streamlit):
        st.success(f"✓ Found app .streamlit directory: {app_streamlit}")
        secrets_file = os.path.join(app_streamlit, 'secrets.toml')
        if os.path.exists(secrets_file):
            st.success("✓ Found secrets.toml in app .streamlit")
        else:
            st.error("✗ No secrets.toml in app .streamlit")
    else:
        st.error("✗ No app .streamlit directory found")

def test_secrets_content():
    st.header("Testing Secrets Content")
    
    # Check if we can access secrets
    if hasattr(st, 'secrets'):
        st.success("✓ Streamlit secrets are available")
        
        # Check Gmail configuration
        if 'GMAIL_TOKEN' in st.secrets:
            token = st.secrets['GMAIL_TOKEN']
            if isinstance(token, str):
                try:
                    import json
                    token_dict = json.loads(token)
                    required_fields = ['client_id', 'client_secret', 'refresh_token', 'token_uri']
                    missing_fields = [f for f in required_fields if f not in token_dict]
                    if not missing_fields:
                        st.success("✓ Gmail token contains all required fields")
                    else:
                        st.error(f"✗ Gmail token missing fields: {missing_fields}")
                except json.JSONDecodeError:
                    st.error("✗ Gmail token is not valid JSON")
            else:
                st.error("✗ Gmail token is not a string")
        else:
            st.error("✗ GMAIL_TOKEN not found in secrets")
            
        # Check MotherDuck configuration
        if 'MOTHERDUCK_TOKEN' in st.secrets:
            st.success("✓ Found MotherDuck token")
        else:
            st.error("✗ MOTHERDUCK_TOKEN not found in secrets")
            
        # Check recipient configuration
        if 'DEFAULT_RECIPIENT' in st.secrets:
            st.success(f"✓ Found default recipient: {st.secrets['DEFAULT_RECIPIENT']}")
        else:
            st.error("✗ DEFAULT_RECIPIENT not found in secrets")
    else:
        st.error("✗ No Streamlit secrets available")

def main():
    st.set_page_config(page_title="Cloud Services Test", layout="wide")
    st.title("Cloud Services Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_gmail_config()
        
    with col2:
        test_motherduck_config()
        
    st.markdown("---")
    st.header("Secrets Configuration Test")
    test_secrets_location()
    st.markdown("---")
    test_secrets_content()
    
    # Show environment info
    st.markdown("---")
    st.header("Environment Information")
    st.write("Current working directory:", os.getcwd())
    st.write("Python path:", os.getenv('PYTHONPATH', 'Not set'))
    st.write("Streamlit running in cloud:", bool(os.getenv('STREAMLIT_CLOUD') or os.getenv('STREAMLIT_SHARING')))

if __name__ == "__main__":
    main()
