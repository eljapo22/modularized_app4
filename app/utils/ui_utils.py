"""
UI utility functions for the Transformer Loading Analysis Application
"""
import streamlit as st
import pandas as pd
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
    # Handle NaN values
    size_kva = 0 if pd.isna(size_kva) else size_kva
    loading_pct = 0 if pd.isna(loading_pct) else loading_pct
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Transformer ID",
            value=str(transformer_id) if transformer_id else "N/A"
        )
    with col2:
        st.metric(
            label="Feeder",
            value=str(feeder) if feeder else "N/A"
        )
    with col3:
        st.metric(
            label="Size",
            value=f"{size_kva:.0f} kVA" if pd.notna(size_kva) else "N/A"
        )
    with col4:
        st.metric(
            label="Loading",
            value=f"{loading_pct:.1f}%" if pd.notna(loading_pct) else "N/A"
        )

def get_alert_status(loading_percentage: float) -> tuple:
    """
    Determine the alert status based on the loading percentage
    
    Args:
        loading_percentage: Current loading percentage
    
    Returns:
        tuple: (status, color)
    """
    if loading_percentage >= 120:
        return "Critical", "#dc3545"  # Red
    elif loading_percentage >= 100:
        return "Overloaded", "#fd7e14"  # Orange
    elif loading_percentage >= 80:
        return "Warning", "#ffc107"  # Yellow
    elif loading_percentage >= 50:
        return "Pre-Warning", "#6f42c1"  # Purple
    else:
        return "Normal", "#198754"  # Green

def display_transformer_dashboard(results_df: pd.DataFrame):
    """Display transformer dashboard visualization."""
    try:
        if results_df is None or results_df.empty:
            st.warning("No data available for transformer dashboard.")
            return

        # Create metrics
        latest = results_df.iloc[-1]
        create_metric_tiles(
            transformer_id=latest['transformer_id'],
            feeder=latest['feeder'],
            size_kva=latest['size_kva'],
            loading_pct=latest['loading_percentage']
        )

        # Display charts
        from app.visualization.charts import display_loading_status_line_chart
        
        st.markdown("### Loading Status")
        display_loading_status_line_chart(results_df)

    except Exception as e:
        logger.error(f"Error displaying transformer dashboard: {str(e)}")
        st.error("Error displaying transformer dashboard")
