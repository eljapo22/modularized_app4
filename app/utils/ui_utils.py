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
        st.markdown(f"""
            <div style="background-color:white; padding:1rem; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.12);">
                <p style="margin:0; color:#666;">Transformer ID</p>
                <h3 style="margin:0;">{transformer_id}</h3>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style="background-color:white; padding:1rem; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.12);">
                <p style="margin:0; color:#666;">Feeder</p>
                <h3 style="margin:0;">{feeder}</h3>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div style="background-color:white; padding:1rem; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.12);">
                <p style="margin:0; color:#666;">Size</p>
                <h3 style="margin:0;">{size_kva:.0f} kVA</h3>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div style="background-color:white; padding:1rem; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.12);">
                <p style="margin:0; color:#666;">Loading</p>
                <h3 style="margin:0;">{loading_pct:.1f}%</h3>
            </div>
        """, unsafe_allow_html=True)

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
    """
    try:
        if results is None or results.empty:
            st.warning("No data available for the selected parameters")
            return
            
        # Get the first row for metrics
        current_data = results.iloc[0]
        
        # Create metric tiles
        create_metric_tiles(
            current_data['transformer_id'],
            "Feeder 1",  # Hardcoded for now
            current_data['size_kva'],
            current_data['loading_percentage']
        )
        
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs(["Loading Status", "Power Analysis", "Voltage & Current"])
        
        with tab1:
            st.plotly_chart(create_loading_chart(results), use_container_width=True)
            
            # Show current status
            status, color = get_alert_status(current_data['loading_percentage'])
            st.markdown(
                f"""
                <div style='padding: 1rem; border-radius: 0.5rem; background-color: {color}25; border: 1px solid {color}'>
                    <h3 style='margin: 0; color: {color}'>Current Status: {status}</h3>
                    <p style='margin: 0; margin-top: 0.5rem;'>Loading: {current_data['loading_percentage']:.1f}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with tab2:
            st.plotly_chart(create_power_chart(results), use_container_width=True)
            
            # Power metrics
            cols = st.columns(3)
            with cols[0]:
                st.metric("Power (kW)", f"{current_data['power_kw']:.1f}")
            with cols[1]:
                st.metric("Power (kVA)", f"{current_data['power_kva']:.1f}")
            with cols[2]:
                st.metric("Power Factor", f"{current_data['power_factor']:.2f}")
        
        with tab3:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_voltage_chart(results), use_container_width=True)
            with col2:
                st.plotly_chart(create_current_chart(results), use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error displaying dashboard: {str(e)}")
        st.error("Failed to display dashboard")

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
