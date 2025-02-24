# Visualization components for the Transformer Loading Analysis Application

import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile, create_colored_banner, create_bordered_header
from app.config.constants import STATUS_COLORS
from app.config.table_config import DECIMAL_PLACES

# Configure logging
logger = logging.getLogger(__name__)

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps in a DataFrame"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status chart."""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status chart")
        return

    # Create a copy of the dataframe
    df = results_df.copy()
    
    # Ensure timestamp is datetime for x-axis
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    # Create colored loading percentage segments
    df['Critical (≥120%)'] = df['loading_percentage'].where(df['loading_percentage'] >= 120, None)
    df['Overloaded (≥100%)'] = df['loading_percentage'].where((df['loading_percentage'] >= 100) & (df['loading_percentage'] < 120), None)
    df['Warning (≥80%)'] = df['loading_percentage'].where((df['loading_percentage'] >= 80) & (df['loading_percentage'] < 100), None)
    df['Pre-Warning (≥50%)'] = df['loading_percentage'].where((df['loading_percentage'] >= 50) & (df['loading_percentage'] < 80), None)
    df['Normal (<50%)'] = df['loading_percentage'].where(df['loading_percentage'] < 50, None)
    
    # Create the line chart with native Streamlit colors
    st.line_chart(
        df[[
            'Critical (≥120%)',
            'Overloaded (≥100%)',
            'Warning (≥80%)',
            'Pre-Warning (≥50%)',
            'Normal (<50%)'
        ]],
        height=400,
        use_container_width=True
    )
    
    # Add color-coded legend below the chart
    legend_html = f"""
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 0.5rem;">
            <span style="color: {STATUS_COLORS['Critical']}">●</span> Critical (≥120%)
            <span style="color: {STATUS_COLORS['Overloaded']}">●</span> Overloaded (≥100%)
            <span style="color: {STATUS_COLORS['Warning']}">●</span> Warning (≥80%)
            <span style="color: {STATUS_COLORS['Pre-Warning']}">●</span> Pre-Warning (≥50%)
            <span style="color: {STATUS_COLORS['Normal']}">●</span> Normal (<50%)
        </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power consumption time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization.")
        return
    
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    
    # Create power chart
    st.line_chart(
        results_df['power_kw'],
        use_container_width=True
    )

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display current time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for current visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    
    # Create current chart
    st.line_chart(
        results_df['current_a'],
        use_container_width=True
    )

def display_voltage_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display voltage time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    
    # Create voltage chart
    st.line_chart(
        results_df['voltage_v'],
        use_container_width=True
    )

def display_power_factor_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power factor time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power factor visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    
    # Create power factor chart
    st.line_chart(
        results_df['power_factor'],
        use_container_width=True
    )

def display_power_consumption(results_df: pd.DataFrame):
    """Display power consumption visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)
        
        # Create power consumption chart
        st.line_chart(
            results_df['power_kw'],
            use_container_width=True
        )
        
    except Exception as e:
        logger.error(f"Error displaying power consumption chart: {str(e)}")
        st.error("Error displaying power consumption chart")

def display_transformer_dashboard(transformer_df: pd.DataFrame, customer_df: pd.DataFrame = None):
    # Display the transformer analysis dashboard
    if transformer_df is None or transformer_df.empty:
        st.warning("No data available for transformer dashboard.")
        return

    # Show customer analysis if tile was clicked
    if 'show_customer_analysis' in st.session_state and st.session_state.show_customer_analysis:
        st.session_state.show_customer_analysis = False  # Reset for next time
        if customer_df is not None:
            display_customer_tab(customer_df)
            return
        else:
            st.warning("No customer data available for this transformer.")
            return

    # Create metrics row
    cols = st.columns(4)
    
    # Current transformer info
    latest = transformer_df.iloc[-1]
    with cols[0]:
        create_tile(
            "Transformer ID",
            latest.get('transformer_id', 'N/A'),
            is_clickable=False
        )
    with cols[1]:
        # Get number of unique customers
        customer_count = len(customer_df['customer_id'].unique()) if customer_df is not None else 'N/A'
        if create_tile(
            "Customers",
            str(customer_count),
            is_clickable=True
        ):
            # Show customer analysis
            st.session_state.show_customer_analysis = True
            st.rerun()
    with cols[2]:
        create_tile(
            "Latitude",
            f"{latest.get('latitude', 'N/A')}",
            is_clickable=False
        )
    with cols[3]:
        create_tile(
            "Longitude",
            f"{latest.get('longitude', 'N/A')}",
            is_clickable=False
        )

    # Display transformer data
    display_transformer_data(transformer_df)

