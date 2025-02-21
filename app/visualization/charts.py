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
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')  # Ensure chronological order
    return df

def create_base_figure(title: str = None, xaxis_title: str = None, yaxis_title: str = None) -> go.Figure:
    """Create a base plotly figure with common settings"""
    fig = go.Figure()
    
    # Update layout with common settings
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#E1E1E1',
            type='date',
            tickformat='%Y-%m-%d %H:%M',  # Show full date and time
            tickangle=-45,  # Angle the timestamps for better readability
            dtick='H1',  # Show hourly ticks
            tickmode='auto',
            nticks=12,  # Limit number of ticks for readability
            rangeslider=dict(visible=True),  # Add range slider
            rangeselector=dict(  # Add range selector buttons
                buttons=list([
                    dict(count=6, label="6h", step="hour", stepmode="backward"),
                    dict(count=12, label="12h", step="hour", stepmode="backward"),
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E1E1E1',
            automargin=True,
            zeroline=True,
            zerolinecolor='#E1E1E1',
            zerolinewidth=1
        ),
        margin=dict(t=30, b=0, l=0, r=0),
        hovermode='x unified'  # Show all points at same x-coordinate
    )
    
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
    """Display power time series visualization."""
    try:
        logger.info("display_power_time_series called with is_transformer_view=" + str(is_transformer_view))
        
        # Normalize and sort timestamps
        results_df = normalize_timestamps(results_df)
        
        # Create figure with existing layout settings
        fig = create_base_figure(
            title=None,
            xaxis_title="Time",
            yaxis_title="Power (kW)"
        )
        
        # Add power consumption trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_kw'],
            mode='lines+markers',
            name='Power Consumption',
            line=dict(color='#0d6efd', width=2),
            marker=dict(size=4)
        ))
        
        # Keep existing transformer size handling
        if is_transformer_view and 'size_kva' in results_df.columns:
            size_kva = results_df['size_kva'].iloc[0]
            if size_kva > 0:
                fig.add_hline(
                    y=size_kva,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Transformer Size: {size_kva} kVA",
                    annotation_position="top right"
                )
                y_max = max(max(results_df['power_kw']), size_kva) * 1.1
            else:
                y_max = max(results_df['power_kw']) * 1.1
        else:
            y_max = max(results_df['power_kw']) * 1.1
        
        # Keep existing layout settings
        fig.update_layout(
            showlegend=True,
            yaxis=dict(
                range=[0, y_max],
                tickformat='.2f' if is_transformer_view else '.3f'
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying power time series: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("Error displaying power time series chart")

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = True):
    """Display current time series visualization."""
    try:
        if results_df is None or results_df.empty:
            st.warning("No data available for visualization")
            return
            
        # Normalize and sort timestamps
        results_df = normalize_timestamps(results_df)
        if results_df is None or results_df.empty:
            st.error("Error processing timestamp data")
            return
        
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
            marker=dict(
                size=4,
                color='#0d6efd'
            ),
            hovertemplate='%{x}<br>Current: %{y:.2f} A<extra></extra>'
        ))
        
        # Update y-axis range
        y_max = max(results_df['current_a']) * 1.1
        fig.update_layout(
            showlegend=False,
            yaxis_range=[0, y_max]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying current time series: {str(e)}")
        st.error("Error displaying current time series chart")

def display_voltage_time_series(results_df: pd.DataFrame):
    """Display voltage time series visualization."""
    try:
        if results_df is None or results_df.empty:
            st.warning("No data available for visualization")
            return
            
        # Normalize and sort timestamps
        results_df = normalize_timestamps(results_df)
        if results_df is None or results_df.empty:
            st.error("Error processing timestamp data")
            return
        
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
            marker=dict(
                size=4,
                color='#0d6efd'
            ),
            hovertemplate='%{x}<br>Voltage: %{y:.2f} V<extra></extra>'
        ))
        
        # Update y-axis range
        y_max = max(results_df['voltage_v']) * 1.1
        fig.update_layout(
            showlegend=False,
            yaxis_range=[0, y_max]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying voltage time series: {str(e)}")
        st.error("Error displaying voltage time series chart")

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
