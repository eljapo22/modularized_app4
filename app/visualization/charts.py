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

# Configure logging
logger = logging.getLogger(__name__)

def add_hour_indicator(fig, selected_hour: int, y_range: tuple = None):
    """Add a vertical line indicator for the selected hour to any Plotly figure."""
    if selected_hour is None or not isinstance(selected_hour, int):
        logger.warning("Selected hour is invalid, skipping hour indicator")
        return

    if not fig.data or len(fig.data) == 0:
        logger.warning("No x-axis data found for hour indicator")
        return

    x_data = fig.data[0].x  # Assuming first trace has the timestamps
    if not isinstance(x_data, (list, np.ndarray)) or len(x_data) == 0:
        logger.warning("No x-axis data found for hour indicator")
        return

    try:
        # Convert the first timestamp to pandas Timestamp and normalize to start of day
        first_timestamp = pd.to_datetime(x_data[0]).normalize()
        if pd.isna(first_timestamp):
            logger.warning("First timestamp is NaT, skipping hour indicator")
            return

        # Calculate the indicator time using Timedelta
        indicator_time = first_timestamp + pd.Timedelta(hours=selected_hour)
        
        # Get y-axis range if not provided
        if y_range is None:
            y_min = min(trace.y.min() for trace in fig.data)
            y_max = max(trace.y.max() for trace in fig.data)
            y_padding = (y_max - y_min) * 0.1
            y_range = (y_min - y_padding, y_max + y_padding)

        # Add vertical line as a shape
        fig.add_shape(
            type="line",
            x0=indicator_time,
            x1=indicator_time,
            y0=y_range[0],
            y1=y_range[1],
            line=dict(
                color="gray",
                width=1,
                dash="dash"
            ),
            layer="below"  # Place line below the data
        )

        # Add annotation for the hour
        fig.add_annotation(
            x=indicator_time,
            y=y_range[1],
            text=f"{selected_hour:02d}:00",
            showarrow=False,
            yshift=10,
            xshift=0,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=4
        )

    except Exception as e:
        logger.error(f"Error adding hour indicator: {str(e)}")
        return

def create_base_figure(title: str, xaxis_title: str, yaxis_title: str):
    # Create a base plotly figure with common settings
    fig = go.Figure()
    
    # Update layout with common settings
    layout_updates = {
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'showlegend': False,
        'margin': dict(l=0, r=0, t=30 if title else 0, b=0),
        'xaxis': {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#f0f0f0',
            'zeroline': False,
            'showline': True,
            'linewidth': 1,
            'linecolor': '#e0e0e0',
            'type': 'date',
            'tickformat': '%Y-%m-%d %H:%M'
        },
        'yaxis': {
            'showgrid': True,
            'gridwidth': 1,
            'gridcolor': '#f0f0f0',
            'zeroline': False,
            'showline': True,
            'linewidth': 1,
            'linecolor': '#e0e0e0',
            'title_standoff': 0,
            'automargin': True
        }
    }
    
    # Only add titles if they are provided
    if title:
        layout_updates['title'] = title
    if xaxis_title:
        layout_updates['xaxis']['title'] = xaxis_title
    if yaxis_title:
        layout_updates['yaxis']['title'] = yaxis_title
    
    fig.update_layout(**layout_updates)
    return fig

def display_loading_status_line_chart(results_df: pd.DataFrame, selected_hour: int = None):
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
        
        # Add hour indicator if specified
        if selected_hour is not None and isinstance(selected_hour, int):
            # Get y-axis range for the indicator
            y_min = min(results_df['loading_percentage'])
            y_max = max(results_df['loading_percentage'])
            y_padding = (y_max - y_min) * 0.1
            y_range = (y_min - y_padding, y_max + y_padding)
            add_hour_indicator(fig, selected_hour, y_range=y_range)
        
        # Update layout
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=150)  # Extra right margin for threshold labels
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying loading status chart: {str(e)}")
        st.error("Error displaying loading status chart")

