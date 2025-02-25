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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        st.error(f"Error initializing data service: {str(e)}")
        logger.error(f"Data service initialization error: {str(e)}")
        data_service = CloudDataService()  # Try again
    
    try:
        alert_service = CloudAlertService()
    except Exception as e:
        st.error(f"Error initializing alert service: {str(e)}")
        logger.error(f"Alert service initialization error: {str(e)}")
        alert_service = None
    
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
        
        # Feeder selection with comprehensive error handling
        st.subheader("Feeder Selection")
        try:
            feeders = data_service.get_feeder_options()
            if not feeders:
                st.warning("No feeders found. Using default.")
                feeders = ["Feeder 1"]
        except Exception as e:
            logger.error(f"Comprehensive feeder loading error: {str(e)}")
            feeders = ["Feeder 1"]
            st.warning(f"Error loading feeders: {str(e)}. Using default.")

        # Ensure a valid selection
        feeder = st.selectbox(
            "Select Feeder",
            options=feeders,
            index=0
        )

        # Transformer selection with comprehensive error handling
        st.subheader("Transformer Selection")
        try:
            # Ensure feeder is a string and extract number if needed
            feeder_str = str(feeder)
            
            # Retrieve transformers
            transformers = data_service.get_transformer_options(feeder_str)
            
            if not transformers:
                st.warning(f"No transformers found for {feeder_str}. Try another feeder.")
                transformers = [f"Transformer_{feeder_str}_001"]  # Fallback
        except Exception as e:
            logger.error(f"Comprehensive transformer loading error: {str(e)}")
            transformers = [f"Transformer_{feeder}_001"]  # Fallback
            st.warning(f"Error loading transformers: {str(e)}. Using default.")

        # Ensure a valid transformer selection
        transformer_id = st.selectbox(
            "Select Transformer",
            options=transformers,
            index=0
        )
        
        # Search & Alert button
        if st.button("Search & Alert"):
            # Clear existing data from session state
            for key in ['transformer_data', 'customer_data', 'current_transformer', 'current_feeder']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.search_clicked = True
            
            try:
                # Get transformer data with detailed logging
                transformer_data = data_service.get_transformer_data_range(
                    start_date=start_date,
                    end_date=end_date,
                    feeder=feeder,
                    transformer_id=transformer_id
                )
                
                # Log detailed information about retrieved transformer data
                if transformer_data is not None and not transformer_data.empty:
                    logger.info(f"Transformer data retrieved successfully")
                    logger.info(f"Data shape: {transformer_data.shape}")
                    logger.info(f"Columns: {transformer_data.columns}")
                    logger.info(f"Timestamp range: {transformer_data.index.min()} to {transformer_data.index.max()}")
                else:
                    logger.warning("No transformer data retrieved")
                
                # Get customer data with comprehensive error handling
                try:
                    customer_data = data_service.get_customer_data(
                        transformer_id=transformer_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Log customer data details
                    if customer_data is not None and not customer_data.empty:
                        logger.info(f"Customer data retrieved successfully")
                        logger.info(f"Customer data shape: {customer_data.shape}")
                        logger.info(f"Customer data columns: {customer_data.columns}")
                    else:
                        logger.warning("No customer data retrieved")
                
                except Exception as e:
                    logger.error(f"Comprehensive error getting customer data: {str(e)}")
                    customer_data = pd.DataFrame()
                    st.warning(f"Could not retrieve customer data: {str(e)}")
                
                # Process alerts if service is available
                if alert_service and transformer_data is not None:
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
            
            except Exception as e:
                logger.error(f"Comprehensive data retrieval error: {str(e)}")
                st.error(f"Failed to retrieve data: {str(e)}")
    
    # Main content area
    if 'transformer_data' in st.session_state:
        transformer_data = st.session_state.transformer_data
        customer_data = st.session_state.get('customer_data', pd.DataFrame())
        
        if transformer_data is not None and not transformer_data.empty:
            try:
                # Ensure timestamp is properly formatted
                if not isinstance(transformer_data.index, pd.DatetimeIndex):
                    transformer_data.index = pd.to_datetime(transformer_data.index)
                
                # Log additional diagnostic information
                logger.info(f"Dashboard Data - Transformer Data Shape: {transformer_data.shape}")
                logger.info(f"Dashboard Data - Transformer Columns: {transformer_data.columns}")
                logger.info(f"Dashboard Data - Timestamp Range: {transformer_data.index.min()} to {transformer_data.index.max()}")
                
                # Display dashboard
                display_transformer_dashboard(transformer_data, customer_data)
            
            except Exception as e:
                logger.error(f"Comprehensive dashboard display error: {str(e)}")
                st.error(f"Failed to display dashboard: {str(e)}")
                
                # Additional diagnostic output
                st.write("Diagnostic Information:")
                st.write(f"Transformer Data Shape: {transformer_data.shape}")
                st.write(f"Transformer Data Columns: {transformer_data.columns}")
                st.write(f"Timestamp Type: {type(transformer_data.index)}")
        else:
            st.warning("No transformer data available for the selected criteria.")

if __name__ == "__main__":
    main()