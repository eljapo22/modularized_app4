"""
Visualization components for the Transformer Loading Analysis Application
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.config.constants import STATUS_COLORS
from datetime import datetime, timedelta
import numpy as np
import logging
from app.utils.ui_components import create_tile, create_section_title
from app.services.cloud_data_service import CloudDataService

# Initialize logger
logger = logging.getLogger(__name__)

def add_hour_indicator(fig, selected_hour: int, y_range: tuple = None):
    """
    Add a vertical line indicator for the selected hour to any Plotly figure.
    
    Args:
        fig: The Plotly figure to add the indicator to
        selected_hour: The hour to mark (0-23)
        y_range: Optional tuple of (min, max) y-values for the line
    """
    if y_range is None:
        y_range = (0, 100)  # Default range
    
    # Get first timestamp from x-axis data
    x_data = fig.data[0].x  # Assuming first trace has the timestamps
    if not x_data:
        logger.warning("No x-axis data found for hour indicator")
        return
    
    # Create indicator time using date_range
    first_timestamp = pd.to_datetime(x_data[0])
    base_time = pd.date_range(start=first_timestamp.date(), periods=24, freq='H')
    indicator_time = base_time[selected_hour]
    
    # Add vertical line
    fig.add_shape(
        type="line",
        x0=indicator_time,
        x1=indicator_time,
        y0=y_range[0],
        y1=y_range[1],
        line=dict(
            color='#9ca3af',
            width=1,
            dash='dash'
        )
    )
    
    # Add annotation
    fig.add_annotation(
        x=indicator_time,
        y=y_range[1],
        text=f"{selected_hour:02d}:00",
        showarrow=False,
        yshift=10
    )

def create_base_figure(title: str, xaxis_title: str, yaxis_title: str):
    """Create a base plotly figure with common settings"""
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
            'linecolor': '#e0e0e0'
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
    """Display a scatter plot of loading status events with detailed hover data"""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status visualization. Please check your database connection and try again.")
        return
        
    # Ensure required columns exist
    required_columns = ['timestamp', 'loading_percentage', 'load_range']
    missing_columns = [col for col in required_columns if col not in results_df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return
    
    # Create figure
    fig = create_base_figure(
        None,
        None,
        "Loading (%)"
    )
    
    # Add scatter plot for each status
    for status, color in STATUS_COLORS.items():
        mask = results_df['load_range'] == status
        if not mask.any():
            continue
            
        status_data = results_df[mask]
        fig.add_trace(
            go.Scatter(
                x=status_data['timestamp'],
                y=status_data['loading_percentage'],
                mode='markers',
                name=status,
                marker=dict(
                    color=color,
                    size=8
                ),
                hovertemplate='%{x|%Y-%m-%d %H:%M}<br>Loading: %{y:.1f}%<br>Status: ' + status + '<extra></extra>'
            )
        )
    
    # Add hour indicator if selected
    if selected_hour is not None:
        # Get y-axis range from data
        y_min = results_df['loading_percentage'].min()
        y_max = results_df['loading_percentage'].max()
        y_padding = (y_max - y_min) * 0.1  # Add 10% padding
        y_range = (y_min - y_padding, y_max + y_padding)
        
        # Get first timestamp and create indicator time
        first_timestamp = pd.to_datetime(results_df['timestamp'].iloc[0])
        base_time = pd.date_range(start=first_timestamp.date(), periods=24, freq='H')
        indicator_time = base_time[selected_hour]
        
        # Add the vertical line
        fig.add_shape(
            type="line",
            x0=indicator_time,
            x1=indicator_time,
            y0=y_range[0],
            y1=y_range[1],
            line=dict(
                color='#9ca3af',
                width=1,
                dash='dash'
            )
        )
        
        # Add the annotation
        fig.add_annotation(
            text=f"{selected_hour:02d}:00",
            x=indicator_time,
            y=y_range[1],
            yanchor="bottom",
            showarrow=False,
            textangle=-90,
            font=dict(
                color='#2f4f4f',
                size=12
            )
        )
    
    # Update layout
    fig.update_layout(
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Time",
        yaxis_title="Loading (%)",
        hovermode='closest'
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_power_time_series(results_df: pd.DataFrame, selected_hour: int = None, is_transformer_view: bool = False):
    """Display power consumption time series visualization"""
    logger.info(f"display_power_time_series called with is_transformer_view={is_transformer_view}")
    
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization. Please check your database connection and try again.")
        return
    
    logger.info(f"DataFrame columns: {results_df.columns.tolist()}")
    if 'size_kva' in results_df.columns:
        logger.info(f"size_kva value in visualization: {results_df['size_kva'].iloc[0]}")

    # Ensure timestamp is in datetime format and reset index if it's the index
    if isinstance(results_df.index, pd.DatetimeIndex):
        results_df = results_df.reset_index()
        logger.info("Reset DatetimeIndex to column")
    if 'timestamp' not in results_df.columns:
        st.error("No timestamp column found in data")
        logger.error(f"Missing timestamp column. Available columns: {results_df.columns.tolist()}")
        return
    
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
    
    # Add transformer size line if in transformer view
    if is_transformer_view and 'size_kva' in results_df.columns:
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

    st.plotly_chart(fig, use_container_width=True)
    logger.info("Displayed chart")

def display_current_time_series(results_df: pd.DataFrame, selected_hour: int = None, is_transformer_view: bool = False):
    """Display current analysis time series visualization"""
    if results_df is None or results_df.empty:
        st.warning("No current data available")
        return

    # Ensure timestamp is in datetime format and reset index if it's the index
    if isinstance(results_df.index, pd.DatetimeIndex):
        results_df = results_df.reset_index()
        logger.info("Reset DatetimeIndex to column")
    if 'timestamp' not in results_df.columns:
        st.error("No timestamp column found in data")
        logger.error(f"Missing timestamp column. Available columns: {results_df.columns.tolist()}")
        return
    
    logger.info(f"Plotting current time series for period: {results_df['timestamp'].min()} to {results_df['timestamp'].max()}")
    logger.info(f"Timestamp dtype: {results_df['timestamp'].dtype}")
    
    # Round current values based on view type
    if is_transformer_view:
        results_df['current_a'] = results_df['current_a'].round(2)  # xx.xx for transformers
    else:
        results_df['current_a'] = results_df['current_a'].round(3)  # x.xxx for customers

    # Sample a few timestamps to verify format
    sample_timestamps = results_df['timestamp'].head()
    logger.info(f"Sample timestamps: {sample_timestamps.tolist()}")
        
    # Create figure
    fig = create_base_figure(
        None,
        None,
        "Current (A)"
    )
    logger.info("Created base figure")
    
    # Add current trace
    fig.add_trace(
        go.Scatter(
            x=results_df['timestamp'],
            y=results_df['current_a'],
            mode='lines+markers',
            name='Current',
            line=dict(color='#3b82f6', width=2),
            marker=dict(color='#3b82f6', size=6),
            hoverinfo='skip'
        )
    )
    logger.info("Added current trace")
    
    # Update layout
    y_max = max(results_df['current_a']) * 1.35
    fig.update_layout(
        showlegend=True,
        yaxis=dict(
            title="Current (A)",
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
        )
    )

    # Add hour indicator if specified
    if selected_hour is not None:
        add_hour_indicator(fig, selected_hour, y_range=(0, y_max))

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_voltage_time_series(results_df: pd.DataFrame, selected_hour: int = None):
    """Display voltage analysis time series visualization"""
    if results_df is None or results_df.empty:
        st.warning("No voltage data available")
        return

    # Ensure timestamp is in datetime format and reset index if it's the index
    if isinstance(results_df.index, pd.DatetimeIndex):
        results_df = results_df.reset_index()
        logger.info("Reset DatetimeIndex to column")
    if 'timestamp' not in results_df.columns:
        st.error("No timestamp column found in data")
        logger.error(f"Missing timestamp column. Available columns: {results_df.columns.tolist()}")
        return
    
    logger.info(f"Plotting voltage time series for period: {results_df['timestamp'].min()} to {results_df['timestamp'].max()}")
    logger.info(f"Timestamp dtype: {results_df['timestamp'].dtype}")
    
    # Sample a few timestamps to verify format
    sample_timestamps = results_df['timestamp'].head()
    logger.info(f"Sample timestamps: {sample_timestamps.tolist()}")
        
    # Create figure
    fig = create_base_figure(
        None,
        None,
        "Voltage (V)"
    )
    logger.info("Created base figure")
    
    # Add voltage trace
    fig.add_trace(
        go.Scatter(
            x=results_df['timestamp'],
            y=results_df['voltage_v'],
            mode='lines+markers',
            name='Voltage',
            line=dict(color='#22c55e', width=2),
            marker=dict(color='#22c55e', size=6),
            hoverinfo='skip'
        )
    )
    logger.info("Added voltage trace")
    
    # Update layout
    y_max = max(results_df['voltage_v']) * 1.35
    fig.update_layout(
        showlegend=True,
        yaxis=dict(
            title="Voltage (V)",
            range=[0, y_max],
            automargin=True,
            gridcolor='#E1E1E1',
            tickformat='.1f'  # Match rounding precision
        ),
        xaxis=dict(
            title='Time',
            gridcolor='#E1E1E1',
            type='date',
            tickformat='%H:%M'  # Only show hour:minute
        )
    )

    # Add hour indicator if specified
    if selected_hour is not None:
        add_hour_indicator(fig, selected_hour, y_range=(0, y_max))

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_voltage_over_time(results_df: pd.DataFrame):
    """Display voltage over time chart."""
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
            tickformat='%H:%M',  # Show hours and minutes
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

def display_loading_status(results_df: pd.DataFrame, selected_hour: int = None):
    """Display loading status visualization"""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status visualization.")
        return

    # Create figure
    fig = create_base_figure(None, None, "Loading (%)")
    
    # Create traces for each status with simpler formatting
    for status, color in STATUS_COLORS.items():
        mask = results_df['load_range'] == status
        if not any(mask):
            continue
            
        status_df = results_df[mask]
        
        fig.add_trace(
            go.Scatter(
                x=status_df['timestamp'],
                y=status_df['loading_percentage'],
                mode='lines+markers',
                name=status,
                line=dict(color=color),
                marker=dict(
                    color=color,
                    size=8
                ),
                hovertemplate='Time: %{x}<br>Loading: %{y:.2f}%<br>Status: ' + status + '<extra></extra>'
            )
        )

    # Update layout with simpler time formatting
    fig.update_layout(
        showlegend=True,
        yaxis=dict(
            title="Loading (%)",
            range=[0, 100],
            gridcolor='#E1E1E1',
            tickformat='.2f'  # Match rounding precision
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

    st.plotly_chart(fig, use_container_width=True)

def display_transformer_dashboard(transformer_df: pd.DataFrame, selected_hour: int = None):
    """Display the transformer analysis dashboard"""
    try:
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

    except Exception as e:
        logger.error(f"Error displaying dashboard: {str(e)}")
        st.error("An error occurred while displaying the dashboard")

def display_transformer_tab(df: pd.DataFrame, selected_hour: int = None):
    """Display transformer analysis tab"""
    logger.info(f"Displaying transformer tab with data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
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
    """Display customer analysis tab"""
    logger.info(f"Displaying customer tab with data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
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
    """Generate sample three-phase voltage data."""
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
