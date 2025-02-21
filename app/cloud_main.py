"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import traceback
from datetime import datetime, date, timedelta
import pandas as pd

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService  # Import for alert functionality
from app.utils.ui_utils import create_banner, display_transformer_dashboard
from app.utils.ui_components import create_section_header, create_tile, create_two_column_charts
from app.visualization.charts import display_customer_tab, display_power_time_series, display_current_time_series, display_voltage_time_series, display_loading_status

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('transformer_alerts.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize alert state
        if 'alert_state' not in st.session_state:
            st.session_state.alert_state = {
                'pending': False,
                'transformer_id': None,
                'loading': None,
                'timestamp': None
            }
        
        # Handle deep link parameters
        params = st.experimental_get_query_params()
        
        # If coming from alert link, pre-populate selections
        if 'view' in params and params['view'][0] == 'alert':
            transformer_id = params.get('id', [None])[0]
            feeder = params.get('feeder', ['Feeder 1'])[0]
            start_date = datetime.fromisoformat(params.get('start', [None])[0]).date() if 'start' in params else None
            end_date = datetime.fromisoformat(params.get('end', [None])[0]).date() if 'end' in params else None
            auto_search = params.get('auto_search', ['false'])[0].lower() == 'true'
            
            # Store in session state
            if 'selections' not in st.session_state:
                st.session_state.selections = {
                    'transformer_id': transformer_id,
                    'feeder': feeder,
                    'start_date': start_date,
                    'end_date': end_date,
                    'auto_search': auto_search
                }
        
        # Track session start
        logger.info("=== Starting new analysis session ===")
        
        # Initialize services
        data_service = CloudDataService()
        
        # Sidebar
        st.sidebar.title("Transformer Selection")
        
        # Get available transformer IDs
        transformer_ids = data_service.get_transformer_ids()
        transformer_id = st.sidebar.selectbox("Select Transformer", transformer_ids)
        
        # Add toggle for chart type
        chart_type = st.sidebar.radio(
            "Select Chart Type",
            ["Power Consumption Over Time", "Loading Condition Status"]
        )
        
        if transformer_id:
            # Get data
            df = data_service.get_transformer_data(transformer_id)
            
            if not df.empty:
                st.title(f"Transformer Analysis: {transformer_id}")
                
                # Display appropriate chart based on selection
                if chart_type == "Power Consumption Over Time":
                    display_power_time_series(df)
                else:
                    display_loading_status(df)
            else:
                st.warning("No data available for selected transformer.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application")

if __name__ == "__main__":
    main()
