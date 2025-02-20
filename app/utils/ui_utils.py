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

def display_transformer_dashboard(data: pd.DataFrame, selected_hour: int):
    """
    Display transformer data dashboard
    
    Args:
        data: DataFrame with transformer data
        selected_hour: Currently selected hour (for vertical line)
    """
    st.markdown("### Transformer Loading Analysis")
    
    # Create loading status chart
    fig = go.Figure()
    
    # Add loading percentage line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['loading_percentage'],
        mode='lines+markers',
        name='Loading %',
        line=dict(color='#0d6efd', width=2),
        marker=dict(size=8)
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
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Loading", f"{data['loading_percentage'].mean():.1f}%")
    with col2:
        st.metric("Max Loading", f"{data['loading_percentage'].max():.1f}%")
    with col3:
        st.metric("Power Factor", f"{data['power_factor'].mean():.2f}")
    with col4:
        st.metric("Size", f"{data['size_kva'].iloc[0]:.0f} kVA")
