# Visualization components for the Transformer Loading Analysis Application

import streamlit as st
import pandas as pd
import numpy as np
import logging
import plotly.graph_objects as go
from datetime import datetime, timedelta
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile, create_colored_banner, create_bordered_header
from app.config.constants import STATUS_COLORS, CHART_COLORS
from app.config.table_config import DECIMAL_PLACES

# Configure logging
logger = logging.getLogger(__name__)

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps in a DataFrame"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status chart."""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status chart")
        return

    # Create a copy and ensure timestamp handling
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Create the scatter plot
    fig = go.Figure()
    
    # Define categories in priority order (highest to lowest)
    categories = [
        (120, float('inf'), 'Critical', 'rgb(255, 0, 0)'),
        (100, 120, 'Overloaded', 'rgb(255, 165, 0)'),
        (80, 100, 'Warning', 'rgb(255, 255, 0)'),
        (50, 80, 'Pre-Warning', 'rgb(147, 112, 219)'),
        (0, 50, 'Normal', 'rgb(0, 255, 0)')
    ]
    
    # First add a line plot for all data to show progression
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['loading_percentage'],
        mode='lines',
        name='Loading Trend',
        line=dict(
            color='rgba(128,128,128,0.3)',
            width=1
        ),
        showlegend=False
    ))
    
    # Then add colored scatter points for each category
    for min_load, max_load, name, color in categories:
        mask = (df['loading_percentage'] >= min_load) & (df['loading_percentage'] < max_load)
        category_data = df[mask]
        
        if not category_data.empty:
            # Create hover text
            hover_text = [
                f"Loading: {row['loading_percentage']:.1f}%<br>" +
                f"Power: {row['power_kw']:.1f} kW<br>" +
                f"Time: {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"
                for _, row in category_data.iterrows()
            ]
            
            # Add scatter plot for this category
            fig.add_trace(go.Scatter(
                x=category_data['timestamp'],
                y=category_data['loading_percentage'],
                mode='markers',
                name=name,
                marker=dict(
                    color=color,
                    size=8,
                    line=dict(
                        color='rgba(255,255,255,0.8)',
                        width=1
                    ),
                    opacity=0.8
                ),
                text=hover_text,
                hoverinfo='text'
            ))

    # Update layout
    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Loading Percentage (%)",
        showlegend=True,
        height=400,
        template="plotly_white",
        margin=dict(l=40, r=10, t=10, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='white',
        font=dict(color='#2f4f4f'),
        xaxis=dict(
            type='date',
            tickformat='%H:%M',  # Show only hour:minute for cleaner display
            dtick=3600000,  # 1 hour in milliseconds
            tickangle=45,
            gridcolor='rgba(128,128,128,0.1)',
            showgrid=True,
            range=[min_time, max_time],  # Set range to exactly match data
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.1)',
            showgrid=True,
            range=[0, max(150, df['loading_percentage'].max() * 1.1)]  # Ensure we see all data plus threshold lines
        ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        )
    )

    # Add threshold lines
    thresholds = [120, 100, 80, 50]
    threshold_colors = ['rgb(255, 0, 0)', 'rgb(255, 165, 0)', 'rgb(255, 255, 0)', 'rgb(147, 112, 219)']
    
    for threshold, color in zip(thresholds, threshold_colors):
        fig.add_hline(
            y=threshold,
            line=dict(
                color=color,
                width=1,
                dash="dash"
            ),
            opacity=0.7,
            layer='below'
        )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power consumption time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization.")
        return
    
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.sort_values('timestamp')  # Sort by timestamp
    results_df = results_df.set_index('timestamp')
    
    # Create power chart
    st.line_chart(
        results_df['power_kw'],
        use_container_width=True
    )

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display current time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for current visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    results_df = results_df.copy()
    results_df['timestamp'] = pd.to_datetime(results_df['timestamp'])
    results_df = results_df.sort_values('timestamp')  # Sort by timestamp
    results_df = results_df.set_index('timestamp')
    
    # Create current chart
    st.line_chart(
        results_df['current_a'],
        use_container_width=True
    )

def display_voltage_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display voltage time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage visualization.")
        return
        
    # Ensure timestamp is datetime and set as index
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')
    
    # Create mock data for 3 phases based on actual voltage
    voltage_data = pd.DataFrame(index=df.index)
    voltage_data['[0]Phase A'] = df['voltage_v']  # Original data
    voltage_data['[1]Phase B'] = df['voltage_v'] * 0.98  # Slightly lower
    voltage_data['[2]Phase C'] = df['voltage_v'] * 1.02  # Slightly higher
    
    # Create voltage chart with all phases
    st.line_chart(voltage_data)