def display_power_time_series(results_df: pd.DataFrame, selected_hour: int = None, is_transformer_view: bool = False):
    # Display power consumption time series visualization
    logger.info(f"display_power_time_series called with is_transformer_view={is_transformer_view}")
    
    st.write("Power Consumption")
    
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization. Please check your database connection and try again.")
        return
    
    logger.info(f"DataFrame columns: {results_df.columns.tolist()}")
    
    # Handle size_kva based on view type
    if not is_transformer_view:
        # For customer view, ensure size_kva is 0
        if 'size_kva' in results_df.columns:
            results_df['size_kva'] = 0
    elif 'size_kva' in results_df.columns:
        # For transformer view, log the value
        logger.info(f"size_kva value in visualization: {results_df['size_kva'].iloc[0]}")

    # Ensure timestamp is in datetime format and reset index if it's the index
    if isinstance(results_df.index, pd.DatetimeIndex):
        results_df = results_df.reset_index()
        logger.info("Reset DatetimeIndex to column")
    if 'timestamp' not in results_df.columns:
        st.error("No timestamp column found in data")
        logger.error(f"Missing timestamp column. Available columns: {results_df.columns.tolist()}")
        return
    
    # Convert timestamp to datetime if needed
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    
    logger.info(f"Plotting power time series for period: {results_df['timestamp'].min()} to {results_df['timestamp'].max()}")
    logger.info(f"Timestamp dtype: {results_df['timestamp'].dtype}")
    
    # Log some sample data for debugging
    if not results_df.empty:
        logger.info("Sample power data:")
        logger.info(results_df[['timestamp', 'power_kw']].head().to_string())
        if 'size_kva' in results_df.columns:
            logger.info(f"Transformer size: {results_df['size_kva'].iloc[0]} kVA")
            logger.info(f"Max power: {results_df['power_kw'].max():.2f} kW")
            logger.info(f"Min power: {results_df['power_kw'].min():.2f} kW")

    # Sample a few timestamps to verify format
    sample_timestamps = results_df['timestamp'].head()
    logger.info(f"Sample timestamps: {sample_timestamps.tolist()}")
        
    # Round power values based on view type
    if is_transformer_view:
        results_df['power_kw'] = results_df['power_kw'].round(2)  # xx.xx for transformers
    else:
        results_df['power_kw'] = results_df['power_kw'].round(3)  # x.xxx for customers
    
    # Create figure
    fig = create_base_figure(
        None,
        None,
        "Power (kW)"
    )
    logger.info("Created base figure")
    
    # Add power consumption trace with simpler formatting
    fig.add_trace(
        go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_kw'],
            mode='lines+markers',
            name='Power',
            line=dict(color='#3b82f6', width=2),
            marker=dict(color='#3b82f6', size=6),
            hoverinfo='skip'
        )
    )
    logger.info("Added power consumption trace")
    
    # Add transformer size line if in transformer view and size_kva exists
    if is_transformer_view and 'size_kva' in results_df.columns and not pd.isna(results_df['size_kva'].iloc[0]):
        logger.info("Adding transformer size line")
        size_kva = float(results_df['size_kva'].iloc[0])
        logger.info(f"Using size_kva value: {size_kva}")
        
        # Add size_kva limit line
        fig.add_trace(
            go.Scatter(
                x=results_df['timestamp'],
                y=[size_kva] * len(results_df),
                mode='lines',
                name='Transformer Capacity (kVA)',
                line=dict(color='red', width=2, dash='dash'),
                hoverinfo='skip'
            )
        )
        logger.info("Added size_kva trace")
        
        # Add size_kva value annotation
        fig.add_annotation(
            x=results_df['timestamp'].iloc[-1],
            y=size_kva,
            text=f"{size_kva:.2f} kVA",
            showarrow=False,
            yshift=10,
            xshift=5,
            font=dict(
                color='red'
            )
        )
        logger.info("Added size_kva annotation")
        
        # Update y-axis to include size_kva
        y_max = max(max(results_df['power_kw']), size_kva) * 1.35
        logger.info(f"Set y_max to {y_max} to include size_kva")
    else:
        logger.info("Not in transformer view or no size_kva column")
        y_max = max(results_df['power_kw']) * 1.35

    # Update layout with simpler time formatting
    fig.update_layout(
        showlegend=True,
        yaxis=dict(
            title="Power (kW)",
            range=[0, y_max],
            automargin=True,
            gridcolor='#E1E1E1',
            tickformat='.2f' if is_transformer_view else '.3f'  # Match rounding precision
        ),
        xaxis=dict(
            title='Time',
            gridcolor='#E1E1E1',
            type='date',
            tickformat='%H:%M'  # Only show hour:minute
        ),
        plot_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    # Add hour indicator if specified
    if selected_hour is not None and isinstance(selected_hour, int):
        add_hour_indicator(fig, selected_hour, y_range=(0, y_max))

    st.plotly_chart(fig, use_container_width=True)
    logger.info("Displayed chart")

def display_current_time_series(results_df: pd.DataFrame, selected_hour: int = None, is_transformer_view: bool = False):
    """Display current time series visualization."""
    try:
        # Ensure timestamp is in datetime format
        results_df = results_df.copy()
        results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])

        # Create figure
        fig = create_base_figure(
            title=None,
            xaxis_title="Time",
            yaxis_title="Current (A)"
        )

        # Add current trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['current_a'],
            mode='lines+markers',
            name='Current',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=6)
        ))

        # Add hour indicator if specified
        if selected_hour is not None and isinstance(selected_hour, int):
            # Get y-axis range for the indicator
            y_min = min(results_df['current_a'])
            y_max = max(results_df['current_a'])
            y_padding = (y_max - y_min) * 0.1
            y_range = (y_min - y_padding, y_max + y_padding)
            add_hour_indicator(fig, selected_hour, y_range=y_range)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying current time series: {str(e)}")
        st.error("Error displaying current time series visualization")

