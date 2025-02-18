"""
Visualization components for the Transformer Loading Analysis Application
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config.constants import STATUS_COLORS
from datetime import datetime, timedelta
import numpy as np
import logging

# Initialize logger
logger = logging.getLogger(__name__)

def add_hour_indicator(fig, selected_hour: int, y_range: tuple = None):
    """
    Add a vertical line indicator for the selected hour to any plotly figure.
    
    Args:
        fig: plotly figure object
        selected_hour: hour to indicate (0-23)
        y_range: optional tuple of (min, max) for y-axis range
    
    Returns:
        Modified plotly figure
    """
    if not isinstance(selected_hour, (int, float)) or not (0 <= selected_hour <= 23):
        return fig
        
    # Find the first x value in the data
    first_x = None
    for trace in fig.data:
        if hasattr(trace, 'x') and len(trace.x) > 0:
            first_x = trace.x[0]
            break
            
    if first_x is None:
        return fig
        
    # Convert the timestamp to pandas Timestamp if it's not already
    if not isinstance(first_x, pd.Timestamp):
        first_x = pd.Timestamp(first_x)
        
    # Create a new timestamp for the indicator at the same date but different hour
    indicator_time = pd.Timestamp(
        year=first_x.year,
        month=first_x.month,
        day=first_x.day,
        hour=selected_hour
    )
    
    # If no y_range provided, try to get it from the figure
    if y_range is None:
        try:
            y_values = []
            for trace in fig.data:
                if hasattr(trace, 'y'):
                    y_values.extend(trace.y)
            y_range = (min(y_values), max(y_values))
        except:
            y_range = (0, 100)
    
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
    
    return fig

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
    if results_df.empty:
        st.warning("No data available for loading status visualization")
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
                hovertemplate=(
                    "<b>%{x}</b><br>" +
                    "Loading: %{y:.1f}%<br>" +
                    f"Status: {status}<br>" +
                    "<extra></extra>"
                )
            )
        )
    
    # Add transformer size line
    transformer_size = 75.0  # kVA
    
    # First, extend the x-axis range to make room for the label
    x_max = results_df['timestamp'].max()
    x_min = results_df['timestamp'].min()
    time_range = x_max - x_min
    x_extension = pd.Timedelta(minutes=int(time_range.total_seconds() * 0.02 / 60))  # 2% of total range
    extended_x_max = x_max + x_extension
    
    # Add the red dashed line
    fig.add_shape(
        type="line",
        x0=x_min,
        x1=extended_x_max,
        y0=100,
        y1=100,
        line=dict(
            color='red',
            width=1,
            dash='dash'
        )
    )
    
    # Add transformer size annotation near the end of the line
    fig.add_annotation(
        text=f"Transformer Size: {transformer_size} kVA",
        x=x_max,  # Place at the last data point
        y=100,
        xanchor="right",  # Anchor to right side
        yanchor="middle",
        showarrow=False,
        font=dict(
            color='red',
            size=12
        ),
        bgcolor="rgba(255, 255, 255, 0.8)",  # Add semi-transparent white background
        bordercolor="red",
        borderwidth=1
    )
    
    # Add hour indicator if specified
    if selected_hour is not None:
        y_range = (
            results_df['loading_percentage'].min(),
            results_df['loading_percentage'].max()
        )
        fig = add_hour_indicator(fig, selected_hour, y_range)
    
    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=50, t=0, b=0),
        yaxis=dict(
            range=[0, max(120, results_df['loading_percentage'].max() * 1.1)],
            title=dict(
                text="Loading (%)",
                font=dict(size=12),
                standoff=15
            ),
            title_standoff=0,
            automargin=True,
            gridcolor='#E1E1E1',  # Darker grey for y-axis grid
            gridwidth=1,
            showgrid=True
        ),
        xaxis=dict(
            title=None,
            range=[x_min, extended_x_max]  # Set the extended range
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=1,
                x1=1,
                y1=1.05,
                fillcolor="#f8f9fa",
                line_width=0,
                layer="below"
            )
        ]
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_power_time_series(results_df: pd.DataFrame, selected_hour: int = None, is_transformer_view: bool = False):
    """Display power consumption time series visualization"""
    logger.info(f"display_power_time_series called with is_transformer_view={is_transformer_view}")
    
    if results_df.empty:
        st.warning("No data available for power consumption visualization")
        return
    
    logger.info(f"DataFrame columns: {results_df.columns.tolist()}")
    if 'size_kva' in results_df.columns:
        logger.info(f"size_kva value in visualization: {results_df['size_kva'].iloc[0]}")

    # Create figure
    fig = go.Figure()

    # Add power consumption trace
    fig.add_trace(go.Scatter(
        x=results_df['timestamp'],
        y=results_df['power_kw'],
        mode='lines+markers',
        name='Power',
        line=dict(color='#00ff00', width=2),  # Changed from #0078d4 to green
        marker=dict(color='#00ff00', size=6)  # Changed marker color to match
    ))
    logger.info("Added power consumption trace with green color")

    # Add transformer size line if in transformer view
    if is_transformer_view and 'size_kva' in results_df.columns:
        logger.info("Adding transformer size line")
        size_kva = float(results_df['size_kva'].iloc[0])
        logger.info(f"Using size_kva value: {size_kva}")
        
        # Add size_kva limit line
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=[size_kva] * len(results_df),
            mode='lines',
            name='Transformer Capacity (kVA)',
            line=dict(color='red', width=2, dash='dash')
        ))
        logger.info("Added size_kva trace")
        
        # Add size_kva value annotation
        fig.add_annotation(
            x=results_df['timestamp'].iloc[-1],
            y=size_kva,
            text=f"{size_kva} kVA",
            showarrow=False,
            yshift=10,
            xshift=5,
            font=dict(color='red')
        )
        logger.info("Added size_kva annotation")
        
        # Update y-axis to include size_kva
        y_max = max(max(results_df['power_kw']), size_kva) * 1.35
        logger.info(f"Set y_max to {y_max} to include size_kva")
    else:
        logger.info("Not in transformer view or no size_kva column")
        y_max = max(results_df['power_kw']) * 1.35

    # Update layout
    fig.update_layout(
        margin=dict(l=50, r=50, t=30, b=30),
        showlegend=True,
        yaxis=dict(
            title="Power (kW)",
            range=[0, y_max],
            automargin=True,
            gridcolor='#E1E1E1'
        ),
        xaxis=dict(
            gridcolor='#E1E1E1',
            title='Time'
        ),
        plot_bgcolor='white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    logger.info(f"Updated layout with y-axis range: [0, {y_max}]")

    st.plotly_chart(fig, use_container_width=True)
    logger.info("Displayed chart")

def display_current_time_series(results_df: pd.DataFrame, selected_hour: int = None):
    """Display current analysis time series visualization"""
    if results_df.empty:
        st.warning("No data available for current visualization")
        return
        
    # Create figure
    fig = create_base_figure(
        None,
        "Time",
        "Current (A)"
    )
    
    # Add current trace
    fig.add_trace(
        go.Scatter(
            x=results_df['timestamp'],
            y=results_df['current_a'],
            mode='lines+markers',
            name='Current',
            line=dict(color='red'),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Current: %{y:.1f} A<br>" +
                "<extra></extra>"
            )
        )
    )
    
    # Add hour indicator if specified
    if selected_hour is not None:
        y_range = (
            results_df['current_a'].min(),
            results_df['current_a'].max()
        )
        fig = add_hour_indicator(fig, selected_hour, y_range)
    
    # Update layout
    fig.update_layout(
        margin=dict(l=50, r=0, t=0, b=0),  # Add left margin for label
        height=250,
        yaxis=dict(
            title=dict(
                text="Current (A)",
                font=dict(size=12),
                standoff=25
            ),
            automargin=True,
            gridcolor='#E1E1E1',  # Darker grey for y-axis grid
            gridwidth=1,
            showgrid=True
        ),
        xaxis=dict(
            title=None,
            gridcolor='#E1E1E1',  # Darker grey for x-axis grid
            gridwidth=1,
            showgrid=True
        ),
        showlegend=False,
        plot_bgcolor='white'  # White background to make grid more visible
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_voltage_time_series(results_df: pd.DataFrame, selected_hour: int = None):
    """Display voltage analysis time series visualization"""
    if results_df.empty:
        st.warning("No data available for voltage visualization")
        return
        
    # Create figure
    fig = create_base_figure(
        None,
        "Time",
        "Voltage (V)"
    )
    
    # Add voltage trace
    fig.add_trace(
        go.Scatter(
            x=results_df['timestamp'],
            y=results_df['voltage_v'],
            mode='lines+markers',
            name='Voltage',
            line=dict(color='green'),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Voltage: %{y:.1f} V<br>" +
                "<extra></extra>"
            )
        )
    )
    
    # Add hour indicator if specified
    if selected_hour is not None:
        y_range = (
            results_df['voltage_v'].min(),
            results_df['voltage_v'].max()
        )
        fig = add_hour_indicator(fig, selected_hour, y_range)
    
    # Update layout
    fig.update_layout(
        margin=dict(l=50, r=0, t=0, b=0),  # Add left margin for label
        height=250,
        yaxis=dict(
            title=dict(
                text="Voltage (V)",
                font=dict(size=12),
                standoff=25
            ),
            automargin=True,
            gridcolor='#E1E1E1',  # Darker grey for y-axis grid
            gridwidth=1,
            showgrid=True
        ),
        xaxis=dict(
            title=None,
            gridcolor='#E1E1E1',  # Darker grey for x-axis grid
            gridwidth=1,
            showgrid=True
        ),
        showlegend=False,
        plot_bgcolor='white'  # White background to make grid more visible
    )
    
    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

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

def display_voltage_over_time(results_df: pd.DataFrame):
    """Display voltage over time chart."""
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
            showgrid=True
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
    """Display loading status visualization."""
    if results_df.empty:
        st.warning("No data available for loading status visualization")
        return

    # Calculate loading percentage
    results_df['loading_pct'] = (results_df['power_kw'] / 75.0) * 100

    # Create figure
    fig = go.Figure()
    
    # Add loading percentage trace
    fig.add_trace(go.Scatter(
        x=results_df.index,
        y=results_df['loading_pct'],
        mode='lines',
        name='Loading %',
        line=dict(color='#2196f3', width=1.5)
    ))

    # Add 100% threshold line
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="red",
        annotation_text="100% Loading",
        annotation_position="right"
    )

    # Calculate y-axis range
    y_max = max(100, results_df['loading_pct'].max() * 1.1)
    y_min = 0

    # Add hour indicator if specified
    if selected_hour is not None:
        add_hour_indicator(fig, selected_hour, y_range=(y_min, y_max))

    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        yaxis=dict(
            title=dict(
                text="Loading (%)",
                font=dict(size=12),
                standoff=25
            ),
            range=[y_min, y_max],
            automargin=True,
            gridcolor='#E1E1E1',  # Darker grey for y-axis grid
            gridwidth=1,
            showgrid=True
        ),
        xaxis=dict(
            title=None,
            gridcolor='#E1E1E1',  # Darker grey for x-axis grid
            gridwidth=1,
            showgrid=True
        ),
        showlegend=False,
        plot_bgcolor='white'  # White background to make grid more visible
    )

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)

def display_transformer_dashboard(results_df, selected_hour: int = None):
    """Display the complete transformer analysis dashboard with filtering options"""
    if results_df.empty:
        st.warning("No data available for the selected filters.")
        return results_df

    # Create two columns for the visualizations
    col1, col2 = st.columns(2)

    # Filter data based on selected hour if provided
    if selected_hour is not None:
        hour_start = pd.Timestamp(results_df.index[0].date()) + pd.Timedelta(hours=selected_hour)
        hour_end = hour_start + pd.Timedelta(hours=1)
        filtered_results = results_df[
            (results_df.index >= hour_start) &
            (results_df.index < hour_end)
        ]
    else:
        filtered_results = results_df

    with col1:
        # Display power consumption over time
        display_power_time_series(results_df, selected_hour, is_transformer_view=True)
        
        # Display current over time
        display_current_time_series(filtered_results, selected_hour)
        
    with col2:
        # Display voltage over time with sample data
        display_voltage_over_time(filtered_results)
    
    return filtered_results  # Return filtered results for raw data display
