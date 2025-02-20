"""
UI utility functions for the Transformer Loading Analysis Application
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

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

def create_power_chart(data: pd.DataFrame, selected_hour: int) -> go.Figure:
    """Create power consumption chart"""
    fig = go.Figure()
    
    # Add power consumption line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['power_kw'],
        mode='lines+markers',
        name='Power (kW)',
        line=dict(color='#0d6efd', width=2),
        marker=dict(size=6)
    ))
    
    # Add vertical line for selected hour
    fig.add_vline(
        x=selected_hour,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Selected Hour: {selected_hour:02d}:00",
        annotation_position="top right"
    )
    
    # Update layout
    fig.update_layout(
        title="Power Consumption Over Time",
        xaxis_title="Hour",
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

def create_loading_chart(data: pd.DataFrame, selected_hour: int) -> go.Figure:
    """Create loading chart"""
    fig = go.Figure()
    
    # Add loading percentage line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['loading_percentage'],
        mode='lines+markers',
        name='Loading %',
        line=dict(color='#0d6efd', width=2),
        marker=dict(size=6)
    ))
    
    # Add vertical line for selected hour
    fig.add_vline(
        x=selected_hour,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Selected Hour: {selected_hour:02d}:00",
        annotation_position="top right"
    )
    
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
        title="Transformer Loading Over Time",
        xaxis_title="Hour",
        yaxis_title="Loading Percentage",
        showlegend=True,
        hovermode='x unified',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def display_transformer_dashboard(data: pd.DataFrame, selected_hour: int = None):
    """
    Display transformer dashboard with metrics and charts
    
    Args:
        data: DataFrame with transformer data
        selected_hour: Selected hour for vertical line indicator (optional)
    """
    try:
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Average Loading",
                f"{data['loading_percentage'].mean():.1f}%"
            )
        with col2:
            st.metric(
                "Max Loading",
                f"{data['loading_percentage'].max():.1f}%"
            )
        with col3:
            st.metric(
                "Power Factor",
                f"{data['power_factor'].mean():.2f}"
            )
        with col4:
            st.metric(
                "Size",
                f"{data['size_kva'].iloc[0]:.0f} kVA"
            )
        
        # Create loading status chart
        fig_loading = go.Figure()
        
        # Add threshold lines
        fig_loading.add_hline(y=120, line_dash="dash", line_color="red", annotation_text="Critical (120%)")
        fig_loading.add_hline(y=100, line_dash="dash", line_color="orange", annotation_text="Overloaded (100%)")
        fig_loading.add_hline(y=80, line_dash="dash", line_color="yellow", annotation_text="Warning (80%)")
        fig_loading.add_hline(y=50, line_dash="dash", line_color="purple", annotation_text="Pre-Warning (50%)")
        
        # Add loading percentage line
        fig_loading.add_trace(go.Scatter(
            x=data.index,
            y=data['loading_percentage'],
            mode='lines',
            name='Loading %',
            line=dict(color='blue', width=2)
        ))
        
        # Add vertical line for selected hour if in single-day mode
        if selected_hour is not None:
            selected_time = data.index[0].replace(hour=selected_hour)
            fig_loading.add_vline(
                x=selected_time,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Selected Hour ({selected_hour:02d}:00)"
            )
        
        fig_loading.update_layout(
            title="Transformer Loading Over Time",
            xaxis_title="Time",
            yaxis_title="Loading (%)",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_loading, use_container_width=True)
        
        # Create power consumption chart
        fig_power = go.Figure()
        fig_power.add_trace(go.Scatter(
            x=data.index,
            y=data['power_kw'],
            mode='lines',
            name='Power (kW)',
            line=dict(color='green', width=2)
        ))
        fig_power.update_layout(
            title="Power Consumption Over Time",
            xaxis_title="Time",
            yaxis_title="Power (kW)",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_power, use_container_width=True)
        
        # Create current chart
        fig_current = go.Figure()
        fig_current.add_trace(go.Scatter(
            x=data.index,
            y=data['current_a'],
            mode='lines',
            name='Current (A)',
            line=dict(color='red', width=2)
        ))
        fig_current.update_layout(
            title="Current Over Time",
            xaxis_title="Time",
            yaxis_title="Current (A)",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_current, use_container_width=True)
        
        # Create voltage chart
        fig_voltage = go.Figure()
        fig_voltage.add_trace(go.Scatter(
            x=data.index,
            y=data['voltage_v'],
            mode='lines',
            name='Voltage (V)',
            line=dict(color='orange', width=2)
        ))
        fig_voltage.update_layout(
            title="Voltage Over Time",
            xaxis_title="Time",
            yaxis_title="Voltage (V)",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_voltage, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying transformer dashboard: {str(e)}")
        st.error("Error displaying transformer dashboard. Check the logs for details.")
