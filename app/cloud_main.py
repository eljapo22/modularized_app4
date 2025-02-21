"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import traceback
import pandas as pd
from datetime import datetime, date, timedelta

from services.cloud_data_service import CloudDataService, get_date_range
from services.cloud_alert_service import CloudAlertService
from utils.ui_utils import display_transformer_dashboard, setup_page

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize services
        data_service = CloudDataService()
        alert_service = CloudAlertService()

        # Setup page
        setup_page()

        # Get date range from service
        available_range = data_service.get_date_range()
        if not available_range:
            st.error("Could not retrieve date range from the database")
            return
            
        start_date, end_date = available_range
        logger.info(f"Got date range: {start_date} to {end_date}")

        # Create date input for filtering
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input(
                "Select Date",
                value=end_date,
                min_value=start_date,
                max_value=end_date
            )

        with col2:
            alert_hour = st.number_input(
                "Alert Hour (24-hour format)",
                min_value=0,
                max_value=23,
                value=14
            )

        # Create feeder selection
        feeder_options = data_service.get_feeder_options()
        if not feeder_options:
            st.error("No feeders found in the database")
            return

        logger.info(f"Found {len(feeder_options)} feeders")
        selected_feeder = st.selectbox("Select Feeder", feeder_options)

        # Get transformers for selected feeder
        transformer_ids = data_service.get_transformer_ids(selected_feeder)
        if not transformer_ids:
            st.error(f"No transformers found for feeder {selected_feeder}")
            return

        logger.info(f"Found {len(transformer_ids)} transformers")
        selected_transformer = st.selectbox("Select Transformer", transformer_ids)

        # Get transformer data
        results = data_service.get_transformer_data(selected_transformer, selected_date)
        if results is None or results.empty:
            st.error("No data available for the selected transformer")
            return

        # Display transformer dashboard
        display_transformer_dashboard(results, alert_hour)

        # Create email alert section
        st.markdown("---")
        st.subheader("Email Alerts")
        
        # Create two columns with different widths
        alert_container = st.container()
        with alert_container:
            alert_col1, alert_col2 = st.columns([1, 4])
            
            with alert_col1:
                enable_alerts = st.checkbox("Enable Email Alerts", value=True)
            
            with alert_col2:
                if enable_alerts:
                    email = st.text_input("Email Address for Alerts")
                    if email:
                        alert_service.set_email_alert(selected_transformer, email, alert_hour)
                        st.success(f"Email alerts set for {selected_transformer} at {alert_hour:02d}:00")

    except Exception as e:
        logger.error(f"Application error: {str(e)}\n\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application. Please check the logs for details.")

if __name__ == "__main__":
    main()
