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
        
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.markdown("### Search Controls")
            
            try:
                # Search mode toggle
                search_mode = st.radio("Search Mode", ("Single Day", "Date Range"))
                
                if search_mode == "Single Day":
                    # Single day inputs
                    default_date = max_date
                    if 'selected_date' in st.session_state:
                        try:
                            default_date = st.session_state.selected_date
                        except:
                            pass
                            
                    selected_date = st.date_input(
                        "Date",
                        value=default_date,
                        min_value=min_date,
                        max_value=max_date
                    )
                    st.session_state.selected_date = selected_date
                    
                    default_hour = 0
                    if 'selected_hour' in st.session_state:
                        try:
                            default_hour = st.session_state.selected_hour
                        except:
                            pass
                            
                    selected_hour = st.selectbox(
                        "Time",
                        range(24),
                        index=default_hour,
                        format_func=lambda x: f"{x:02d}:00"
                    )
                    st.session_state.selected_hour = selected_hour
                else:
                    # Date range inputs with URL parameter handling
                    try:
                        if from_alert and start_date_str:
                            url_start_date = datetime.fromisoformat(start_date_str).date()
                            url_end_date = datetime.fromisoformat(alert_time_str).date() if alert_time_str else max_date
                            initial_dates = [url_start_date, url_end_date]
                        elif 'start_date' in st.session_state and 'end_date' in st.session_state:
                            initial_dates = [st.session_state.start_date, st.session_state.end_date]
                        else:
                            initial_dates = [min_date, max_date]
                    except:
                        initial_dates = [min_date, max_date]
                    
                    # Always use list for value to ensure we get a range
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
                        st.session_state.start_date = start_date
                        st.session_state.end_date = end_date
                    else:
                        # If somehow we get a single date, use it for both
                        start_date = end_date = date_input
                        st.session_state.start_date = st.session_state.end_date = date_input
                
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
                col1, col2 = st.columns(2)
                with col1:
                    search_clicked = st.button("Search & Analyze")
                with col2:
                    alert_clicked = st.button("Set Alert")
                
                if search_clicked or (from_alert and alert_transformer):
                    if search_mode == "Single Day":
                        if not all([st.session_state.selected_date, st.session_state.selected_hour is not None, selected_feeder, selected_transformer]):
                            st.error("Please select all required parameters")
                        else:
                            query_datetime = datetime.combine(st.session_state.selected_date, time(st.session_state.selected_hour))
                            results = data_service.get_transformer_data(
                                query_datetime, 
                                st.session_state.selected_hour,
                                selected_feeder,
                                selected_transformer
                            )
                            if results is not None and not results.empty:
                                logger.info("Displaying transformer dashboard...")
                                display_transformer_dashboard(results, st.session_state.selected_hour)
                                
                                # Check and send alerts if needed
                                if alert_service is not None and alert_clicked:
                                    logger.info("Attempting to send alert email...")
                                    if alert_service.check_and_send_alerts(
                                        results,
                                        st.session_state.selected_date,
                                        query_datetime
                                    ):
                                        st.success("Alert email sent successfully")
                                    else:
                                        st.warning("No alert conditions met or email sending failed")
                            else:
                                st.warning("No data available for the selected criteria.")
                    else:
                        if not all([st.session_state.start_date, st.session_state.end_date, selected_feeder, selected_transformer]):
                            st.error("Please select all required parameters")
                        else:
                            # Handle alert URL parameters
                            if from_alert and alert_time_str:
                                try:
                                    alert_time = datetime.fromisoformat(alert_time_str)
                                    results = data_service.get_transformer_data_to_point(
                                        st.session_state.start_date,
                                        alert_time,
                                        selected_feeder,
                                        selected_transformer
                                    )
                                except ValueError:
                                    logger.warning("Invalid alert time format in URL")
                                    results = data_service.get_transformer_data_range(
                                        st.session_state.start_date,
                                        st.session_state.end_date,
                                        selected_feeder,
                                        selected_transformer
                                    )
                            else:
                                results = data_service.get_transformer_data_range(
                                    st.session_state.start_date,
                                    st.session_state.end_date,
                                    selected_feeder,
                                    selected_transformer
                                )
                            
                            if results is not None and not results.empty:
                                # Display dashboard with alert time marker if available
                                alert_hour = None
                                if alert_time_str:
                                    try:
                                        alert_time = datetime.fromisoformat(alert_time_str)
                                        alert_hour = alert_time.hour
                                    except ValueError:
                                        logger.warning("Invalid alert time format")
                                
                                display_transformer_dashboard(results, alert_hour)
                                
                                # Check and send alerts if needed
                                if alert_service is not None and alert_clicked:
                                    logger.info("Attempting to send alert email for date range...")
                                    if alert_service.check_and_send_alerts(
                                        results,
                                        st.session_state.start_date,
                                        alert_time if alert_time_str else None
                                    ):
                                        st.success("Alert email sent successfully")
                                    else:
                                        st.warning("No alert conditions met or email sending failed")
                            else:
                                st.warning("No data available for the selected criteria.")
                
            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while loading the interface. Please try again.")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
