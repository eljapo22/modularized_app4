"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import traceback
from datetime import datetime, time
import logging

from app.services.cloud_data_service import CloudDataService
from app.utils.ui_utils import create_banner, display_transformer_dashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize services
        data_service = CloudDataService()
        
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
        
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.markdown("### Search Controls")
            
            try:
                # Get available date range
                with st.spinner("Loading available dates..."):
                    min_date, max_date = data_service.get_available_dates()
                    logger.info(f"Got date range: {min_date} to {max_date}")
                
                # Date selection
                selected_date = st.date_input(
                    "Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Hour selection
                selected_hour = st.selectbox(
                    "Time",
                    range(24),
                    format_func=lambda x: f"{x:02d}:00"
                )
                
                # Get feeder options
                with st.spinner("Loading feeders..."):
                    feeder_options = data_service.get_feeder_options()
                    logger.info(f"Found {len(feeder_options)} feeders")
                
                # Feeder selection (disabled)
                selected_feeder = st.selectbox(
                    "Feeder",
                    options=feeder_options,
                    disabled=True  # Make it visible but not interactive
                )
                
                # Get transformer IDs
                with st.spinner("Loading transformers..."):
                    transformer_ids = data_service.get_load_options(selected_feeder)
                    logger.info(f"Found {len(transformer_ids)} transformers")
                
                # Transformer ID selection - pre-select if from alert
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
                    if not all([selected_date, selected_hour is not None, selected_feeder, selected_transformer]):
                        st.error("Please select all required parameters")
                    else:
                        try:
                            with st.spinner("Fetching transformer data..."):
                                # Convert date to datetime for query
                                query_datetime = datetime.combine(selected_date, time(selected_hour))
                                results = data_service.get_transformer_data(
                                    query_datetime, 
                                    selected_hour,
                                    selected_feeder,
                                    selected_transformer
                                )
                                
                                if results is not None and not results.empty:
                                    logger.info("Displaying transformer dashboard...")
                                    display_transformer_dashboard(results, selected_hour)
                                else:
                                    st.warning("No data available for the selected criteria.")
                        except Exception as e:
                            logger.error(f"Error fetching data: {str(e)}\nTraceback: {traceback.format_exc()}")
                            st.error(f"Error fetching data: {str(e)}")
                
                if alert_clicked:
                    # Store alert preferences in session state
                    st.session_state.alert_settings = {
                        'transformer_id': selected_transformer,
                        'threshold': 80  # Default threshold
                    }
                    st.success(f"Alert set for transformer {selected_transformer}")
                
            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while loading the interface. Please try again.")
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please refresh the page and try again.")

if __name__ == "__main__":
    main()
