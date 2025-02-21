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
from app.visualization.charts import display_customer_tab, display_power_time_series, display_current_time_series, display_voltage_time_series

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize data service
        data_service = CloudDataService()
        logger.info("Services initialized successfully")

        # Get available date range
        min_date, max_date = data_service.get_available_dates()
        logger.info(f"Got date range: {min_date} to {max_date}")
            
        # Set page config
        st.set_page_config(
            page_title="Transformer Loading Analysis",
            page_icon="⚡",
            layout="wide"
        )
        
        create_banner("Transformer Loading Analysis")
        
        # Analysis Parameters in sidebar
        st.sidebar.header("Analysis Parameters")
        
        # Date range selection with default range
        dates = st.sidebar.date_input(
            "Select Date Range",
            value=[min_date, min_date],  # Pass as list for range selection
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
        
        # Ensure we have a start and end date
        if isinstance(dates, (datetime, date)):
            start_date = end_date = dates
        else:
            start_date, end_date = dates[0], dates[-1]  # Handle both list and tuple cases
        
        # Feeder and transformer selection
        feeder = st.sidebar.selectbox("Select Feeder", data_service.get_feeder_options())
        transformer_id = st.sidebar.selectbox(
            "Select Transformer",
            data_service.get_load_options(feeder)
        )
        
        # Search button
        search_clicked = st.sidebar.button("Search & Analyze")
        
        # Main content area for visualization
        main_container = st.container()
        with main_container:
            if search_clicked:
                if not all([start_date, end_date, feeder, transformer_id]):
                    st.error("Please select all required parameters")
                else:
                    logger.info(f"Fetching data for date range: {start_date} to {end_date}")
                    
                    # Get transformer data
                    transformer_data = data_service.get_transformer_data_range(
                        start_date,
                        end_date,
                        feeder,
                        transformer_id
                    )
                    if transformer_data is not None:
                        logger.info(f"Transformer data timestamp range: {transformer_data['timestamp'].min()} to {transformer_data['timestamp'].max()}")
                    
                    # Get customer data
                    customer_data = data_service.get_customer_data(
                        transformer_id,
                        start_date,
                        end_date
                    )
                    if customer_data is not None:
                        logger.info(f"Customer data timestamp range: {customer_data['timestamp'].min()} to {customer_data['timestamp'].max()}")
                    
                    if transformer_data is not None and not transformer_data.empty:
                        # Create tabs for transformer and customer data
                        tab1, tab2 = st.tabs(["Transformer Analysis", "Customer Analysis"])
                        
                        with tab1:
                            # Get unique customer count
                            customer_count = len(customer_data['customer_id'].unique()) if customer_data is not None else 0
                            
                            # Display transformer details
                            create_section_header("Transformer Details")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                create_tile("Transformer ID", transformer_id)
                            with col2:
                                create_tile("Customers", str(customer_count))
                            with col3:
                                create_tile("Latitude", "45.5123")  # Actual coordinate format
                            with col4:
                                create_tile("Longitude", "-79.3892")  # Actual coordinate format

                            # Display power consumption chart
                            create_section_header("Power Consumption Over Time")
                            display_power_time_series(transformer_data, is_transformer_view=True)

                            # Display current and voltage charts side by side
                            current_col, voltage_col = create_two_column_charts()
                            
                            with current_col:
                                create_section_header("Current Over Time")
                                display_current_time_series(transformer_data)
                                
                            with voltage_col:
                                create_section_header("Voltage Over Time")
                                display_voltage_time_series(transformer_data)
                        
                        with tab2:
                            if customer_data is not None and not customer_data.empty:
                                display_customer_tab(customer_data)
                            else:
                                st.warning("No customer data available for the selected criteria.")
                    else:
                        st.warning("No transformer data available for the selected criteria.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application")

if __name__ == "__main__":
    main()
