# Visualization components for the Transformer Loading Analysis Application

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile
from app.config.constants import STATUS_COLORS
from app.config.table_config import DECIMAL_PLACES

# Configure logging
logger = logging.getLogger(__name__)

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps in a DataFrame"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def create_base_figure(title: str, xaxis_title: str, yaxis_title: str):
    # Create a base plotly figure with common settings
    fig = go.Figure()
    
    # Update layout with common settings
    layout_updates = {
        'xaxis': {
            'title': xaxis_title,
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#f0f0f0'
        },
        'yaxis': {
            'title': yaxis_title,
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#f0f0f0'
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'margin': dict(t=30, b=0, l=0, r=0)
    }
    
    fig.update_layout(**layout_updates)
    return fig

def display_loading_status_line_chart(results_df: pd.DataFrame):
    """Display loading status as a line chart with threshold indicators."""
    try:
        # Ensure timestamp is in datetime format
        results_df = results_df.copy()
        results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
        
        # Create the line chart
        fig = create_base_figure(
            title="Loading Status Over Time",
            xaxis_title="Time",
            yaxis_title="Loading (%)"
        )
        
        # Add loading percentage line
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['loading_percentage'],
            mode='lines+markers',
            name='Loading %',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=6)
        ))
        
        # Add threshold lines
        thresholds = [
            (120, 'Critical', '#dc3545'),
            (100, 'Overloaded', '#fd7e14'),
            (80, 'Warning', '#ffc107'),
            (50, 'Pre-Warning', '#6f42c1')
        ]
        
        for threshold, label, color in thresholds:
            fig.add_hline(
                y=threshold,
                line_dash="dot",
                line_color=color,
                annotation_text=f"{label} ({threshold}%)",
                annotation_position="left"
            )
        
        # Update layout
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=150)  # Extra right margin for threshold labels
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying loading status chart: {str(e)}")
        st.error("Error displaying loading status chart")

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status chart."""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.set_index('timestamp')
    
    # Create loading percentage chart
    st.line_chart(
        results_df['loading_percentage'],
        use_container_width=True
    )

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
        
        # Create figure
        fig = create_base_figure(
            title="Power Consumption Over Time",
            xaxis_title="Time",
            yaxis_title="Power (kW)"
        )
        
        # Add power consumption line
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_kw'],
            mode='lines+markers',
            name='Power (kW)',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=6)
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying power consumption chart: {str(e)}")
        st.error("Error displaying power consumption chart")

def display_transformer_dashboard(transformer_df: pd.DataFrame):
    # Display the transformer analysis dashboard
    if transformer_df is None or transformer_df.empty:
        st.warning("No data available for transformer dashboard.")
        return

    # Get customer data
    data_service = CloudDataService()
    customer_df = data_service.get_customer_data(
        transformer_df['transformer_id'].iloc[0],
        pd.to_datetime(transformer_df['timestamp'].iloc[0]).date(),
        pd.to_datetime(transformer_df['timestamp'].iloc[-1]).date()
    )
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Transformer Analysis", "Customer Analysis"])

    with tab1:
        display_transformer_tab(transformer_df)

    with tab2:
        if customer_df is not None:
            display_customer_tab(customer_df)
        else:
            st.warning("No customer data available for this transformer")

def display_transformer_tab(df: pd.DataFrame):
    # Display transformer analysis tab
    if df is None or df.empty:
        st.warning("No data available for transformer analysis.")
        return

    # Create metrics row
    cols = st.columns(4)
    
    # Current loading metrics
    latest = df.iloc[-1]
    with cols[0]:
        create_tile(
            "Loading Status",
            f"{latest['loading_percentage']:.{DECIMAL_PLACES['loading_percentage']}f}%",
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

    # Create section for loading status
    st.markdown("### Loading Status")
    with st.container():
        create_tile("Loading Status Over Time", "")
        display_loading_status_line_chart(df)

    # Create section for power analysis
    st.markdown("### Power Analysis")
    with st.container():
        create_tile("Power Consumption Over Time", "")
        display_power_time_series(df, is_transformer_view=True)

    # Create section for voltage and current
    st.markdown("### Voltage and Current")
    cols = st.columns(2)
    with cols[0]:
        create_tile("Current Over Time", "")
        display_current_time_series(df, is_transformer_view=True)
    with cols[1]:
        create_tile("Voltage Over Time", "")
        display_voltage_time_series(df)

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
    st.markdown("### Power Consumption")
    with st.container():
        create_tile("Power Over Time", "")
        display_power_time_series(customer_df, is_transformer_view=False)

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Current")
        create_tile("Current Over Time", "")
        display_current_time_series(customer_df, is_transformer_view=False)
    with cols[1]:
        st.markdown("### Voltage")
        create_tile("Voltage Over Time", "")
        display_voltage_time_series(customer_df)

    # Display customer table
    st.markdown("### Customer Details")
    st.dataframe(
        customer_df[['timestamp', 'power_kw', 'power_factor', 'voltage_v', 'current_a']].sort_values('timestamp', ascending=False),
        use_container_width=True
    )

def get_sample_voltage_data(df):
    # Generate sample three-phase voltage data
    if df is None or df.empty:
        return pd.DataFrame()

    # Create a 24-hour time range with hourly points
    if isinstance(df.index[0], (int, float)):
        # If index is numeric, create a 24-hour range from midnight
        start_time = pd.Timestamp.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # If index is timestamp, use its date
        start_time = pd.Timestamp(df.index[0]).replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_time = start_time + pd.Timedelta(days=1)
    time_index = pd.date_range(start=start_time, end=end_time, freq='5T')  # 5-minute intervals
    
    # Generate sample voltage data
    n_points = len(time_index)
    t = np.linspace(0, 8*np.pi, n_points)  # Increase cycles for 24-hour period
    
    # Base voltage with some random fluctuation
    base_voltage = 120
    noise_level = 0.5
    
    # Generate three phases with 120-degree shifts and realistic fluctuation
    # Add slow variation over 24 hours
    daily_variation = 1 * np.sin(np.linspace(0, 2*np.pi, n_points))  # ±1V daily swing
    
    phase_a = base_voltage + daily_variation + 2*np.sin(t) + noise_level * np.random.randn(n_points)
    phase_b = base_voltage + daily_variation + 2*np.sin(t + 2*np.pi/3) + noise_level * np.random.randn(n_points)
    phase_c = base_voltage + daily_variation + 2*np.sin(t + 4*np.pi/3) + noise_level * np.random.randn(n_points)
    
    # Ensure voltages stay within realistic bounds
    phase_a = np.clip(phase_a, 117, 123)
    phase_b = np.clip(phase_b, 117, 123)
    phase_c = np.clip(phase_c, 117, 123)
    
    return pd.DataFrame({
        'Red Phase': phase_a,
        'Yellow Phase': phase_b,
        'Blue Phase': phase_c
    }, index=time_index)

def display_voltage_over_time(results_df: pd.DataFrame):
    # Display voltage over time chart
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage over time visualization. Please check your database connection and try again.")
        return

    # Create sample voltage data
    voltage_df = get_sample_voltage_data(results_df)
    
    # Create figure
    fig = go.Figure()
    
    # Add voltage traces
    fig.add_trace(go.Scatter(
        x=voltage_df.index,
        y=voltage_df['Red Phase'],
        name='Red Phase',
        line=dict(color='red', width=1)
    ))
    
    fig.add_trace(go.Scatter(
        x=voltage_df.index,
        y=voltage_df['Yellow Phase'],
        name='Yellow Phase',
        line=dict(color='#FFD700', width=1)  # Dark yellow for better visibility
    ))
    
    fig.add_trace(go.Scatter(
        x=voltage_df.index,
        y=voltage_df['Blue Phase'],
        name='Blue Phase',
        line=dict(color='blue', width=1)
    ))
    
    # Add nominal voltage line
    fig.add_hline(
        y=120,
        line_dash="dash",
        line_color="gray",
        annotation_text="Nominal (120V)",
        annotation_position="right"
    )
    
    # Add +5% limit line (126V)
    fig.add_hline(
        y=126,
        line_dash="dash",
        line_color="red",
        annotation_text="+5% (126V)",
        annotation_position="right"
    )
    
    # Add -5% limit line (114V)
    fig.add_hline(
        y=114,
        line_dash="dash",
        line_color="red",
        annotation_text="-5% (114V)",
        annotation_position="right"
    )
    
    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=100, t=0, b=0),  # Add right margin for annotations
        height=250,
        yaxis=dict(
            title=dict(
                text="Voltage (V)",
                font=dict(size=12),
                standoff=25
            ),
            range=[110, 130],  # Expanded range to show limits clearly
            automargin=True,
            gridcolor='#E1E1E1',  # Darker grey for y-axis grid
            gridwidth=1,
            showgrid=True,
            tickformat='.1f'  # Match rounding precision
        ),
        xaxis=dict(
            tickformat='%Y-%m-%d %H:%M',  # Show full datetime
            dtick=3*3600000,  # Show tick every 3 hours (in milliseconds)
            tickangle=0,
            gridcolor='#E1E1E1',  # Darker grey for x-axis grid
            gridwidth=1,
            showgrid=True
        ),
        showlegend=False,
        plot_bgcolor='white'  # White background to make grid more visible
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_transformer_data(results_df: pd.DataFrame):
    """Display transformer data visualizations in the same layout as customer tab."""
    if results_df is None or results_df.empty:
        st.warning("No data available for transformer visualization.")
        return

    # Power Consumption
    st.subheader("Power Consumption")
    display_power_time_series(results_df, is_transformer_view=True)

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current")
        display_current_time_series(results_df, is_transformer_view=True)
        
    with col2:
        st.subheader("Voltage")
        display_voltage_time_series(results_df, is_transformer_view=True)

def display_customer_data(results_df: pd.DataFrame):
    """Display customer data visualizations."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer visualization.")
        return

    # Power Consumption
    st.subheader("Power Consumption")
    display_power_time_series(results_df)

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current")
        display_current_time_series(results_df)
        
    with col2:
        st.subheader("Voltage")
        display_voltage_time_series(results_df)
