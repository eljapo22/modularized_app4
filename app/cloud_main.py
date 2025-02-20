"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""

import streamlit as st
import logging
import traceback
from datetime import datetime
from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.visualization.charts import (
    display_transformer_dashboard,
    display_loading_status_line_chart,
    display_power_time_series,
    display_current_time_series,
    display_voltage_time_series,
    display_loading_status,
    add_hour_indicator
)
from app.utils.ui_components import create_banner, create_section_banner
from app.utils.performance import log_performance

# Initialize logger
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    handlers=[
        logging.StreamHandler()
    ]
)

# Initialize services
try:
    logger.info("Initializing services...")
    data_service = CloudDataService()
    alert_service = CloudAlertService(data_service)
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}\nTraceback: {traceback.format_exc()}")
    st.error("Failed to initialize application services. Please check the logs for details.")
    st.stop()

# Configure page
st.set_page_config(page_title="Transformer Loading Analysis", layout="wide")

@log_performance
def main():
    """Main application function for cloud environment"""
    try:
        # Create banner
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.header("Analysis Parameters")
            
            try:
                # Date selection
                logger.info("Getting available dates...")
                min_date, max_date = data_service.get_available_dates()
                logger.info(f"Got date range: {min_date} to {max_date}")
                
                selected_date = st.date_input(
                    "Select Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Hour selection
                selected_hour = st.slider(
                    "Select Hour",
                    min_value=0,
                    max_value=23,
                    value=12,
                    help="Select hour of the day (24-hour format)"
                )
                
                # Feeder selection
                logger.info("Getting feeder list...")
                feeders = data_service.get_feeder_list()
                logger.info(f"Found {len(feeders)} feeders")
                
                selected_feeder = st.selectbox(
                    "Select Feeder",
                    options=feeders,
                    format_func=lambda x: f"Feeder {x}"
                )
                
                if selected_feeder:
                    logger.info(f"Getting transformers for feeder {selected_feeder}...")
                    transformers = data_service.get_transformer_ids(selected_feeder)
                    logger.info(f"Found {len(transformers)} transformers")
                    
                    selected_transformer = st.selectbox(
                        "Select Transformer",
                        options=transformers
                    )
                    
                    if selected_transformer:
                        # Search & Alert button
                        if st.button("Search & Alert"):
                            with st.spinner("Processing..."):
                                logger.info(f"Getting data for transformer {selected_transformer}...")
                                results = data_service.get_transformer_data(selected_transformer, selected_date)
                                
                                if results is not None and not results.empty:
                                    # Process alerts
                                    logger.info("Processing alerts...")
                                    alert_sent = alert_service.process_alerts(
                                        results,
                                        selected_transformer,
                                        selected_date,
                                        selected_hour
                                    )
                                    
                                    if alert_sent:
                                        st.success("Alert processed successfully!")
                                    else:
                                        st.info("No alerts triggered for the selected criteria.")
                                else:
                                    st.warning("No data available for the selected transformer and date.")
            
            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while loading the sidebar. Please try again.")
                return
        
        # Main content area
        if selected_transformer:
            try:
                logger.info(f"Getting data for transformer {selected_transformer}...")
                results = data_service.get_transformer_data(selected_transformer, selected_date)
                
                if results is not None and not results.empty:
                    logger.info("Displaying transformer dashboard...")
                    display_transformer_dashboard(results, selected_hour)
                else:
                    st.warning("No data available for the selected transformer and date.")
            except Exception as e:
                logger.error(f"Error displaying dashboard: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while displaying the dashboard. Please try again.")
        else:
            st.info("Please select a transformer to view analysis.")
            
    except Exception as e:
        logger.error(f"Main application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()
