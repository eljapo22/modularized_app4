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
from app.services.cloud_data_service import data_service
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
    # Create banner
    create_banner("Transformer Loading Analysis")
    
    # Sidebar for parameters
    with st.sidebar:
        st.header("Analysis Parameters")
        
        # Date selection
        min_date, max_date = data_service.get_available_dates()  # Use method instead of property
        selected_date = st.date_input(
            "Select Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        # Hour selection
        selected_hour = st.selectbox(
            "Select Hour",
            range(24),
            format_func=lambda x: f"{x:02d}:00"
        )
        
        # Feeder selection
        available_feeders = data_service.get_feeder_list()
        selected_feeder = st.selectbox(
            "Select Feeder",
            available_feeders
        )
        
        # Get transformer options for selected feeder
        transformer_options = data_service.get_transformer_ids(int(selected_feeder.split()[-1]))
        selected_transformer = st.selectbox(
            "Select Transformer",
            transformer_options if transformer_options else ["No transformers available"]
        )
        
        # Search & Alert button
        if st.button("Search & Alert", type="primary"):
            with st.spinner("Processing data and sending alerts..."):
                # Get transformer data
                results = data_service.get_transformer_data(selected_transformer, selected_date)
                
                if results is not None and not results.empty:
                    # Initialize cloud alert service
                    alert_service = CloudAlertService()
                    
                    # Process alerts
                    alert_sent = alert_service.process_alerts(
                        results,
                        selected_date,
                        selected_hour
                    )
                    
                    if alert_sent:
                        st.success("Alerts processed and sent successfully!")
                    else:
                        st.info("No alerts needed at this time.")
                else:
                    st.error("No data available for selected parameters.")
    
    # Main content area
    if 'selected_transformer' in locals() and selected_transformer != "No transformers available":
        # Get transformer data
        results = data_service.get_transformer_data(selected_transformer, selected_date)
        
        if results is not None and not results.empty:
            # Create two columns for metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate metrics
            hour_data = results[results['timestamp'].dt.hour == selected_hour]
            if not hour_data.empty:
                current_loading = hour_data['loading_percentage'].iloc[0]
                power_factor = hour_data['power_factor'].iloc[0]
            else:
                current_loading = 0.0
                power_factor = 0.0
                
            max_loading = results['loading_percentage'].max()
            avg_loading = results['loading_percentage'].mean()
            
            # Display metrics in tiles
            with col1:
                create_tile("Current Loading", f"{current_loading:.1f}%")
            with col2:
                create_tile("Maximum Loading", f"{max_loading:.1f}%")
            with col3:
                create_tile("Average Loading", f"{avg_loading:.1f}%")
            with col4:
                create_tile("Power Factor", f"{power_factor:.2f}")
            
            # Display transformer dashboard
            display_transformer_dashboard(results, selected_hour)
            
            # Get and display customer data
            customer_data = data_service.get_customer_data(selected_transformer, selected_date)
            if customer_data is not None and not customer_data.empty:
                create_section_banner("Customer Data")
                
                # Calculate customer metrics
                total_customers = len(customer_data)
                avg_consumption = customer_data['consumption_kwh'].mean()
                peak_demand = customer_data['peak_demand_kw'].max()
                avg_pf = customer_data['power_factor'].mean()
                
                # Display customer metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    create_tile("Total Customers", str(total_customers))
                with col2:
                    create_tile("Avg. Consumption", f"{avg_consumption:.1f} kWh")
                with col3:
                    create_tile("Peak Demand", f"{peak_demand:.1f} kW")
                with col4:
                    create_tile("Avg. Power Factor", f"{avg_pf:.2f}")
                
                # Display customer data table
                from app.visualization.tables import display_customer_data
                display_customer_data(customer_data)
        else:
            st.warning("No data available for the selected transformer and date.")
    else:
        st.info("Please select a transformer to view analysis.")

if __name__ == "__main__":
    main()