def display_customer_tab(df: pd.DataFrame):
    # Display customer analysis tab
    if df is None or df.empty:
        st.warning("No customer data available")
        return

    # Create customer selector
    customer_ids = sorted(df['customer_id'].unique())
    selected_customer = st.selectbox(
        "Select Customer",
        customer_ids,
        format_func=lambda x: f"Customer {x}"
    )

    # Filter data for selected customer
    customer_df = df[df['customer_id'] == selected_customer].copy()  # Create copy to avoid SettingWithCopyWarning
    
    # Round values according to spec
    customer_df['power_kw'] = customer_df['power_kw'].round(3)  # x.xxx
    customer_df['current_a'] = customer_df['current_a'].round(3)  # x.xxx
    customer_df['power_factor'] = customer_df['power_factor'].round(3)  # x.xxx
    customer_df['voltage_v'] = customer_df['voltage_v'].round(1)  # xxx.x

    # Display customer metrics in tiles
    cols = st.columns(4)
    latest = customer_df.iloc[-1]
    
    with cols[0]:
        create_tile(
            "Current (A)",
            f"{latest['current_a']:.{DECIMAL_PLACES['current_a']}f}",
            is_clickable=True
        )
    with cols[1]:
        create_tile(
            "Power Factor",
            f"{latest['power_factor']:.{DECIMAL_PLACES['power_factor']}f}",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Power (kW)",
            f"{latest['power_kw']:.{DECIMAL_PLACES['power_kw']}f}",
            is_clickable=True
        )
    with cols[3]:
        create_tile(
            "Power (kVA)",
            f"{latest['power_kva']:.{DECIMAL_PLACES['power_kva']}f}",
            is_clickable=True
        )
    
    # Display customer charts
    with st.container():
        create_colored_banner("Power Consumption")
        display_power_time_series(customer_df, is_transformer_view=False)

    cols = st.columns(2)
    with cols[0]:
        create_colored_banner("Current")
        display_current_time_series(customer_df, is_transformer_view=False)
    with cols[1]:
        create_colored_banner("Voltage")
        display_voltage_time_series(customer_df)

    # Display customer table
    st.markdown("### Customer Details")
    st.dataframe(
        customer_df[['timestamp', 'power_kw', 'power_factor', 'voltage_v', 'current_a']].sort_values('timestamp', ascending=False),
        use_container_width=True
    )

def display_transformer_data(results_df: pd.DataFrame):
    """Display transformer data visualizations in the same layout as customer tab."""
    if results_df is None or results_df.empty:
        st.warning("No data available for transformer visualization.")
        return

    # Ensure timestamp is datetime for all visualizations
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')

    # Power Consumption
    st.subheader("Power Consumption")
    st.line_chart(df['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current")
        st.line_chart(df['current_a'])
        
    with col2:
        st.subheader("Voltage")
        st.line_chart(df['voltage_v'])
    
    # Loading Status at the bottom
    st.subheader("Loading Status")
    df['loading_percentage'] = df['loading_percentage'].round(2)
    st.line_chart(df[['loading_percentage']], height=400, use_container_width=True)

def display_customer_data(results_df: pd.DataFrame):
    """Display customer data visualizations."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer visualization.")
        return

    # Power Consumption
    st.subheader("Power Consumption")
    df_power = results_df.copy()
    df_power['timestamp'] = pd.to_datetime(df_power['timestamp'])
    df_power = df_power.set_index('timestamp')
    st.line_chart(df_power['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current")
        df_current = results_df.copy()
        df_current['timestamp'] = pd.to_datetime(df_current['timestamp'])
        df_current = df_current.set_index('timestamp')
        st.line_chart(df_current['current_a'])
        
    with col2:
        st.subheader("Voltage")
        df_voltage = results_df.copy()
        df_voltage['timestamp'] = pd.to_datetime(df_voltage['timestamp'])
        df_voltage = df_voltage.set_index('timestamp')
        st.line_chart(df_voltage['voltage_v'])
