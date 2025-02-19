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

# App imports with app. prefix for cloud
from app.services.data_service import (
    get_transformer_ids_for_feeder,
    get_analysis_results,
    get_available_dates,
    get_transformer_options,
    get_customer_data,
    get_transformer_attributes
)
from app.services.alert_service import AlertService
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
from app.core.database import get_database_connection

# Configure the application
st.set_page_config(
    page_title="Transformer Loading Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Initialize database connection
if 'db_con' not in st.session_state:
    st.session_state.db_con = get_database_connection()

# Force light theme
st._config.set_option('theme.base', 'light')
st._config.set_option('theme.backgroundColor', '#ffffff')
st._config.set_option('theme.secondaryBackgroundColor', '#f8f9fa')
st._config.set_option('theme.textColor', '#2f4f4f')
st._config.set_option('theme.font', 'sans serif')

# Additional CSS for light theme
st.markdown("""
    <style>
        /* Global theme override */
        :root, .stApp, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: #2f4f4f !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
            border-right: 1px solid #e9ecef !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #2f4f4f !important;
        }
        
        /* Buttons */
        .stButton button {
            background-color: #f0f2f6 !important;
            color: #2f4f4f !important;
            border: 1px solid #d1d5db !important;
        }
        
        /* Inputs */
        .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: white !important;
            color: #2f4f4f !important;
        }
        
        /* Remove dark mode elements */
        [data-testid="stToolbar"], [data-testid="stDecoration"], footer {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Disable discovery cache warning
warnings.filterwarnings('ignore', message='file_cache is unavailable when using oauth2client >= 4.0.0')

@log_performance
def main():
    """Main application function for cloud environment"""
    
    # Display app title
    st.title("⚡ Transformer Loading Analysis")
    
    # Initialize alert service for cloud
    alert_service = CloudAlertService()
    
    # Sidebar
    with st.sidebar:
        st.header("Analysis Parameters")
        
        # Feeder selection
        feeder_options = ["feeder1", "feeder2", "feeder3", "feeder4"]
        selected_feeder = st.selectbox("Select Feeder", feeder_options)
        
        # Get transformer options for selected feeder
        transformer_options = get_transformer_options(selected_feeder)
        selected_transformer = st.selectbox("Select Transformer", transformer_options)
        
        # Date selection
        min_date, max_date = get_available_dates()
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
            format="%H:00"
        )
        
        # Alert button
        if st.button("Search & Alert"):
            with st.spinner("Analyzing transformer status..."):
                try:
                    results = get_analysis_results(
                        selected_transformer,
                        selected_date,
                        time_range=(selected_hour, selected_hour + 1)
                    )
                    if results is not None and not results.empty:
                        alert_service.process_and_send_alert(
                            results,
                            selected_transformer,
                            selected_date,
                            selected_hour
                        )
                except Exception as e:
                    st.error(f"Error processing alert: {str(e)}")
    
    # Main content
    try:
        # Get transformer data
        results = get_analysis_results(selected_transformer, selected_date)
        
        if results is not None and not results.empty:
            # Display transformer dashboard
            display_transformer_dashboard(results, selected_transformer)
            
            # Display loading status chart
            display_loading_status_line_chart(results)
            add_hour_indicator(selected_hour)
            
            # Display time series charts
            col1, col2 = st.columns(2)
            with col1:
                display_power_time_series(results)
                add_hour_indicator(selected_hour)
            with col2:
                display_current_time_series(results)
                add_hour_indicator(selected_hour)
            
            # Display voltage chart
            display_voltage_time_series(results)
            add_hour_indicator(selected_hour)
            
            # Get and display customer data
            customer_data = get_customer_data(selected_transformer, selected_date)
            if customer_data is not None and not customer_data.empty:
                st.subheader("Customer Information")
                st.dataframe(customer_data)
            
            # Get and display transformer attributes
            transformer_attrs = get_transformer_attributes(selected_transformer)
            if transformer_attrs is not None and not transformer_attrs.empty:
                st.subheader("Transformer Attributes")
                st.dataframe(transformer_attrs)
        else:
            st.warning("No data available for the selected transformer and date.")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    main()
