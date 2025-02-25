"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import logging.handlers
import pandas as pd
from datetime import datetime, timedelta
import sys
import traceback

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
        consolidated_service = CloudDataService()
        
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
            
            # Hour selection
            st.subheader("Hour Selection")
            hour = st.number_input(
                "Hour (0-23)",
                min_value=0,
                max_value=23,
                value=12
            )
            
            # Feeder selection
            st.subheader("Feeder Selection")
            feeders = consolidated_service.get_feeder_options()
            feeder = st.selectbox(
                "Select Feeder",
                options=feeders,
                index=0 if feeders else None
            )
            
            # Transformer selection
            st.subheader("Transformer Selection")
            transformers = consolidated_service.get_load_options(feeder) if feeder else []
            transformer_id = st.selectbox(
                "Select Transformer",
                options=transformers,
                index=0 if transformers else None
            )
            
            # Search & Alert button
            if st.button("Search & Alert"):
                st.session_state.search_clicked = True
                
                # Get transformer data
                transformer_data = consolidated_service.get_transformer_data_range(
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                # Get customer data
                customer_data = consolidated_service.get_customer_data(
                    transformer_id=transformer_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if transformer_data is not None:
                    # Process alerts
                    CloudAlertService().check_and_send_alerts(
                        results_df=transformer_data,
                        start_date=start_date,
                        end_date=end_date,
                        hour=hour,
                        feeder=feeder
                    )
                    
                    # Store data in session state
                    st.session_state.transformer_data = transformer_data
                    st.session_state.customer_data = customer_data
                    st.session_state.current_transformer = transformer_id
                    st.session_state.current_feeder = feeder
                    
                    # Rerun to update display
                    st.rerun()
        
        # Main content area
        if 'transformer_data' in st.session_state:
            transformer_data = st.session_state.transformer_data
            customer_data = st.session_state.customer_data
            
            if transformer_data is not None:
                display_transformer_dashboard(transformer_data, customer_data)
            else:
                st.warning("No transformer data available for the selected criteria.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(traceback.format_exc())
        st.error(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
