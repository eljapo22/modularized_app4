"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import traceback
import pandas as pd
from datetime import datetime, date, timedelta

from services.cloud_data_service import CloudDataService
from services.cloud_alert_service import CloudAlertService
from utils.ui_utils import create_banner, display_transformer_dashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Streamlit application."""
    try:
        # Initialize services
        data_service = CloudDataService()
        alert_service = CloudAlertService() if st.secrets.get("ENABLE_EMAIL_ALERTS", False) else None
        
        # Get URL parameters
        params = st.experimental_get_query_params()
        start_date_str = params.get('start', '')
        alert_time_str = params.get('alert_time', '')
        
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for analysis parameters
        with st.sidebar:
            st.markdown("### Analysis Parameters")
            
            # Date selection
            available_range = data_service.get_date_range()
            if available_range:
                min_date, max_date = available_range
                
                # Default to today if no date provided in URL
                default_date = datetime.now().date()
                if start_date_str:
                    try:
                        default_date = datetime.strptime(start_date_str[0], '%Y-%m-%d').date()
                    except ValueError:
                        logger.warning(f"Invalid date format in URL: {start_date_str[0]}")
                
                start_date = st.date_input(
                    "Start Date",
                    min_value=min_date,
                    max_value=max_date,
                    value=default_date
                )
                
                end_date = st.date_input(
                    "End Date",
                    min_value=start_date,
                    max_value=max_date if max_date else datetime.now().date(),
                    value=start_date + timedelta(days=3)
                )
                
                # Hour selection
                selected_hour = st.number_input(
                    "Hour (24-hour format)",
                    min_value=0,
                    max_value=23,
                    value=12
                )
                st.session_state['selected_hour'] = selected_hour
                
                # Feeder selection
                st.markdown("### Feeder Selection")
                feeder_options = data_service.get_feeder_options()
                if feeder_options:
                    selected_feeder = st.selectbox(
                        "Select Feeder",
                        options=feeder_options,
                        key="feeder_selector"
                    )
                    logger.info(f"Found {len(feeder_options)} feeders")
                    
                    # Transformer selection
                    transformer_ids = data_service.get_transformer_ids(selected_feeder)
                    if transformer_ids:
                        selected_transformer = st.selectbox(
                            "Select Transformer",
                            options=transformer_ids,
                            key="transformer_selector"
                        )
                        logger.info(f"Found {len(transformer_ids)} transformers")
                        
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
                        
                        # Fetch and display data
                        results = data_service.get_transformer_data(
                            selected_transformer,
                            start_date,
                            end_date
                        )
                        
                        if results is not None:
                            # Display transformer dashboard
                            display_transformer_dashboard(results)
                            
                            # Check and send alerts if needed
                            if alert_service is not None and alert_clicked:
                                if alert_email and alert_threshold:
                                    alert_service.set_alert(
                                        transformer_id=selected_transformer,
                                        threshold=alert_threshold,
                                        email=alert_email,
                                        check_hour=selected_hour
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
            else:
                st.error("Could not retrieve date range from the database")
                
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
