"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import traceback
from datetime import datetime, time, date
import logging
import pandas as pd

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.utils.ui_utils import create_banner, display_transformer_dashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize services first to get date range
        try:
            data_service = CloudDataService()
            alert_service = CloudAlertService()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            st.error("Failed to initialize some services. Some features may be limited.")
            data_service = CloudDataService()  # Retry just the data service
            alert_service = None

        # Get available date range
        min_date, max_date = data_service.get_available_dates()
        logger.info(f"Got date range: {min_date} to {max_date}")
            
        # Set page config
        st.set_page_config(
            page_title="Transformer Loading Analysis",
            page_icon="⚡",
            layout="wide"
        )
        
        # Check for URL parameters
        params = st.query_params
        from_alert = params.get('view', '') == 'alert'
        alert_transformer = params.get('id', '') if from_alert else None
        start_date_str = params.get('start', '')
        alert_time_str = params.get('alert_time', '')
        
        logger.info(f"URL Parameters - from_alert: {from_alert}, alert_transformer: {alert_transformer}")
        logger.info(f"URL Parameters - start_date: {start_date_str}, alert_time: {alert_time_str}")
        
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.markdown("### Search Controls")
            
            # Date range inputs with URL parameter handling
            if from_alert and start_date_str:
                try:
                    url_start_date = datetime.fromisoformat(start_date_str).date()
                    url_end_date = datetime.fromisoformat(alert_time_str).date() if alert_time_str else max_date
                    initial_dates = [url_start_date, url_end_date]
                except ValueError:
                    initial_dates = [min_date, max_date]
            else:
                initial_dates = [min_date, max_date]
            
            # Date range input
            date_input = st.date_input(
                "Date Range",
                value=initial_dates,
                min_value=min_date,
                max_value=max_date
            )
            
            # Handle both list and tuple returns
            if isinstance(date_input, (list, tuple)) and len(date_input) >= 2:
                start_date = date_input[0]
                end_date = date_input[-1]
            else:
                # If somehow we get a single date, use it for both
                start_date = end_date = date_input
            
            # Feeder selection
            with st.spinner("Loading feeders..."):
                feeder_options = data_service.get_feeder_options()
                logger.info(f"Found {len(feeder_options)} feeders")
            selected_feeder = st.selectbox(
                "Feeder",
                options=feeder_options,
                disabled=True
            )
            
            # Transformer ID selection
            with st.spinner("Loading transformers..."):
                transformer_ids = data_service.get_load_options(selected_feeder)
                logger.info(f"Found {len(transformer_ids)} transformers")
            transformer_index = transformer_ids.index(alert_transformer) if alert_transformer in transformer_ids else 0
            selected_transformer = st.selectbox(
                "Transformer ID",
                options=transformer_ids,
                index=transformer_index
            )
            
            # Search and Alert buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                search_clicked = st.button("Search & Analyze")
            with col2:
                # Only enable alert button if we have results
                if 'results' not in st.session_state:
                    st.button("Set Alert", disabled=True, help="First click 'Search & Analyze' to load data")
                    alert_clicked = False
                else:
                    alert_clicked = st.button("Set Alert", key="set_alert")
            
            if alert_clicked:
                logger.info("Alert button clicked")
                if alert_service is None:
                    logger.warning("Alert service not available")
                    st.error("Alert service is not available")
                elif 'results' not in st.session_state:
                    logger.warning("No results available for alert")
                    st.error("Please click 'Search & Analyze' first to load data")
                else:
                    logger.info("Checking alert conditions...")
                    if not all([selected_feeder, selected_transformer]):
                        logger.warning("Missing required parameters for alert")
                        st.error("Please select a feeder and transformer")
                    else:
                        try:
                            # Find the row with maximum loading
                            max_loading_row = st.session_state.results.loc[
                                st.session_state.results['loading_percentage'].idxmax()
                            ]
                            alert_time = max_loading_row.name  # This is the datetime index
                            alert_date = alert_time.date()
                            
                            logger.info(f"Checking alerts for highest loading ({max_loading_row['loading_percentage']:.1f}%) at {alert_time}")
                            
                            # Check and send alerts if needed
                            if alert_service.check_and_send_alerts(
                                st.session_state.results,
                                alert_date,
                                alert_time
                            ):
                                logger.info("Alert email sent successfully")
                                st.success("Alert email sent successfully")
                            else:
                                logger.warning("Alert check completed without sending email")
                        except Exception as e:
                            error_msg = f"Error processing alert: {str(e)}"
                            logger.error(error_msg)
                            st.error(f"❌ {error_msg}")
            
            if search_clicked or (from_alert and alert_transformer):
                logger.info(f"Search triggered - clicked: {search_clicked}, from_alert: {from_alert}, alert_transformer: {alert_transformer}")
                if not all([start_date, end_date, selected_feeder, selected_transformer]):
                    st.error("Please select all required parameters")
                else:
                    logger.info(f"Querying data from {start_date} to {end_date}")
                    try:
                        results = data_service.get_transformer_data_range(
                            transformer_id=selected_transformer,
                            start_date=start_date,
                            end_date=end_date,
                            feeder=selected_feeder
                        )
                        
                        if results is not None and not results.empty:
                            logger.info("Data retrieved successfully")
                            st.session_state.results = results
                            
                            logger.info(f"Displaying data for date range")
                            display_transformer_dashboard(results, start_date)
                        else:
                            st.warning("No data available for the selected criteria.")
                    except Exception as e:
                        error_msg = f"Error retrieving data: {str(e)}"
                        logger.error(error_msg)
                        st.error(f"❌ {error_msg}")
                        
    except Exception as e:
        logger.error(f"Unhandled error in main: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"❌ An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
