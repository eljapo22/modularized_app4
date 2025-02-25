# Visualization components for the Transformer Loading Analysis Application

import streamlit as st
import pandas as pd
import numpy as np
import logging
import plotly.graph_objects as go
from datetime import datetime, timedelta
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile, create_colored_banner, create_bordered_header
from app.config.constants import STATUS_COLORS, CHART_COLORS
from app.config.table_config import DECIMAL_PLACES

# Configure logging
logger = logging.getLogger(__name__)

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps in a DataFrame"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status chart showing loading percentages over time."""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status chart")
        return

    # Create a copy and ensure timestamp handling
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Debug: Check for duplicate timestamps
    duplicate_times = df[df.duplicated(subset=['timestamp'], keep=False)]
    if not duplicate_times.empty:
        st.warning("Found duplicate timestamps in data:")
        st.write(duplicate_times.sort_values('timestamp')[['timestamp', 'loading_percentage']].head(10))
    
    # Debug: Show value ranges
    st.write("Loading percentage range:", 
             f"Min: {df['loading_percentage'].min():.1f}%, ",
             f"Max: {df['loading_percentage'].max():.1f}%, ",
             f"Mean: {df['loading_percentage'].mean():.1f}%")
    
    df = df.sort_values('timestamp')  # Ensure data is sorted by time
    
    # Round loading percentages to 1 decimal place for consistent display
    df['loading_percentage'] = df['loading_percentage'].round(1)
    
    # Create the scatter plot
    fig = go.Figure()
    
    # Add scatter plot for loading percentages with explicit line and marker settings
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['loading_percentage'],
        mode='markers',  # Only show markers, no lines
        name='Loading %',
        marker=dict(
            size=6,
            color='blue',
            line=dict(width=1, color='darkblue')
        ),
        hovertemplate='<b>Loading:</b> %{y}%<br>' +
                     '<b>Time:</b> %{x}<br>' +
                     '<b>Power:</b> %{customdata[0]:.1f} kW<extra></extra>',
        customdata=df[['power_kw']],
        connectgaps=False,  # Don't connect gaps in data
        line=dict(width=0)  # Ensure no lines are drawn
    ))

    # Add horizontal lines for thresholds with labels
    thresholds = [
        (120, 'Critical', 'red'),
        (100, 'Overloaded', 'orange'),
        (80, 'Warning', 'yellow'),
        (50, 'Pre-Warning', 'purple'),
    ]

    for threshold, label, color in thresholds:
        # Add horizontal line
        fig.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=threshold,
            y1=threshold,
            xref="paper",
            yref="y",
            line=dict(
                color=color,
                width=1,
                dash="dash",
            )
        )
        # Add label
        fig.add_annotation(
            text=f"{label} ≥ {threshold}%",
            xref="paper",
            yref="y",
            x=1.02,
            y=threshold,
            showarrow=False,
            font=dict(size=10)
        )

    # Update layout with explicit time axis settings
    fig.update_layout(
        title=dict(text="Loading Status", x=0.5),
        xaxis=dict(
            title="Time",
            showgrid=True,
            type='date',
            tickformat='%Y-%m-%d %H:%M',
            dtick='H2'  # Show tick every 2 hours
        ),
        yaxis=dict(
            title="Loading Percentage (%)",
            showgrid=True,
            range=[0, max(125, df['loading_percentage'].max() * 1.1)]
        ),
        height=500,
        showlegend=False,
        margin=dict(r=150),  # Add right margin for threshold labels
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power consumption time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization.")
        return
    
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.sort_values('timestamp')  # Sort by timestamp
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
    results_df = results_df.sort_values('timestamp')  # Sort by timestamp
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
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')
    
    # Create mock data for 3 phases based on actual voltage
    voltage_data = pd.DataFrame(index=df.index)
    voltage_data['[0]Phase A'] = df['voltage_v']  # Original data
    voltage_data['[1]Phase B'] = df['voltage_v'] * 0.98  # Slightly lower
    voltage_data['[2]Phase C'] = df['voltage_v'] * 1.02  # Slightly higher
    
    # Create voltage chart with all phases
    st.line_chart(voltage_data)

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
            "Power (kW)",
            f"{latest['power_kw']:.{DECIMAL_PLACES['power_kw']}f}",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Power (kVA)",
            f"{latest['power_kva']:.{DECIMAL_PLACES['power_kva']}f}",
            is_clickable=True
        )
    with cols[3]:
        create_tile(
            "Voltage (V)",
            f"{latest['voltage_v']:.{DECIMAL_PLACES['voltage_v']}f}",
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
        customer_df[['timestamp', 'power_kw', 'current_a', 'voltage_v']].sort_values('timestamp', ascending=False),
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
    df = df.sort_values('timestamp')  # Sort by timestamp
    
    # Loading Status at the top
    st.markdown("""
        <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <h3 style='margin: 0px; color: #262626; font-size: 18px'>Loading Status</h3>
        </div>
    """, unsafe_allow_html=True)
    display_loading_status(df)

    # Power Consumption
    st.markdown("""
        <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <h3 style='margin: 0px; color: #262626; font-size: 18px'>Power Consumption</h3>
        </div>
    """, unsafe_allow_html=True)
    df = df.set_index('timestamp')
    st.line_chart(df['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
                <h3 style='margin: 0px; color: #262626; font-size: 18px'>Current</h3>
            </div>
        """, unsafe_allow_html=True)
        st.line_chart(df['current_a'])
        
    with col2:
        st.markdown("""
            <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
                <h3 style='margin: 0px; color: #262626; font-size: 18px'>Voltage</h3>
            </div>
        """, unsafe_allow_html=True)
        st.line_chart(df['voltage_v'])

def display_customer_data(results_df: pd.DataFrame):
    """Display customer data visualizations."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer visualization.")
        return

    # Display mock coordinates
    st.markdown("""
        <div style='padding: 10px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <p style='margin: 0; color: #666666; font-size: 14px'>X: 43.6532° N, Y: 79.3832° W</p>
        </div>
    """, unsafe_allow_html=True)

    # Power Consumption
    create_colored_banner("Power Consumption")
    df_power = results_df.copy()
    df_power['timestamp'] = pd.to_datetime(df_power['timestamp'])
    df_power = df_power.sort_values('timestamp')  # Sort by timestamp
    df_power = df_power.set_index('timestamp')
    st.line_chart(df_power['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        create_colored_banner("Current")
        df_current = results_df.copy()
        df_current['timestamp'] = pd.to_datetime(df_current['timestamp'])
        df_current = df_current.sort_values('timestamp')  # Sort by timestamp
        df_current = df_current.set_index('timestamp')
        st.line_chart(df_current['current_a'])
        
    with col2:
        create_colored_banner("Voltage")
        df_voltage = results_df.copy()
        df_voltage['timestamp'] = pd.to_datetime(df_voltage['timestamp'])
        df_voltage = df_voltage.sort_values('timestamp')  # Sort by timestamp
        df_voltage = df_voltage.set_index('timestamp')
        st.line_chart(df_voltage['voltage_v'])
