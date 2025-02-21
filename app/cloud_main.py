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

        # Get available feeders
        feeders = data_service.get_feeder_options()
        logger.info(f"Found {len(feeders)} feeders")

        # Create feeder selector
        selected_feeder = st.selectbox(
            "Select Feeder",
            options=feeders,
            key="feeder_selector"
        )

        if selected_feeder:
            # Get transformers for selected feeder
            transformers = data_service.get_transformer_ids(selected_feeder)
            logger.info(f"Found {len(transformers)} transformers")

            # Create transformer selector
            selected_transformer = st.selectbox(
                "Select Transformer",
                options=transformers,
                key="transformer_selector"
            )

            if selected_transformer:
                # Get transformer data
                results = data_service.get_transformer_data(
                    transformer_id=selected_transformer,
                    start_date=selected_date,
                    end_date=selected_date
                )

                if results is not None:
                    # Display transformer dashboard
                    if 'selected_hour' in st.session_state:
                        hour = st.session_state.selected_hour
                    else:
                        hour = None

                    display_transformer_dashboard(
                        results,
                        start_date=selected_date,
                        end_date=selected_date,
                        hour=hour
                    )

                    # Alert configuration
                    if alert_service is not None:
                        st.markdown("### Alert Configuration")
                        alert_threshold = st.number_input(
                            "Alert Threshold (%)",
                            min_value=0,
                            max_value=200,
                            value=100
                        )
                        alert_email = st.text_input("Alert Email")
                        alert_clicked = st.button("Set Alert")

                    # Check and send alerts if needed
                    if alert_service is not None and alert_clicked:
                        if alert_email and alert_threshold:
                            alert_service.set_alert(
                                transformer_id=selected_transformer,
                                threshold=alert_threshold,
                                email=alert_email,
                                check_hour=hour
                            )
                            st.success("Alert set successfully!")
                        else:
                            logger.warning("Missing required parameters for alert")
                            st.error("Please select all required parameters")
                else:
                    st.warning("No data available for the selected transformer")
            else:
                st.warning("No transformers found for the selected feeder")
        else:
            st.warning("No feeders available")
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
