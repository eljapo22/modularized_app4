"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import sys
import pandas as pd
from datetime import datetime

# Remove all existing handlers to avoid duplicates
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override any existing configuration
)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info("Starting cloud application...")

from app.services.services import CloudDataService, CloudAlertService
from app.visualization.charts import display_transformer_dashboard
from app.utils.performance import log_performance

@log_performance
def main():
    st.set_page_config(
        page_title="Transformer Loading Analysis",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("Transformer Loading Analysis")
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        data_service = CloudDataService()
        alert_service = CloudAlertService()
        
        # Default dates
        default_start = pd.to_datetime("2024-01-01").date()
        default_end = pd.to_datetime("2024-06-28").date()
        
        # Only get URL parameters if we're coming from an alert link
        params = st.experimental_get_query_params()
        is_from_alert = 'transformer_id' in params
        
        if is_from_alert:
            logger.info("Loading from alert link...")
            initial_start = params.get('start_date', [None])[0]
            initial_end = params.get('end_date', [None])[0]
            initial_transformer = params.get('transformer_id', [None])[0]
            initial_feeder = params.get('feeder', [None])[0]
            initial_hour = params.get('hour', [None])[0]
            
            # Convert dates if provided
            try:
                start_date = pd.to_datetime(initial_start).date() if initial_start else default_start
                end_date = pd.to_datetime(initial_end).date() if initial_end else default_end
            except:
                start_date = default_start
                end_date = default_end
        else:
            logger.info("Initial launch...")
            start_date = default_start
            end_date = default_end
            initial_transformer = None
            initial_feeder = None
            initial_hour = None
        
        # Sidebar for controls
        with st.sidebar:
            st.header("Controls")
            
            # Date range selection
            st.subheader("Date Range")
            start_date = st.date_input(
                "Start Date",
                value=start_date,
                min_value=default_start,
                max_value=default_end
            )
            end_date = st.date_input(
                "End Date",
                value=end_date,
                min_value=default_start,
                max_value=default_end
            )
            
            # Hour selection if provided from alert
            hour = None
            if initial_hour and is_from_alert:
                try:
                    hour = int(initial_hour)
                    st.info(f"Analyzing data for hour: {hour}:00")
                except:
                    pass
            
            # Feeder selection
            st.subheader("Feeder Selection")
            feeders = data_service.get_feeder_options()
            
            # Only try to match feeder if coming from alert
            initial_feeder_idx = 0
            if is_from_alert and initial_feeder:
                try:
                    initial_feeder_idx = feeders.index(f"Feeder {initial_feeder}")
                except:
                    pass
                    
            feeder = st.selectbox(
                "Select Feeder",
                options=feeders,
                index=initial_feeder_idx if feeders else None
            )
            
            # Transformer selection
            st.subheader("Transformer Selection")
            transformers = data_service.get_transformer_ids(feeder) if feeder else []
            
            # Only try to match transformer if coming from alert
            initial_transformer_idx = 0
            if is_from_alert and initial_transformer and transformers:
                try:
                    initial_transformer_idx = transformers.index(initial_transformer)
                except:
                    pass
                    
            transformer_id = st.selectbox(
                "Select Transformer",
                options=transformers,
                index=initial_transformer_idx if transformers else None
            )
            
            # Search & Alert button
            if st.button("Search & Alert"):
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
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                # Check for alerts
                if not transformer_data.empty:
                    alert_service.check_and_send_alerts(
                        transformer_data,
                        start_date=start_date,
                        end_date=end_date,
                        feeder=feeder
                    )
                
                # Display dashboard
                display_transformer_dashboard(transformer_data, customer_data)
                
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        st.error("An error occurred. Please try again.")

if __name__ == "__main__":
    main()
