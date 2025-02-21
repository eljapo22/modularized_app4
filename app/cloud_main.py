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
from app.utils.ui_utils import create_banner, display_transformer_dashboard
from app.utils.ui_components import create_section_header, create_tile, create_two_column_charts
from app.visualization.charts import display_power_time_series, display_current_time_series, display_voltage_time_series

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
        # Track session start
        logger.info("=== Starting new analysis session ===")
        
        # Initialize services
        data_service = CloudDataService()
        
        # Sidebar
        st.sidebar.title("Transformer Selection")
        
        # Get available transformer IDs
        transformer_ids = data_service.get_transformer_ids()
        transformer_id = st.sidebar.selectbox("Select Transformer", transformer_ids)
        
        if transformer_id:
            # Get data
            df = data_service.get_transformer_data(transformer_id)
            
            if not df.empty:
                st.title(f"Transformer Analysis: {transformer_id}")
                
                # Display power consumption over time
                display_power_time_series(df)
                
                # Display current and voltage in two columns
                create_two_column_charts(
                    df,
                    display_current_time_series,
                    display_voltage_time_series
                )
            else:
                st.warning("No data available for selected transformer.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application")

if __name__ == "__main__":
    main()
