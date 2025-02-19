"""
Local-specific entry point for the Transformer Loading Analysis Application
Uses direct imports that work in local environment
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

# Direct imports for local environment
from services.data_service import (
    get_transformer_ids_for_feeder,
    get_analysis_results,
    get_available_dates,
    get_transformer_options,
    get_customer_data,
    get_transformer_attributes
)
from services.alert_service import AlertService
from services.local_alert_service import LocalAlertService
from utils.logging_utils import Timer, logger, log_performance
from utils.cloud_environment_check import display_environment_status, is_cloud_ready
from visualization.charts import (
    display_loading_status_line_chart,
    display_power_time_series,
    display_current_time_series,
    display_voltage_time_series,
    display_loading_status,
    display_transformer_dashboard,
    add_hour_indicator
)

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

@log_performance
def main():
    """Main application function for local environment"""
    # Rest of the main function code...
    # (Copy the existing main function but ensure imports don't use app. prefix)

if __name__ == "__main__":
    main()
