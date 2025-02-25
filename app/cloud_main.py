"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timedelta

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.visualization.charts import display_transformer_dashboard

# Configure logging
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(
        page_title="Transformer Loading Analysis",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("Transformer Loading Analysis")
    
    # Initialize services
    data_service = CloudDataService()
    alert_service = CloudAlertService()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Date range selection
        st.subheader("Date Range")
        start_date = st.date_input(
            "Start Date",
            value=pd.to_datetime("2024-01-01").date(),
            min_value=pd.to_datetime("2024-01-01").date(),
            max_value=pd.to_datetime("2024-06-28").date()
        )
        end_date = st.date_input(
            "End Date",
            value=pd.to_datetime("2024-06-28").date(),
            min_value=pd.to_datetime("2024-01-01").date(),
            max_value=pd.to_datetime("2024-06-28").date()
        )
        
        # Feeder selection
        st.subheader("Feeder Selection")
        feeders = data_service.get_feeder_options()
        feeder = st.selectbox(
            "Select Feeder",
            options=feeders,
            index=0 if feeders else None
        )
        
        # Transformer selection
        st.subheader("Transformer Selection")
        transformers = data_service.get_load_options(feeder) if feeder else []
        transformer_id = st.selectbox(
            "Select Transformer",
            options=transformers,
            index=0 if transformers else None
        )
        
        # Search & Alert button
        if st.button("Search & Alert"):
            # Clear existing data from session state
            for key in ['transformer_data', 'customer_data', 'current_transformer', 'current_feeder']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.search_clicked = True
            
            # Get transformer data
            transformer_data = data_service.get_transformer_data_range(
                start_date=start_date,
                end_date=end_date,
                feeder=feeder,
                transformer_id=transformer_id
            )
            
            # Get customer data
            customer_data = data_service.get_customer_data(
                transformer_id=transformer_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if transformer_data is not None:
                # Process alerts
                alert_service.check_and_send_alerts(transformer_data)
                
                # Store data in session state
                st.session_state.transformer_data = transformer_data
                st.session_state.customer_data = customer_data
                st.session_state.current_transformer = transformer_id
                st.session_state.current_feeder = feeder
                
                # Rerun to update display
                st.rerun()
    
    # Main content area
    if 'transformer_data' in st.session_state:
        transformer_data = st.session_state.transformer_data
        customer_data = st.session_state.customer_data
        
        if transformer_data is not None:
            display_transformer_dashboard(transformer_data, customer_data)
        else:
            st.warning("No transformer data available for the selected criteria.")

if __name__ == "__main__":
    main()
