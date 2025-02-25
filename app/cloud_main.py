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
        
        # Sidebar for controls
        with st.sidebar:
            st.header("Controls")
            
            # Date range selection
            st.subheader("Date Range")
            start_date = st.date_input(
                "Start Date",
                value=pd.to_datetime("2024-01-01").date(),
                min_value=pd.to_datetime("2024-01-01").date(),
                max_value=pd.to_datetime("2024-06-28").date()
            )
            end_date = st.date_input(
                "End Date",
                value=pd.to_datetime("2024-06-28").date(),
                min_value=pd.to_datetime("2024-01-01").date(),
                max_value=pd.to_datetime("2024-06-28").date()
            )
            
            # Feeder selection
            st.subheader("Feeder Selection")
            feeders = data_service.get_feeder_options()
            feeder = st.selectbox(
                "Select Feeder",
                options=feeders,
                index=0 if feeders else None
            )
            
            # Transformer selection
            st.subheader("Transformer Selection")
            transformers = data_service.get_transformer_ids(feeder) if feeder else []
            transformer_id = st.selectbox(
                "Select Transformer",
                options=transformers,
                index=0 if transformers else None
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