def display_voltage_time_series(results_df: pd.DataFrame, selected_hour: int = None):
    """Display voltage time series visualization."""
    try:
        # Ensure timestamp is in datetime format
        results_df = results_df.copy()
        results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])

        # Create figure
        fig = create_base_figure(
            title=None,
            xaxis_title="Time",
            yaxis_title="Voltage (V)"
        )

        # Add voltage trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['voltage_v'],
            mode='lines+markers',
            name='Voltage',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=6)
        ))

        # Add hour indicator if specified
        if selected_hour is not None and isinstance(selected_hour, int):
            # Get y-axis range for the indicator
            y_min = min(results_df['voltage_v'])
            y_max = max(results_df['voltage_v'])
            y_padding = (y_max - y_min) * 0.1
            y_range = (y_min - y_padding, y_max + y_padding)
            add_hour_indicator(fig, selected_hour, y_range=y_range)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying voltage time series: {str(e)}")
        st.error("Error displaying voltage time series visualization")

def display_loading_status(results_df: pd.DataFrame, selected_hour: int = None):
    """Display loading status visualization."""
    try:
        # Ensure timestamp is in datetime format
        results_df = results_df.copy()
        results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])

        # Create figure
        fig = create_base_figure(
            title=None,
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

        # Add hour indicator if specified
        if selected_hour is not None and isinstance(selected_hour, int):
            # Get y-axis range for the indicator
            y_min = min(results_df['loading_percentage'])
            y_max = max(results_df['loading_percentage'])
            y_padding = (y_max - y_min) * 0.1
            y_range = (y_min - y_padding, y_max + y_padding)
            add_hour_indicator(fig, selected_hour, y_range=y_range)

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying loading status: {str(e)}")
        st.error("Error displaying loading status visualization")

def display_transformer_dashboard(transformer_df: pd.DataFrame, selected_hour: int = None):
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
        display_transformer_tab(transformer_df, selected_hour)

    with tab2:
        if customer_df is not None:
            display_customer_tab(customer_df, selected_hour=selected_hour)
        else:
            st.warning("No customer data available for this transformer")

def display_transformer_tab(df: pd.DataFrame, selected_hour: int = None):
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
            f"{latest['loading_percentage']:.1f}%",
            is_clickable=True
        )
    with cols[1]:
        create_tile(
            "Power Factor",
            f"{latest['power_factor']:.2f}",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Power (kW)",
            f"{latest['power_kw']:.1f}",
            is_clickable=True
        )
    with cols[3]:
        create_tile(
            "Power (kVA)",
            f"{latest['power_kva']:.1f}",
            is_clickable=True
        )

    # Create section for loading status
    st.markdown("### Loading Status")
    with st.container():
        create_tile("Loading Status Over Time", "")
        display_loading_status_line_chart(df, selected_hour)

    # Create section for power analysis
    st.markdown("### Power Analysis")
    with st.container():
        create_tile("Power Consumption Over Time", "")
        display_power_time_series(df, selected_hour, is_transformer_view=True)

    # Create section for voltage and current
    st.markdown("### Voltage and Current")
    cols = st.columns(2)
    with cols[0]:
        create_tile("Current Over Time", "")
        display_current_time_series(df, selected_hour, is_transformer_view=True)
    with cols[1]:
        create_tile("Voltage Over Time", "")
        display_voltage_time_series(df, selected_hour)

def display_customer_tab(df: pd.DataFrame, selected_hour: int = None):
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
            "Current Power",
            f"{latest['power_kw']} kW"  # No format needed, already rounded
        )
    with cols[1]:
        create_tile(
            "Power Factor",
            f"{latest['power_factor']}"  # No format needed, already rounded
        )
    with cols[2]:
        create_tile(
            "Current",
            f"{latest['current_a']} A"  # No format needed, already rounded
        )
    with cols[3]:
        create_tile(
            "Voltage",
            f"{latest['voltage_v']} V"  # No format needed, already rounded
        )
    
    # Display customer charts
    st.markdown("### Power Consumption")
    with st.container():
        create_tile("Power Over Time", "")
        display_power_time_series(customer_df, selected_hour, is_transformer_view=False)

    cols = st.columns(2)
    with cols[0]:
        st.markdown("### Current")
        create_tile("Current Over Time", "")
        display_current_time_series(customer_df, selected_hour, is_transformer_view=False)
    with cols[1]:
        st.markdown("### Voltage")
        create_tile("Voltage Over Time", "")
        display_voltage_time_series(customer_df, selected_hour)

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