def display_power_consumption(results_df: pd.DataFrame):
    """Display power consumption visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)
        
        # Create power consumption chart
        st.line_chart(
            results_df['power_kw'],
            use_container_width=True
        )
        
    except Exception as e:
        logger.error(f"Error displaying power consumption chart: {str(e)}")
        st.error("Error displaying power consumption chart")

def display_transformer_dashboard(transformer_df: pd.DataFrame, customer_df: pd.DataFrame = None):
    # Display the transformer analysis dashboard
    if transformer_df is None or transformer_df.empty:
        st.warning("No data available for transformer dashboard.")
        return

    # Show customer analysis if tile was clicked
    if 'show_customer_analysis' in st.session_state and st.session_state.show_customer_analysis:
        st.session_state.show_customer_analysis = False  # Reset for next time
        if customer_df is not None:
            display_customer_tab(customer_df)
            return
        else:
            st.warning("No customer data available for this transformer.")
            return

    # Create metrics row
    cols = st.columns(4)
    
    # Current transformer info
    latest = transformer_df.iloc[-1]
    with cols[0]:
        create_tile(
            "Transformer ID",
            latest.get('transformer_id', 'N/A'),
            is_clickable=False
        )
    with cols[1]:
        # Get number of unique customers
        customer_count = len(customer_df['customer_id'].unique()) if customer_df is not None else 'N/A'
        if create_tile(
            "Customers",
            str(customer_count),
            is_clickable=True
        ):
            # Show customer analysis
            st.session_state.show_customer_analysis = True
            st.rerun()
    with cols[2]:
        create_tile(
            "Latitude",
            f"{latest.get('latitude', 'N/A')}",
            is_clickable=False
        )
    with cols[3]:
        create_tile(
            "Longitude",
            f"{latest.get('longitude', 'N/A')}",
            is_clickable=False
        )

    # Display transformer data
    display_transformer_data(transformer_df)

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
    customer_df['voltage_v'] = customer_df['voltage_v'].round(1)  # xxx.x

    # Display customer metrics in tiles
    cols = st.columns(4)
    latest = customer_df.iloc[-1]
    
    with cols[0]:
        create_tile(
            "Current (A)",
            f"{latest['current_a']:.{DECIMAL_PLACES['current_a']}f}",
            is_clickable=True
        )
    with cols[1]:
        create_tile(
            "Power (kW)",
            f"{latest['power_kw']:.{DECIMAL_PLACES['power_kw']}f}",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Power (kVA)",
            f"{latest['power_kva']:.{DECIMAL_PLACES['power_kva']}f}",
            is_clickable=True
        )
    with cols[3]:
        create_tile(
            "Voltage (V)",
            f"{latest['voltage_v']:.{DECIMAL_PLACES['voltage_v']}f}",
            is_clickable=True
        )
    
    # Display customer charts
    with st.container():
        create_colored_banner("Power Consumption")
        display_power_time_series(customer_df, is_transformer_view=False)

    cols = st.columns(2)
    with cols[0]:
        create_colored_banner("Current")
        display_current_time_series(customer_df, is_transformer_view=False)
    with cols[1]:
        create_colored_banner("Voltage")
        display_voltage_time_series(customer_df)

    # Display customer table
    st.markdown("### Customer Details")
    st.dataframe(
        customer_df[['timestamp', 'power_kw', 'current_a', 'voltage_v']].sort_values('timestamp', ascending=False),
        use_container_width=True
    )

def display_transformer_data(results_df: pd.DataFrame):
    """Display transformer data visualizations in the same layout as customer tab."""
    if results_df is None or results_df.empty:
        st.warning("No data available for transformer visualization.")
        return

    # Ensure timestamp is datetime for all visualizations
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')  # Sort by timestamp
    
    # Loading Status at the top
    st.markdown("""
        <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <h3 style='margin: 0px; color: #262626; font-size: 18px'>Loading Status</h3>
        </div>
    """, unsafe_allow_html=True)
    display_loading_status(df)

    # Power Consumption
    st.markdown("""
        <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <h3 style='margin: 0px; color: #262626; font-size: 18px'>Power Consumption</h3>
        </div>
    """, unsafe_allow_html=True)
    df = df.set_index('timestamp')
    st.line_chart(df['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
                <h3 style='margin: 0px; color: #262626; font-size: 18px'>Current</h3>
            </div>
        """, unsafe_allow_html=True)
        st.line_chart(df['current_a'])
        
    with col2:
        st.markdown("""
            <div style='padding: 6px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
                <h3 style='margin: 0px; color: #262626; font-size: 18px'>Voltage</h3>
            </div>
        """, unsafe_allow_html=True)
        st.line_chart(df['voltage_v'])

def display_customer_data(results_df: pd.DataFrame):
    """Display customer data visualizations."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer visualization.")
        return

    # Display mock coordinates
    st.markdown("""
        <div style='padding: 10px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <p style='margin: 0; color: #666666; font-size: 14px'>X: 43.6532° N, Y: 79.3832° W</p>
        </div>
    """, unsafe_allow_html=True)

    # Power Consumption
    create_colored_banner("Power Consumption")
    df_power = results_df.copy()
    df_power['timestamp'] = pd.to_datetime(df_power['timestamp'])
    df_power = df_power.sort_values('timestamp')  # Sort by timestamp
    df_power = df_power.set_index('timestamp')
    st.line_chart(df_power['power_kw'])

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    
    with col1:
        create_colored_banner("Current")
        df_current = results_df.copy()
        df_current['timestamp'] = pd.to_datetime(df_current['timestamp'])
        df_current = df_current.sort_values('timestamp')  # Sort by timestamp
        df_current = df_current.set_index('timestamp')
        st.line_chart(df_current['current_a'])
        
    with col2:
        create_colored_banner("Voltage")
        df_voltage = results_df.copy()
        df_voltage['timestamp'] = pd.to_datetime(df_voltage['timestamp'])
        df_voltage = df_voltage.sort_values('timestamp')  # Sort by timestamp
        df_voltage = df_voltage.set_index('timestamp')
        st.line_chart(df_voltage['voltage_v'])
