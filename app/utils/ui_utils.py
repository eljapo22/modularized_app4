"""
UI utility functions for the Transformer Loading Analysis Application
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from typing import Optional, Dict
import logging

# Configure logging
logger = logging.getLogger(__name__)

def create_banner(title: str) -> None:
    """Create a banner with the specified title."""
    st.markdown(f"# {title}")
    st.markdown("---")

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

def create_customer_metrics(customer_data: pd.DataFrame, aggregated_data: Dict) -> None:
    """Display customer metrics in a clean format"""
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Customers",
            f"{aggregated_data['customer_count']}",
            help="Number of customers connected to this transformer"
        )
    
    with col2:
        st.metric(
            "Total Power",
            f"{aggregated_data['total_power_kw']:.1f} kW",
            help="Total power consumption across all customers"
        )
    
    with col3:
        st.metric(
            "Average Power Factor",
            f"{aggregated_data['avg_power_factor']:.2f}",
            help="Average power factor across all customers"
        )

def create_customer_power_chart(customer_data: pd.DataFrame) -> None:
    """Create a bar chart showing power consumption by customer"""
    
    fig = go.Figure()
    
    # Sort customers by power consumption
    sorted_data = customer_data.sort_values('power_kw', ascending=True)
    
    # Create bar chart
    fig.add_trace(go.Bar(
        x=sorted_data['power_kw'],
        y=sorted_data['customer_id'],
        orientation='h',
        marker_color='rgb(55, 83, 109)'
    ))
    
    fig.update_layout(
        title="Customer Power Consumption",
        xaxis_title="Power (kW)",
        yaxis_title="Customer ID",
        showlegend=False,
        height=max(350, len(customer_data) * 25)  # Dynamic height based on number of customers
    )
    
    st.plotly_chart(fig, use_container_width=True)

def setup_page():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Transformer Dashboard",
        page_icon="⚡",
        layout="wide"
    )

def display_transformer_dashboard(results, start_date=None, end_date=None, hour=None):
    """Display transformer dashboard with loading status and graphs."""
    if results is None or results.empty:
        st.warning("No data available for display")
        return

    # Use provided dates or get from results
    start_date = start_date or results.index.min().date()
    end_date = end_date or results.index.max().date()
    selected_hour = hour or st.session_state.get('selected_hour')

    # Display loading status
    st.markdown("#### Loading Status")
    
    # Create loading status plot
    fig = go.Figure()
    
    # Add scatter plot for loading percentage
    fig.add_trace(go.Scatter(
        x=results.index,
        y=results['loading_percentage'],
        name='Loading',
        line=dict(color='#0d6efd', width=2),
        mode='lines+markers',
        hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
    ))

    # Add threshold line
    fig.add_hline(
        y=100,
        line=dict(color='red', width=2, dash='dash'),
        annotation=dict(
            text="100% Loading",
            font=dict(size=12),
            bgcolor='rgba(255,255,255,0.8)'
        )
    )

    # Add marker for selected hour if available
    if selected_hour is not None:
        marker_date = end_date
        marker_time = pd.Timestamp.combine(marker_date, pd.Timestamp(f"{selected_hour:02d}:00").time())
        if marker_time in results.index:
            marker_value = results.loc[marker_time, 'loading_percentage']
            fig.add_vline(
                x=marker_time,
                line=dict(color='gray', width=2, dash='dash'),
                annotation=dict(
                    text=f"Selected Hour ({selected_hour:02d}:00)<br>{marker_value:.1f}%",
                    font=dict(size=12),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='gray',
                    borderwidth=1,
                    showarrow=True,
                    arrowhead=2,
                    ax=40,
                    ay=-40
                )
            )

    fig.update_layout(
        title="Transformer Loading Status",
        xaxis_title="Time",
        yaxis_title="Loading (%)",
        showlegend=False,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Display customer data if available
    if 'customer_data' in results.columns and not results['customer_data'].empty:
        st.markdown("### Connected Customers")
        customer_data = results['customer_data'].iloc[0]  # Get customer data from first row
        
        if customer_data is not None and not customer_data.empty:
            # Display customer selector
            st.markdown("#### Select Customer")
            customer_ids = sorted(customer_data['customer_id'].unique())
            selected_customer = st.selectbox(
                "Choose a customer to view details",
                customer_ids,
                key="customer_selector"
            )
            
            # Filter data for selected customer
            customer_details = customer_data[customer_data['customer_id'] == selected_customer]
            customer_details = customer_details.set_index('timestamp')
            customer_details = customer_details.sort_index()
            
            # Display customer data table for the selected hour
            st.markdown("#### Customer Data")
            if selected_hour is not None:
                current_hour_data = customer_details[
                    (customer_details.index.date == end_date) &
                    (customer_details.index.hour == selected_hour)
                ]
                st.dataframe(
                    current_hour_data[[
                        'customer_id',
                        'power_kw',
                        'power_factor',
                        'current_a',
                        'voltage_v'
                    ]].style.format({
                        'power_kw': '{:.1f}',
                        'power_factor': '{:.2f}',
                        'current_a': '{:.1f}',
                        'voltage_v': '{:d}'
                    })
                )

            # Power (kW) plot
            st.markdown("#### Power Distribution")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=customer_details.index,
                y=customer_details['power_kw'],
                name='Power',
                line=dict(color='#0d6efd', width=2),
                mode='lines+markers',
                hovertemplate='%{y:.1f} kW<br>%{x}<extra></extra>'
            ))
            
            # Add marker for selected hour
            if selected_hour is not None:
                marker_date = end_date
                marker_time = pd.Timestamp.combine(marker_date, pd.Timestamp(f"{selected_hour:02d}:00").time())
                if marker_time in customer_details.index:
                    marker_value = customer_details.loc[marker_time, 'power_kw']
                    fig.add_vline(
                        x=marker_time,
                        line=dict(color='gray', width=2, dash='dash'),
                        annotation=dict(
                            text=f"Selected Hour ({selected_hour:02d}:00)<br>{marker_value:.1f} kW",
                            font=dict(size=12),
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='gray',
                            borderwidth=1,
                            showarrow=True,
                            arrowhead=2,
                            ax=40,
                            ay=-40
                        )
                    )

            fig.update_layout(
                title=f"Power Consumption - Customer {selected_customer}",
                xaxis_title="Time",
                yaxis_title="Power (kW)",
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Current plot
            st.markdown("#### Current Distribution")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=customer_details.index,
                y=customer_details['current_a'],
                name='Current',
                line=dict(color='#198754', width=2),
                mode='lines+markers',
                hovertemplate='%{y:.1f} A<br>%{x}<extra></extra>'
            ))
            
            # Add marker for selected hour
            if selected_hour is not None and marker_time in customer_details.index:
                marker_value = customer_details.loc[marker_time, 'current_a']
                fig.add_vline(
                    x=marker_time,
                    line=dict(color='gray', width=2, dash='dash'),
                    annotation=dict(
                        text=f"Selected Hour ({selected_hour:02d}:00)<br>{marker_value:.1f} A",
                        font=dict(size=12),
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='gray',
                        borderwidth=1,
                        showarrow=True,
                        arrowhead=2,
                        ax=40,
                        ay=-40
                    )
                )

            fig.update_layout(
                title=f"Current - Customer {selected_customer}",
                xaxis_title="Time",
                yaxis_title="Current (A)",
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Voltage plot
            st.markdown("#### Voltage Distribution")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=customer_details.index,
                y=customer_details['voltage_v'],
                name='Voltage',
                line=dict(color='#dc3545', width=2),
                mode='lines+markers',
                hovertemplate='%{y} V<br>%{x}<extra></extra>'
            ))
            
            # Add marker for selected hour
            if selected_hour is not None and marker_time in customer_details.index:
                marker_value = customer_details.loc[marker_time, 'voltage_v']
                fig.add_vline(
                    x=marker_time,
                    line=dict(color='gray', width=2, dash='dash'),
                    annotation=dict(
                        text=f"Selected Hour ({selected_hour:02d}:00)<br>{marker_value} V",
                        font=dict(size=12),
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='gray',
                        borderwidth=1,
                        showarrow=True,
                        arrowhead=2,
                        ax=40,
                        ay=-40
                    )
                )

            fig.update_layout(
                title=f"Voltage - Customer {selected_customer}",
                xaxis_title="Time",
                yaxis_title="Voltage (V)",
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

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
