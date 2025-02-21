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

def display_transformer_dashboard(results: pd.DataFrame, marker_hour: Optional[int] = None) -> None:
    """
    Display transformer loading dashboard with optional time marker
    
    Args:
        results: DataFrame with transformer data
        marker_hour: Optional hour to mark with vertical line (e.g., alert time)
    """
    try:
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs([
            "Loading Status", 
            "Power Analysis", 
            "Detailed Data",
            "Customer Data"
        ])
        
        with tab1:
            st.markdown("### Loading Status Over Time")
            
            # Create loading status chart
            fig = go.Figure()
            
            # Add loading percentage line
            fig.add_trace(go.Scatter(
                x=results.index,
                y=results['loading_percentage'],
                name='Loading %',
                line=dict(color='#0d6efd', width=2),
                hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
            ))
            
            # Add threshold lines with proper annotations
            thresholds = [
                (120, 'Critical', '#dc3545'),
                (100, 'Overloaded', '#fd7e14'),
                (80, 'Warning', '#ffc107'),
                (50, 'Pre-Warning', '#6f42c1')
            ]
            
            for threshold, label, color in thresholds:
                # Add the threshold line
                fig.add_hline(
                    y=threshold,
                    line=dict(color=color, width=1, dash='dash')
                )
                
                # Add separate annotation for the label
                fig.add_annotation(
                    text=f"{label} ({threshold}%)",
                    xref="paper",
                    x=1.02,
                    y=threshold,
                    showarrow=False,
                    font=dict(color=color),
                    align="left"
                )
            
            # Add marker for alert time if provided
            if marker_hour is not None:
                # Find the timestamp for the marker hour
                marker_date = results.index[0].date()  # Use first date in range
                marker_time = pd.Timestamp.combine(marker_date, pd.Timestamp(f"{marker_hour:02d}:00").time())
                
                if marker_time in results.index:
                    marker_value = results.loc[marker_time, 'loading_percentage']
                    
                    fig.add_vline(
                        x=marker_time,
                        line=dict(color='gray', width=2, dash='dash'),
                        annotation=dict(
                            text=f"Alert Time ({marker_hour:02d}:00)<br>{marker_value:.1f}%",
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
            
            # Update layout
            fig.update_layout(
                title=f"Transformer {results['transformer_id'].iloc[0]} Loading Status",
                xaxis_title="Time",
                yaxis_title="Loading Percentage (%)",
                hovermode='x unified',
                showlegend=False,
                margin=dict(r=150)  # Extra right margin for threshold labels
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add status summary
            current_loading = results['loading_percentage'].iloc[-1]
            status, color = get_alert_status(current_loading)
            st.markdown(
                f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color: {color}25; border: 1px solid {color}">
                    <h4 style="color: {color}; margin: 0">Current Status: {status}</h4>
                    <p style="margin: 0.5rem 0 0 0">Loading: {current_loading:.1f}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with tab2:
            st.markdown("### Power Analysis")
            
            # Create power analysis chart
            fig = go.Figure()
            
            # Add power trace
            fig.add_trace(go.Scatter(
                x=results.index,
                y=results['power_kw'],
                name='Power (kW)',
                line=dict(color='#198754', width=2),
                hovertemplate='%{y:.1f} kW<br>%{x}<extra></extra>'
            ))
            
            # Add marker for alert time if provided
            if marker_hour is not None and marker_time in results.index:
                marker_power = results.loc[marker_time, 'power_kw']
                fig.add_vline(
                    x=marker_time,
                    line=dict(color='gray', width=2, dash='dash'),
                    annotation=dict(
                        text=f"Alert Time ({marker_hour:02d}:00)<br>{marker_power:.1f} kW",
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
            
            # Update layout
            fig.update_layout(
                title=f"Power Consumption Over Time",
                xaxis_title="Time",
                yaxis_title="Power (kW)",
                hovermode='x unified',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("### Detailed Readings")
            
            # Format the data for display
            display_df = results.copy()
            display_df.index = display_df.index.strftime('%Y-%m-%d %H:%M')
            display_df = display_df.round(2)
            
            # Highlight the alert time row if provided
            if marker_hour is not None and marker_time in results.index:
                marker_time_str = marker_time.strftime('%Y-%m-%d %H:%M')
                st.dataframe(
                    display_df.style.apply(
                        lambda x: ['background-color: #f8f9fa' if i == marker_time_str else '' 
                                 for i in display_df.index],
                        axis=0
                    )
                )
            else:
                st.dataframe(display_df)
        
        with tab4:
            st.markdown("### Customer Analysis")
            
            # Get customer data from the data service
            from app.services.cloud_data_service import data_service
            
            # Use the first timestamp's date and hour
            first_timestamp = results.index[0]
            customer_data = data_service.get_customer_data(
                results['transformer_id'].iloc[0],
                first_timestamp,
                first_timestamp.hour
            )
            
            if customer_data is not None and not customer_data.empty:
                # Display customer data table
                st.markdown("#### Customer Data")
                st.dataframe(
                    customer_data[[
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
            else:
                st.warning("No customer data available for this transformer at the selected time")
            
    except Exception as e:
        logger.error(f"Error displaying transformer dashboard: {str(e)}")
        st.error("An error occurred while displaying the dashboard. Please try refreshing the page.")

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
