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
from app.visualization.charts import display_transformer_dashboard
from app.utils.ui_components import create_tile, create_banner, create_section_banner
from app.utils.performance import log_performance

# Configure page - must be first Streamlit command
st.set_page_config(page_title="Transformer Loading Analysis", layout="wide")

# Add custom CSS for tabs and sidebar
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        color: #6c757d;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e9ecef;
        color: #212529;
    }
    
    /* Sidebar styling */
    .css-1d391kg {  /* Sidebar */
        background-color: white;
    }
    .css-1544g2n {  /* Sidebar content */
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    [data-testid="stExpander"] {
        border: 1px solid #dee2e6;
        border-radius: 4px;
        background-color: white;
    }
</style>""", unsafe_allow_html=True)

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
data_service = None
alert_service = None

@log_performance
def main():
    """Main application function for cloud environment"""
    global data_service, alert_service
    
    try:
        # Initialize services if not already initialized
        if data_service is None or alert_service is None:
            logger.info("Initializing services...")
            data_service = CloudDataService()
            alert_service = CloudAlertService(data_service)
            logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("Failed to initialize application services. Please check the logs for details.")
        st.stop()

    try:
        # Create banner
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.markdown("### Search Controls")
            
            try:
                # Get available date range
                logger.info("Getting available dates...")
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
                logger.info("Getting feeder list...")
                feeder_options = data_service.get_feeder_options()
                logger.info(f"Found {len(feeder_options)} feeders")
                
                # Feeder selection
                selected_feeder = st.selectbox(
                    "Feeder",
                    options=feeder_options
                )
                
                if selected_feeder:
                    # Get load options for selected feeder
                    load_options = data_service.get_load_options(selected_feeder)
                    logger.info(f"Found {len(load_options)} load numbers for feeder {selected_feeder}")
                    
                    # Load number selection
                    selected_load = st.selectbox(
                        "Load Number",
                        options=load_options
                    )
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        search_clicked = st.button("Search", use_container_width=True)
                    with col2:
                        merge_clicked = st.button("Merge", use_container_width=True)
                    
                    # Reset Data Configuration
                    with st.expander("Reset Data Configuration"):
                        st.checkbox("Reset on next search")
                    
                    # Handle search action
                    if search_clicked and selected_load:
                        results_df = data_service.get_transformer_data(
                            selected_date,
                            selected_hour,
                            selected_feeder,
                            selected_load
                        )
                        
                        if results_df is not None and not results_df.empty:
                            display_transformer_dashboard(results_df, selected_hour)
                        else:
                            st.warning("No data available for the selected criteria.")
            
            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while loading the interface. Please try again.")
        
        # Main content area
        if selected_load:
            try:
                logger.info(f"Getting data for load {selected_load}...")
                results = data_service.get_transformer_data(selected_date, selected_hour, selected_feeder, selected_load)
                
                if results is not None and not results.empty:
                    logger.info("Displaying transformer dashboard...")
                    display_transformer_dashboard(results, selected_hour)
                else:
                    st.warning("No data available for the selected load and date.")
            except Exception as e:
                logger.error(f"Error displaying dashboard: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while displaying the dashboard. Please try again.")
        else:
            st.info("Please select a load to view analysis.")
            
    except Exception as e:
        logger.error(f"Main application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()
