"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import pandas as pd
from datetime import datetime, timedelta, date

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.visualization.charts import display_transformer_dashboard

# Configure logging
logger = logging.getLogger(__name__)

def main():
    st.set_page_config(
        page_title="Transformer Loading Analysis",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("Transformer Loading Analysis")
    
    # Initialize services with error handling
    try:
        data_service = CloudDataService()
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        data_service = CloudDataService()  # Try again
    
    try:
        alert_service = CloudAlertService()
    except Exception as e:
        st.error(f"Error initializing alert service: {str(e)}")
        logger.error(f"Alert service initialization error: {str(e)}")
    
    # Get available date range with fallback
    try:
        min_date, max_date = data_service.get_available_dates()
    except Exception as e:
        logger.error(f"Error getting date range: {str(e)}")
        min_date = date(2024, 1, 1)
        max_date = date(2024, 6, 30)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Date range selection
        st.subheader("Date Range")
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        # Feeder selection
        st.subheader("Feeder Selection")
        try:
            feeders = data_service.get_feeder_options()
            if not feeders:
                st.warning("No feeders found. Using default.")
                feeders = ["Feeder 1"]
        except Exception as e:
            logger.error(f"Error loading feeders: {str(e)}")
            feeders = ["Feeder 1"]
            st.warning("Error loading feeders. Using default.")
        
        feeder = st.selectbox(
            "Select Feeder",
            options=feeders,
            index=0 if feeders else None
        )
        
        # Transformer selection
        st.subheader("Transformer Selection")
        try:
            transformers = data_service.get_transformer_options(feeder) if feeder else []
            if not transformers:
                st.warning(f"No transformers found for {feeder}. Try another feeder.")
        except Exception as e:
            logger.error(f"Error loading transformers: {str(e)}")
            transformers = []
            st.warning("Error loading transformers.")
            
        transformer_id = st.selectbox(
            "Select Transformer",
            options=transformers,
            index=0 if transformers else None
        )
        
        # Search & Alert button
        if st.button("Search & Alert"):
            # Clear existing data from session state
            for key in ['transformer_data', 'customer_data', 'current_transformer', 'current_feeder']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.search_clicked = True
            
            try:
                # Get transformer data
                transformer_data = data_service.get_transformer_data_range(
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                # Get customer data - adapt parameters based on the actual method signature
                try:
                    # Use the correct parameter format for get_customer_data
                    customer_data = data_service.get_customer_data(
                        customer_id=transformer_id,
                        date_str=start_date.strftime("%Y-%m-%d")
                    )
                except Exception as e:
                    logger.warning(f"Error getting customer data: {str(e)}")
                    customer_data = pd.DataFrame()
                
                if transformer_data is not None:
                    # Process alerts
                    try:
                        alert_service.check_and_send_alerts(transformer_data)
                    except Exception as e:
                        logger.error(f"Alert processing error: {str(e)}")
                        st.warning("Could not process alerts.")
                    
                    # Store data in session state
                    st.session_state.transformer_data = transformer_data
                    st.session_state.customer_data = customer_data
                    st.session_state.current_transformer = transformer_id
                    st.session_state.current_feeder = feeder
                    
                    # Rerun to update display
                    st.rerun()
                else:
                    st.warning("No transformer data available for the selected criteria.")
            except Exception as e:
                logger.error(f"Error retrieving data: {str(e)}")
                st.error("Failed to retrieve data. Please try again.")
    
    # Main content area
    if 'transformer_data' in st.session_state:
        transformer_data = st.session_state.transformer_data
        customer_data = st.session_state.customer_data
        
        if transformer_data is not None and not transformer_data.empty:
            try:
                display_transformer_dashboard(transformer_data, customer_data)
            except Exception as e:
                logger.error(f"Error displaying dashboard: {str(e)}")
                st.error("Failed to display dashboard. Please try again.")
        else:
            st.warning("No transformer data available for the selected criteria.")

if __name__ == "__main__":
    main()
