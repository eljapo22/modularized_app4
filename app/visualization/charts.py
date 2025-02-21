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

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps in a DataFrame"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def create_base_figure(title: str, xaxis_title: str, yaxis_title: str):
    """Create a base plotly figure with common settings"""
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
        results_df = normalize_timestamps(results_df)
        
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

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
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

    # Normalize timestamps
    results_df = normalize_timestamps(results_df)

    # Ensure timestamp is in datetime format and reset index if it's the index
    if isinstance(results_df.index, pd.DatetimeIndex):
        results_df = results_df.reset_index()
        logger.info("Reset DatetimeIndex to column")
    
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

    st.plotly_chart(fig, use_container_width=True)
    logger.info("Displayed chart")

def display_current_time_series(results_df: pd.DataFrame):
    """Display current time series visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)

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

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying current time series: {str(e)}")
        st.error("Error displaying current time series visualization")

def display_voltage_time_series(results_df: pd.DataFrame):
    """Display voltage time series visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)

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

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying voltage time series: {str(e)}")
        st.error("Error displaying voltage time series visualization")

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)

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

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying loading status: {str(e)}")
        st.error("Error displaying loading status visualization")

def display_power_factor_time_series(results_df: pd.DataFrame):
    """Display power factor time series visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)
        
        # Create figure
        fig = create_base_figure(
            title="Power Factor Over Time",
            xaxis_title="Time",
            yaxis_title="Power Factor"
        )
        
        # Add power factor line
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_factor'],
            mode='lines+markers',
            name='Power Factor',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=6)
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying power factor chart: {str(e)}")
        st.error("Error displaying power factor chart")

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

def display_voltage_over_time(results_df: pd.DataFrame):
    # Display voltage over time chart
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage over time visualization.")
        return

    # Create figure
    fig = create_base_figure(
        title="Voltage Over Time",
        xaxis_title="Time",
        yaxis_title="Voltage (V)"
    )
    
    # Add voltage traces
    for phase, color in [('Red Phase', 'red'), ('Yellow Phase', '#FFD700'), ('Blue Phase', 'blue')]:
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['voltage_v'],
            name=phase,
            line=dict(color=color, width=1)
        ))
    
    # Add nominal voltage line and limits
    for voltage, label, color in [
        (120, "Nominal (120V)", "gray"),
        (126, "+5% (126V)", "red"),
        (114, "-5% (114V)", "red")
    ]:
        fig.add_hline(
            y=voltage,
            line_dash="dash",
            line_color=color,
            annotation_text=label,
            annotation_position="right"
        )
    
    # Update layout
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=150),
        yaxis_range=[110, 130]
    )
    
    st.plotly_chart(fig, use_container_width=True)
