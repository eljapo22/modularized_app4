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
from app.visualization.charts import display_transformer_data, display_customer_data

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
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=7),
            key="start_date"
        )
        end_date = st.date_input(
            "End Date",
            value=date.today(),
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
            customer_data = data_service.get_customer_data_range(
                start_date=start_date,
                end_date=end_date,
                feeder=feeder,
                transformer_id=transformer_id
            )
            
            if transformer_data is not None:
                # Process alerts
                alert_service.process_alerts(transformer_data)
                
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
            # Display transformer data
            st.header("Transformer Analysis")
            display_transformer_data(transformer_data)
            
            # Display customer data if available
            if customer_data is not None and not customer_data.empty:
                st.header("Customer Analysis")
                display_customer_data(customer_data)
            else:
                st.warning("No customer data available for this transformer")
        else:
            st.warning("No transformer data available for the selected criteria.")

if __name__ == "__main__":
    main()
