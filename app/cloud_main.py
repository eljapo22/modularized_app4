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
from app.visualization.charts import display_customer_tab

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
        params = st.experimental_get_query_params()
        from_alert = params.get('view', [''])[0] == 'alert'
        alert_transformer = params.get('id', [''])[0] if from_alert else None
        start_date_str = params.get('start', [''])[0]
        alert_time_str = params.get('alert_time', [''])[0]
        
        create_banner("Transformer Loading Analysis")
        
        # Analysis Parameters in sidebar
        st.sidebar.header("Analysis Parameters")
        
        # Date range selection
        dates = st.sidebar.date_input(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, min_date)
        )
        
        # Convert to tuple if single date
        if isinstance(dates, (datetime, date)):
            start_date = end_date = dates
        else:
            start_date, end_date = dates
        
        # Feeder and transformer selection
        feeder = st.sidebar.selectbox("Select Feeder", data_service.get_feeder_options())
        transformer_id = st.sidebar.selectbox(
            "Select Transformer",
            data_service.get_load_options(feeder)
        )
        
        # Action buttons
        search_clicked = st.sidebar.button("Search & Analyze")
        alert_clicked = st.sidebar.button("Set Alert", key="set_alert")
        
        # Main content area for visualization
        main_container = st.container()
        with main_container:
            if alert_clicked:
                logger.info("Alert button clicked")
                if alert_service is None:
                    logger.warning("Alert service not available")
                    st.error("Alert service is not available")
                else:
                    logger.info("Checking alert conditions...")
                    if not all([start_date, end_date, feeder, transformer_id]):
                        logger.warning("Missing required parameters for alert")
                        st.error("Please select all required parameters")
                    else:
                        query_datetime = datetime.combine(start_date, time(12))
                        logger.info(f"Checking alerts for {query_datetime}")
                        
                        # Check and send alerts if needed
                        if alert_service.check_and_send_alerts(
                            None,
                            start_date,
                            query_datetime
                        ):
                            logger.info("Alert email sent successfully")
                            st.success("Alert email sent successfully")
                        else:
                            logger.warning("Alert check completed without sending email")
            
            if search_clicked or (from_alert and alert_transformer):
                if not all([start_date, end_date, feeder, transformer_id]):
                    st.error("Please select all required parameters")
                else:
                    # Get transformer data
                    transformer_data = data_service.get_transformer_data_range(
                        start_date,
                        end_date,
                        feeder,
                        transformer_id
                    )
                    
                    # Get customer data
                    customer_data = data_service.get_customer_data(
                        transformer_id,
                        start_date,
                        end_date
                    )
                    
                    # Get customer aggregation
                    customer_agg = data_service.get_customer_aggregation(
                        transformer_id,
                        start_date,
                        end_date
                    )
                    
                    if transformer_data is not None and not transformer_data.empty:
                        # Create tabs for transformer and customer data
                        tab1, tab2 = st.tabs(["Transformer Analysis", "Customer Analysis"])
                        
                        with tab1:
                            display_transformer_dashboard(transformer_data)
                        
                        with tab2:
                            if customer_data is not None and not customer_data.empty:
                                display_customer_tab(customer_data, customer_agg)
                            else:
                                st.warning("No customer data available for the selected criteria.")
                    else:
                        st.warning("No transformer data available for the selected criteria.")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
