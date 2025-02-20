"""
Test Streamlit app to verify cloud setup and MotherDuck connection
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from app.core.database import get_database_connection
from app.services.cloud_data_service import CloudDataService
from app.config.cloud_config import use_motherduck

def main():
    st.set_page_config(page_title="Cloud Setup Test", layout="wide")
    st.title("Cloud Setup Test")
    
    # Test MotherDuck Configuration
    st.header("1. Configuration Test")
    
    # Check if MotherDuck is enabled
    is_motherduck = use_motherduck()
    st.write(f"MotherDuck enabled: {'✓' if is_motherduck else '✗'}")
    
    # Check if token exists
    token_exists = bool(st.secrets.get('MOTHERDUCK_TOKEN'))
    st.write(f"MotherDuck token found: {'✓' if token_exists else '✗'}")
    
    # Test Database Connection
    st.header("2. Database Connection Test")
    try:
        conn = get_database_connection()
        if conn:
            st.write("✓ Database connection successful")
            
            # List available tables
            tables = conn.execute('SHOW TABLES').fetchdf()
            st.write("Available tables:", tables['name'].tolist())
        else:
            st.error("✗ Failed to connect to database")
            return
    except Exception as e:
        st.error(f"✗ Connection error: {str(e)}")
        return
        
    # Test Data Service
    st.header("3. Data Service Test")
    try:
        service = CloudDataService()
        test_date = datetime(2024, 1, 1).date()
        
        # Test each feeder
        for feeder in range(1, 5):
            st.subheader(f"Feeder {feeder}")
            
            # Test transformer data
            transformer_data = service.get_transformer_data_for_date(feeder, test_date)
            if not transformer_data.empty:
                st.write(f"✓ Transformer data available")
                st.write(f"- Records: {len(transformer_data)}")
                st.write(f"- Unique transformers: {transformer_data['transformer_id'].nunique()}")
                with st.expander("View sample transformer data"):
                    st.dataframe(transformer_data.head())
            else:
                st.warning(f"✗ No transformer data for feeder {feeder}")
            
            # Test customer data
            customer_data = service.get_customer_data_for_date(feeder, test_date)
            if not customer_data.empty:
                st.write(f"✓ Customer data available")
                st.write(f"- Records: {len(customer_data)}")
                st.write(f"- Unique customers: {customer_data['customer_id'].nunique()}")
                with st.expander("View sample customer data"):
                    st.dataframe(customer_data.head())
            else:
                st.warning(f"✗ No customer data for feeder {feeder}")
            
            # Test relationships
            relationships = service.get_transformer_customer_relationships(feeder, test_date)
            if not relationships.empty:
                st.write(f"✓ Relationship data available")
                st.write(f"- Transformer-customer mappings: {len(relationships)}")
                with st.expander("View relationship data"):
                    st.dataframe(relationships.head())
            else:
                st.warning(f"✗ No relationship data for feeder {feeder}")
                
    except Exception as e:
        st.error(f"✗ Data service error: {str(e)}")
        return

if __name__ == "__main__":
    main()
