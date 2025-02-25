"""
Cloud-specific entry point for the Transformer Loading Analysis Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import logging.handlers
import traceback
import plotly.express as px
import sys
from pathlib import Path

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

# Add the app directory to Python path
app_dir = str(Path(__file__).parent)
if app_dir not in sys.path:
    sys.path.append(app_dir)
    logger.info(f"Added {app_dir} to Python path")

# Import services after logging is configured
from app.services.services import CloudDataService, CloudAlertService
from app.visualization.charts import display_transformer_dashboard
from app.utils.performance import log_performance
from app.utils.ui_components import (
    create_tile, 
    create_banner, 
    create_section_banner
)

# Configure page - must be first Streamlit command
st.set_page_config(page_title="Transformer Loading Analysis", layout="wide")

# Add custom CSS for tabs and sidebar
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
    }
    section[data-testid="stSidebar"] > div {
        background-color: #F0F2F6;
        padding-top: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    div[data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }
    div[data-testid="stSidebarNav"]::before {
        content: "Navigation";
        margin-left: 20px;
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@log_performance
def main():
    """Main application function for cloud environment"""
    try:
        # Initialize services
        data_service = CloudDataService()
        alert_service = CloudAlertService()
        
        # Create header banner
        create_banner("Transformer Loading Analysis Dashboard")
        
        # Handle URL parameters from alert links
        params = st.experimental_get_query_params()
        alert_view = params.get("view", [""])[0] == "alert"
        alert_transformer = params.get("id", [None])[0]
        start_date_param = params.get("start_date", [None])[0]
        end_date_param = params.get("end_date", [None])[0]
        hour_param = params.get("hour", [None])[0]
        feeder_param = params.get("feeder", [None])[0]

        logger.info(f"URL Parameters: view={alert_view}, id={alert_transformer}, start_date={start_date_param}, end_date={end_date_param}, hour={hour_param}, feeder={feeder_param}")

        # Set initial values from alert parameters
        initial_hour = int(hour_param) if hour_param else None
        initial_date = datetime.fromisoformat(start_date_param).date() if start_date_param else None
        initial_end_date = datetime.fromisoformat(end_date_param).date() if end_date_param else None
        initial_feeder = int(feeder_param) if feeder_param else None

        logger.info(f"Initial Values: Date={initial_date}, End Date={initial_end_date}, Hour={initial_hour}, Feeder={initial_feeder}, Transformer={alert_transformer}")

        # Get feeder from transformer ID if coming from alert
        initial_feeder = int(alert_transformer[2]) if alert_transformer and len(alert_transformer) >= 3 else initial_feeder

        # Store the alert parameters in session state to persist across reruns
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.initial_date = initial_date
            st.session_state.initial_end_date = initial_end_date
            st.session_state.initial_hour = initial_hour
            if alert_transformer:
                st.session_state.alert_transformer = alert_transformer
            else:
                st.session_state.alert_transformer = None
            st.session_state.initial_feeder = initial_feeder
            
        # Create sidebar with search criteria
        with st.sidebar:
            st.markdown("## Analysis Parameters")
            
            # Date Range selection
            st.markdown("### Date Range")
            selected_start_date = st.date_input(
                "Start Date",
                value=st.session_state.initial_date,
                key="start_date_selector"
            )
            
            selected_end_date = st.date_input(
                "End Date",
                value=selected_start_date + timedelta(days=30),
                key="end_date_selector"
            )
            
            # Hour selection
            selected_hour = st.number_input(
                "Select Hour (0-23)",
                min_value=0,
                max_value=23,
                value=st.session_state.initial_hour,
                key="hour_selector"
            )
            
            # Feeder selection
            st.markdown("### Feeder Selection")
            selected_feeder = st.selectbox(
                "Select Feeder",
                options=[1, 2, 3, 4],
                index=st.session_state.initial_feeder - 1,
                key="feeder_selector"
            )
            
            # Transformer selection
            st.markdown("### Transformer Selection")
            transformers = data_service.get_transformer_ids(selected_feeder)
            if st.session_state.alert_transformer in transformers:
                transformer_index = transformers.index(st.session_state.alert_transformer)
            else:
                transformer_index = 0
                
            selected_transformer = st.selectbox(
                "Select Transformer",
                options=transformers,
                index=transformer_index,
                key="transformer_selector"
            )
            
            # Alert button
            st.markdown("---")
            st.markdown("## Alerts")
            search_clicked = st.button("Search & Alert", key="alert_button")

        # Automatically trigger search if coming from alert link
        if alert_view or search_clicked:
            logger.info(f"Alert view triggered. alert_view={alert_view}, search_clicked={search_clicked}")
            with st.spinner("Loading data..."):
                # Get and display transformer data
                transformer_data = data_service.get_transformer_data(
                    date=selected_start_date,
                    hour=selected_hour,
                    feeder=f"Feeder {selected_feeder}",
                    transformer_id=selected_transformer
                )

                if transformer_data is not None:
                    logger.info(f"Data loaded successfully. Shape: {transformer_data.shape}")
                    # Display transformer data
                    st.markdown("## Transformer Data")
                    st.dataframe(transformer_data)
                    
                    # Display loading chart
                    if 'loading_percentage' in transformer_data.columns:
                        st.markdown("## Loading Chart")
                        fig = px.line(transformer_data, x='timestamp', y='loading_percentage',
                                    title=f'Loading Percentage for {selected_transformer}')
                        st.plotly_chart(fig)
                else:
                    logger.error("No data returned from get_transformer_data")
                    st.error("No data available for the selected parameters")

                # If search button was clicked, check for alerts
                if search_clicked:
                    # Get data for the entire date range
                    logger.info("=== Search & Alert Parameters ===")
                    logger.info(f"Start Date: {selected_start_date}")
                    logger.info(f"End Date: {selected_end_date}")
                    logger.info(f"Hour: {selected_hour}")
                    logger.info(f"Feeder: {selected_feeder}")
                    logger.info(f"Transformer: {selected_transformer}")
                    logger.info("============================")

                    # Fetch data with selected parameters
                    logger.info("Fetching data for selected parameters...")
                    date_range_data = data_service.get_transformer_data_by_range(
                        selected_transformer,
                        selected_start_date,
                        selected_end_date,
                        selected_hour,
                        selected_feeder
                    )
                    
                    # Get values directly from sidebar
                    url_params = {
                        'view': 'alert',
                        'id': selected_transformer,
                        'start_date': selected_start_date.isoformat(),
                        'end_date': selected_end_date.isoformat(),
                        'hour': str(selected_hour),
                        'feeder': str(selected_feeder)
                    }
                    logger.info("Setting URL parameters:")
                    for key, value in url_params.items():
                        logger.info(f"  {key}: {value}")
                    
                    # Update query parameters to match sidebar
                    st.experimental_set_query_params(**url_params)
                    
                    # Send alert with the sidebar selections
                    logger.info("Triggering alert with search parameters...")
                    alert_service.check_and_send_alerts(
                        date_range_data,
                        start_date=selected_start_date,
                        end_date=selected_end_date,
                        hour=selected_hour,
                        feeder=selected_feeder
                    )

                # Loading Status
                st.subheader("Loading Status")
                fig_loading = px.line(transformer_data, x='timestamp', y='loading_percentage')
                st.plotly_chart(fig_loading, use_container_width=True)

                # Power Consumption
                st.subheader("Power Consumption")
                fig_power = px.line(transformer_data, x='timestamp', y='power_consumption')
                st.plotly_chart(fig_power, use_container_width=True)

                # Current and Voltage
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Current")
                    fig_current = px.line(transformer_data, x='timestamp', y='current')
                    st.plotly_chart(fig_current, use_container_width=True)
                with col2:
                    st.subheader("Voltage")
                    fig_voltage = px.line(transformer_data, x='timestamp', y='voltage')
                    st.plotly_chart(fig_voltage, use_container_width=True)

            if search_clicked:  # Only show success message if manually clicked
                st.success("Search completed!")

        # Create main content area with tabs
        tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Data"])
        
        with tab1:
            # Display transformer dashboard
            display_transformer_dashboard(
                data_service,
                selected_transformer,
                selected_start_date,
                selected_hour,
                selected_feeder
            )
        
        with tab2:
            # Create data section
            create_section_banner("Raw Data")
            
            # Get and display transformer data
            transformer_data = data_service.get_transformer_data(
                date=selected_start_date,
                hour=selected_hour,
                feeder=f"Feeder {selected_feeder}",
                transformer_id=selected_transformer
            )
            if transformer_data is not None:
                st.dataframe(transformer_data)
            else:
                st.warning("No transformer data available for the selected parameters.")
            
            # Get and display customer data
            customer_data = data_service.get_customer_data(
                selected_transformer,
                selected_start_date,
                selected_hour
            )
            if customer_data is not None:
                st.dataframe(customer_data)
            else:
                st.warning("No customer data available for the selected parameters.")
    
    except Exception as e:
        st.error("An error occurred while running the application.")
        logging.error(f"Application error: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
