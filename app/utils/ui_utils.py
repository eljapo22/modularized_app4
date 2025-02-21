"""
UI utility functions for the Transformer Loading Analysis Application
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

def create_banner(title: str):
    """Create a page banner with title"""
    st.markdown(f"""
        <div style="background-color:#f8f9fa; padding:1.5rem; border-radius:0.5rem; margin-bottom:1rem;">
            <h1 style="color:#2f4f4f; margin:0; text-align:center;">{title}</h1>
        </div>
    """, unsafe_allow_html=True)

def create_metric_tiles(transformer_id: str, feeder: str, size_kva: float, loading_pct: float):
    """Create metric tiles for transformer details"""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Transformer ID",
            value=transformer_id
        )
    with col2:
        st.metric(
            label="Feeder",
            value=feeder
        )
    with col3:
        st.metric(
            label="Size",
            value=f"{size_kva:.0f} kVA"
        )
    with col4:
        st.metric(
            label="Loading",
            value=f"{loading_pct:.1f}%"
        )

def create_power_chart(data: pd.DataFrame) -> go.Figure:
    """Create power consumption chart"""
    fig = go.Figure()
    
    # Add power consumption line
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['power_kw'],
        mode='lines+markers',
        name='Power (kW)',
        line=dict(color='#0d6efd', width=2),
        marker=dict(size=6)
    ))
    
    # Update layout
    fig.update_layout(
        title="Power Consumption Over Time",
        xaxis_title="Time",
        yaxis_title="Power (kW)",
        showlegend=True,
        hovermode='x unified',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_current_chart(data: pd.DataFrame) -> go.Figure:
    """Create current chart"""
    fig = go.Figure()
    
    # Add current line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['current_a'],
        mode='lines+markers',
        name='Current (A)',
        line=dict(color='#dc3545', width=2),
        marker=dict(size=6)
    ))
    
    # Update layout
    fig.update_layout(
        title="Current Over Time",
        xaxis_title="Hour",
        yaxis_title="Current (A)",
        showlegend=True,
        hovermode='x unified',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_voltage_chart(data: pd.DataFrame) -> go.Figure:
    """Create voltage chart"""
    fig = go.Figure()
    
    # Add voltage lines for each phase
    phases = ['voltage_a', 'voltage_b', 'voltage_c'] if all(col in data.columns for col in ['voltage_a', 'voltage_b', 'voltage_c']) else ['voltage_v']
    colors = ['#ffc107', '#0dcaf0', '#198754']
    
    for phase, color in zip(phases, colors):
        if phase in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[phase],
                mode='lines+markers',
                name=f'Voltage {phase[-1].upper()}' if len(phases) > 1 else 'Voltage',
                line=dict(color=color, width=2),
                marker=dict(size=6)
            ))
    
    # Add threshold lines
    fig.add_hline(y=126, line_dash="dot", line_color="red", annotation_text="High (126V)")
    fig.add_hline(y=114, line_dash="dot", line_color="red", annotation_text="Low (114V)")
    
    # Update layout
    fig.update_layout(
        title="Voltage Over Time",
        xaxis_title="Hour",
        yaxis_title="Voltage (V)",
        showlegend=True,
        hovermode='x unified',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_loading_chart(data: pd.DataFrame) -> go.Figure:
    """Create loading chart"""
    fig = go.Figure()
    
    # Add loading percentage line
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['loading_percentage'],
        mode='lines+markers',
        name='Loading (%)',
        line=dict(color='#198754', width=2),
        marker=dict(size=6)
    ))
    
    # Add threshold lines
    thresholds = [
        (120, 'Critical', '#dc3545'),  # Red
        (100, 'Overloaded', '#ffc107'),  # Yellow
        (80, 'Warning', '#fd7e14'),  # Orange
        (50, 'Pre-Warning', '#0dcaf0')  # Light blue
    ]
    
    for threshold, name, color in thresholds:
        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{name} ({threshold}%)",
            annotation_position="right"
        )
    
    # Update layout
    fig.update_layout(
        title="Loading Status Over Time",
        xaxis_title="Time",
        yaxis_title="Loading (%)",
        showlegend=True,
        hovermode='x unified',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def display_transformer_dashboard(results: pd.DataFrame, marker_hour: Optional[int] = None):
    """
    Display transformer loading dashboard
    
    Args:
        results: DataFrame with transformer data
        marker_hour: Optional hour to mark in the visualizations
    """
    try:
        if results is None or results.empty:
            st.warning("No data available for the selected parameters")
            return
            
        # Get the first row for metrics
        current_data = results.iloc[0]
        
        # Create hourly time range if marker_hour is provided
        if marker_hour is not None and isinstance(marker_hour, int):
            first_timestamp = pd.to_datetime(results['timestamp'].iloc[0])
            marker_timestamp = first_timestamp.floor('D') + pd.Timedelta(hours=marker_hour)
        
        # Create metric tiles
        create_metric_tiles(
            transformer_id=current_data['transformer_id'],
            feeder=current_data['transformer_id'][:3],  # Extract feeder from transformer ID
            size_kva=current_data['size_kva'],
            loading_pct=current_data['loading_percentage']
        )
        
        # Create loading chart
        st.markdown("### Loading Status")
        loading_fig = create_loading_chart(results)
        if marker_hour is not None:
            # Add vertical line for selected hour
            loading_fig.add_vline(
                x=marker_timestamp,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"{marker_hour:02d}:00"
            )
        st.plotly_chart(loading_fig, use_container_width=True)
        
        # Create power chart
        st.markdown("### Power Consumption")
        power_fig = create_power_chart(results)
        if marker_hour is not None:
            # Add vertical line for selected hour
            power_fig.add_vline(
                x=marker_timestamp,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"{marker_hour:02d}:00"
            )
        st.plotly_chart(power_fig, use_container_width=True)
        
        # Create current and voltage charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Current")
            current_fig = create_current_chart(results)
            if marker_hour is not None:
                # Add vertical line for selected hour
                current_fig.add_vline(
                    x=marker_timestamp,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"{marker_hour:02d}:00"
                )
            st.plotly_chart(current_fig, use_container_width=True)
            
        with col2:
            st.markdown("### Voltage")
            voltage_fig = create_voltage_chart(results)
            if marker_hour is not None:
                # Add vertical line for selected hour
                voltage_fig.add_vline(
                    x=marker_timestamp,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"{marker_hour:02d}:00"
                )
            st.plotly_chart(voltage_fig, use_container_width=True)
            
    except Exception as e:
        logger.error(f"Error displaying transformer dashboard: {str(e)}")
        st.error("An error occurred while displaying the dashboard")

def get_alert_status(loading_percentage: float) -> tuple:
    """
    Determine the alert status based on the loading percentage
    
    Args:
        loading_percentage: Current loading percentage
    
    Returns:
        tuple: (status, color)
    """
    if loading_percentage >= 120:
        return "Critical", "#dc3545"
    elif loading_percentage >= 100:
        return "Overloaded", "#fd7e14"
    elif loading_percentage >= 80:
        return "Warning", "#ffc107"
    elif loading_percentage >= 50:
        return "Pre-Warning", "#6f42c1"
    else:
        return "Normal", "#198754"
