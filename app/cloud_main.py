"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""

import streamlit as st
import os
import sys
from pathlib import Path
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import logging
import plotly.graph_objects as go
from dateutil import parser
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set page config - must be first Streamlit command
st.set_page_config(page_title="Transformer Loading Analysis", layout="wide")

# App imports with app. prefix for cloud
from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.utils.logging_utils import Timer, logger, log_performance
from app.utils.cloud_environment_check import display_environment_status, is_cloud_ready
from app.visualization.charts import (
    display_loading_status_line_chart,
    display_power_time_series,
    display_current_time_series,
    display_voltage_time_series,
    display_loading_status,
    display_transformer_dashboard,
    add_hour_indicator
)

# Initialize services
try:
    logger.info("Initializing services...")
    data_service = CloudDataService()
    alert_service = CloudAlertService(data_service)
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}\nTraceback: {traceback.format_exc()}")
    st.error("Failed to initialize application services. Please check the logs for details.")
    st.stop()

# App imports with app. prefix for cloud
from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.utils.logging_utils import Timer, logger, log_performance
from app.utils.cloud_environment_check import display_environment_status, is_cloud_ready
from app.visualization.charts import (
    display_loading_status_line_chart,
    display_power_time_series,
    display_current_time_series,
    display_voltage_time_series,
    display_loading_status,
    display_transformer_dashboard,
    add_hour_indicator
)

# Initialize services
try:
    logger.info("Initializing services...")
    data_service = CloudDataService()
    alert_service = CloudAlertService(data_service)
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}\nTraceback: {traceback.format_exc()}")
    st.error("Failed to initialize application services. Please check the logs for details.")
    st.stop()

def create_tile(title: str, value: str, has_multiline_title: bool = False, is_clickable: bool = False):
    """Create a styled tile using Streamlit components"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 100%;
            {'cursor: pointer;' if is_clickable else ''}
        ">
            <h3 style="
                margin: 0;
                color: #6c757d;
                font-size: 0.9rem;
                font-weight: 600;
                {'white-space: normal;' if has_multiline_title else 'white-space: nowrap;'}
                overflow: hidden;
                text-overflow: ellipsis;
            ">{title}</h3>
            <p style="
                margin: 0.5rem 0 0 0;
                color: #212529;
                font-size: 1.1rem;
                font-weight: 500;
            ">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_banner(title: str):
    """Create a professional banner with title"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h1 style="
                margin: 0;
                color: #2f4f4f;
                font-size: 1.5rem;
                font-weight: 600;
                text-align: center;
            ">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

def create_section_banner(title: str):
    """Create a section banner with professional styling"""
    st.markdown(
        f"""
        <div style="
            background-color: #f8f9fa;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <h2 style="
                margin: 0;
                color: #2f4f4f;
                font-size: 1.2rem;
                font-weight: 600;
            ">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

@log_performance
def main():
    """Main application function for cloud environment"""
    try:
        # Create banner
        create_banner("Transformer Loading Analysis")
        
        # Sidebar for parameters
        with st.sidebar:
            st.header("Analysis Parameters")
            
            try:
                # Date selection
                logger.info("Getting available dates...")
                min_date, max_date = data_service.get_available_dates()
                logger.info(f"Got date range: {min_date} to {max_date}")
                
                selected_date = st.date_input(
                    "Select Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Hour selection
                selected_hour = st.slider(
                    "Select Hour",
                    min_value=0,
                    max_value=23,
                    value=12,
                    help="Select hour of the day (24-hour format)"
                )
                
                # Feeder selection
                logger.info("Getting feeder list...")
                feeders = data_service.get_feeder_list()
                logger.info(f"Found {len(feeders)} feeders")
                
                selected_feeder = st.selectbox(
                    "Select Feeder",
                    options=feeders,
                    format_func=lambda x: f"Feeder {x}"
                )
                
                if selected_feeder:
                    logger.info(f"Getting transformers for feeder {selected_feeder}...")
                    transformers = data_service.get_transformer_ids(selected_feeder)
                    logger.info(f"Found {len(transformers)} transformers")
                    
                    selected_transformer = st.selectbox(
                        "Select Transformer",
                        options=transformers
                    )
                    
                    if selected_transformer:
                        # Search & Alert button
                        if st.button("Search & Alert"):
                            with st.spinner("Processing..."):
                                logger.info(f"Getting data for transformer {selected_transformer}...")
                                results = data_service.get_transformer_data(selected_transformer, selected_date)
                                
                                if results is not None and not results.empty:
                                    # Process alerts
                                    logger.info("Processing alerts...")
                                    alert_sent = alert_service.process_alerts(
                                        results,
                                        selected_transformer,
                                        selected_date,
                                        selected_hour
                                    )
                                    
                                    if alert_sent:
                                        st.success("Alert processed successfully!")
                                    else:
                                        st.info("No alerts triggered for the selected criteria.")
                                else:
                                    st.warning("No data available for the selected transformer and date.")
            
            except Exception as e:
                logger.error(f"Error in sidebar: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while loading the sidebar. Please try again.")
                return
        
        # Main content area
        if selected_transformer:
            try:
                logger.info(f"Getting data for transformer {selected_transformer}...")
                results = data_service.get_transformer_data(selected_transformer, selected_date)
                
                if results is not None and not results.empty:
                    logger.info("Displaying transformer dashboard...")
                    display_transformer_dashboard(results, selected_hour)
                else:
                    st.warning("No data available for the selected transformer and date.")
            except Exception as e:
                logger.error(f"Error displaying dashboard: {str(e)}\nTraceback: {traceback.format_exc()}")
                st.error("An error occurred while displaying the dashboard. Please try again.")
        else:
            st.info("Please select a transformer to view analysis.")
            
    except Exception as e:
        logger.error(f"Main application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An unexpected error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()
