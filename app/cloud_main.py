"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from typing import Optional, Tuple

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.visualization.charts import display_transformer_tab, display_customer_tab

# Configure logging
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(
        page_title="Transformer Loading Analysis",
        page_icon="⚡",
        layout="wide"
    )
    
    # Initialize services
    data_service = CloudDataService()
    alert_service = CloudAlertService()
    
    # Create title
    st.title("Transformer Loading Analysis")
    
    # Create sidebar
    with st.sidebar:
        st.header("Analysis Parameters")
        
        # Date range selection
        st.subheader("Select Date Range")
        
        # Get available date range from data service
        min_date = data_service.min_date
        max_date = data_service.max_date
        default_start = max_date - timedelta(days=7)
        if default_start < min_date:
            default_start = min_date
            
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=min_date,
            max_value=max_date,
            key="start_date"
        )
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="end_date"
        )
        
        # Feeder selection
        st.subheader("Select Feeder")
        feeder_options = data_service.get_feeder_options()
        if not feeder_options:
            st.error("No feeders available")
            return
            
        feeder = st.selectbox(
            "Feeder",
            options=feeder_options,
            key="feeder"
        )
        
        # Transformer selection
        st.subheader("Select Transformer")
        transformer_options = data_service.get_load_options(feeder)
        if not transformer_options:
            st.error("No transformers available")
            return
            
        transformer_id = st.selectbox(
            "Transformer ID",
            options=transformer_options,
            key="transformer"
        )
        
        # Search & Alert button
        if st.button("Search & Alert", key="search"):
            logger.info(f"Fetching data for date range: {start_date} to {end_date}")
            
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
                st.experimental_rerun()
    
    # Main content area
    if 'transformer_data' in st.session_state:
        transformer_data = st.session_state.transformer_data
        customer_data = st.session_state.customer_data
        
        if transformer_data is not None:
            # Create tabs
            transformer_tab, customer_tab = st.tabs(["Transformer Analysis", "Customer Analysis"])
            
            # Transformer Analysis Tab
            with transformer_tab:
                customer_count = len(customer_data) if customer_data is not None else 0
                display_transformer_tab(transformer_data, customer_count)
            
            # Customer Analysis Tab
            with customer_tab:
                display_customer_tab(customer_data)
        else:
            st.warning("No transformer data available for the selected criteria.")

if __name__ == "__main__":
    main()
