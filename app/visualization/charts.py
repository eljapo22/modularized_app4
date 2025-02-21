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
    """Helper function to normalize timestamps and validate data in a DataFrame"""
    df = df.copy()
    if 'timestamp' in df.columns:
        # Convert to datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Remove duplicates keeping last value
        df = df.drop_duplicates(subset=['timestamp'], keep='last')

        # Identify and handle gaps
        time_diff = df['timestamp'].diff()
        mean_diff = time_diff.mean()
        std_diff = time_diff.std()
        
        # Filter out points that create unrealistic gaps (more than 3 std from mean)
        valid_diffs = time_diff <= (mean_diff + 3 * std_diff)
        df = df[valid_diffs.fillna(True)]  # Keep first point
        
        # Validate numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['power_kw', 'power_kva', 'current_a', 'voltage_v', 'loading_percentage']:
                # Remove negative values
                df = df[df[col] >= 0]
                
                # Remove unrealistic spikes (more than 3 std from mean)
                mean_val = df[col].mean()
                std_val = df[col].std()
                df = df[df[col] <= (mean_val + 3 * std_val)]
                
                # Interpolate small gaps
                df[col] = df[col].interpolate(method='linear', limit=2)

    return df

def create_base_figure(xaxis_title: str = None, yaxis_title: str = None) -> go.Figure:
    """Create a base plotly figure with common settings"""
    fig = go.Figure()
    
    # Update layout with common settings
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=250,  # Smaller chart height
        xaxis=dict(
            showgrid=True,
            gridcolor='#E1E1E1',
            type='date',
            tickformat='%H:%M',  # Show only time for compactness
            tickangle=-45,
            dtick='H2',  # Show every 2 hours
            tickmode='auto',
            nticks=8,
            showline=True,
            linecolor='#E1E1E1'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#E1E1E1',
            automargin=True,
            zeroline=True,
            zerolinecolor='#E1E1E1',
            zerolinewidth=1,
            showline=True,
            linecolor='#E1E1E1'
        ),
        margin=dict(t=10, b=40, l=40, r=40),  # Reduced margins
        hovermode='x unified',
        showlegend=False
    )
    
    return fig

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power time series visualization."""
    try:
        logger.info("display_power_time_series called with is_transformer_view=" + str(is_transformer_view))
        
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid power data available for the selected time range")
            return
            
        # Create figure
        fig = create_base_figure()
        
        # Add power consumption trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_kw'],
            mode='lines',
            name='Power Consumption',
            line=dict(
                color='#0d6efd',
                width=2
            ),
            hovertemplate='%{y:.2f} kW<br>%{x}<extra></extra>'
        ))
        
        # Add transformer size reference if available
        if is_transformer_view and 'size_kva' in results_df.columns:
            size_kva = results_df['size_kva'].iloc[0]
            if size_kva > 0:
                fig.add_hline(
                    y=size_kva,
                    line_dash="dash",
                    line_color="#dc3545",
                    annotation=dict(
                        text=f"Transformer Size: {size_kva} kVA",
                        xref="paper",
                        x=1,
                        y=size_kva,
                        showarrow=False,
                        font=dict(color="#dc3545")
                    )
                )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying power time series: {str(e)}")
        st.error("Error displaying power time series chart")

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = True):
    """Display current time series visualization."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid current data available for the selected time range")
            return
            
        # Create figure
        fig = create_base_figure()
        
        # Add current trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['current_a'],
            mode='lines',
            name='Current',
            line=dict(
                color='#dc3545',  # Red color like in image
                width=2
            ),
            hovertemplate='%{y:.2f} A<br>%{x}<extra></extra>'
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying current time series: {str(e)}")
        st.error("Error displaying current time series chart")

def display_voltage_time_series(results_df: pd.DataFrame):
    """Display voltage time series visualization."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid voltage data available for the selected time range")
            return
            
        # Create figure
        fig = create_base_figure()
        
        # Add voltage traces for three phases
        colors = ['#dc3545', '#ffc107', '#0d6efd']  # Red, Yellow, Blue
        phase_names = ['Phase 1', 'Phase 2', 'Phase 3']
        for i, phase in enumerate(phase_names):
            fig.add_trace(go.Scatter(
                x=results_df['timestamp'],
                y=results_df['voltage_v'] + np.random.normal(0, 2, len(results_df)),  # Simulate 3 phases
                mode='lines',
                name=phase,
                line=dict(
                    color=colors[i],
                    width=1
                ),
                hovertemplate=f'{phase}: %{{y:.1f}} V<br>%{{x}}<extra></extra>'
            ))
        
        # Add nominal voltage and limits
        nominal_voltage = 400
        for voltage, label, color in [
            (nominal_voltage, "Nominal", "#6c757d"),
            (nominal_voltage * 1.05, "+5%", "#dc3545"),
            (nominal_voltage * 0.95, "-5%", "#dc3545")
        ]:
            fig.add_hline(
                y=voltage,
                line_dash="dash",
                line_color=color,
                annotation=dict(
                    text=label,
                    xref="paper",
                    x=1,
                    y=voltage,
                    showarrow=False,
                    font=dict(color=color)
                )
            )
        
        # Update y-axis range to match image
        fig.update_layout(
            yaxis=dict(
                range=[nominal_voltage * 0.9, nominal_voltage * 1.1]
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying voltage time series: {str(e)}")
        st.error("Error displaying voltage time series chart")

def display_loading_status_line_chart(results_df: pd.DataFrame):
    """Display loading status as a line chart with threshold indicators."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid loading data available for the selected time range")
            return
            
        # Create the line chart
        fig = create_base_figure(
            title="Loading Status Over Time",
            xaxis_title="Time",
            yaxis_title="Loading Percentage"
        )
        
        # Add loading status trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['loading_percentage'],
            mode='lines',
            name='Loading Status',
            line=dict(
                color='#0d6efd',
                width=2
            ),
            hovertemplate='%{y:.2f}%<br>%{x}<extra></extra>'
        ))
        
        # Add threshold lines with improved visibility
        thresholds = [
            (120, 'Critical', '#dc3545'),
            (100, 'Overloaded', '#fd7e14'),
            (80, 'Warning', '#ffc107'),
            (50, 'Pre-Warning', '#6f42c1')
        ]
        
        for threshold, label, color in thresholds:
            fig.add_hline(
                y=threshold,
                line_dash="dash",
                line_color=color,
                annotation=dict(
                    text=label,
                    xref="paper",
                    x=1,
                    y=threshold,
                    showarrow=False,
                    font=dict(color=color)
                )
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying loading status: {str(e)}")
        st.error("Error displaying loading status chart")

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)

        # Create figure
        fig = create_base_figure(
            title="Loading Status Over Time",
            xaxis_title="Time",
            yaxis_title="Loading Percentage"
        )
        
        # Add loading status trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['loading_percentage'],
            mode='lines',
            name='Loading Status',
            line=dict(
                color='#0d6efd',
                width=2
            ),
            hovertemplate='%{y:.2f}%<br>%{x}<extra></extra>'
        ))
        
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
        
        # Add power factor trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_factor'],
            mode='lines',
            name='Power Factor',
            line=dict(
                color='#0d6efd',
                width=2
            ),
            hovertemplate='%{y:.2f}<br>%{x}<extra></extra>'
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
        
        # Add power consumption trace
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['power_kw'],
            mode='lines',
            name='Power Consumption',
            line=dict(
                color='#0d6efd',
                width=2
            ),
            hovertemplate='%{y:.2f} kW<br>%{x}<extra></extra>'
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
    
    # Add voltage traces for three phases
    colors = ['#dc3545', '#ffc107', '#0d6efd']  # Red, Yellow, Blue
    for i, phase in enumerate(['A', 'B', 'C']):
        fig.add_trace(go.Scatter(
            x=results_df['timestamp'],
            y=results_df['voltage_v'] + np.random.normal(0, 2, len(results_df)),  # Simulate 3 phases
            mode='lines',
            name=f'Phase {phase}',
            line=dict(
                color=colors[i],
                width=1
            ),
            hovertemplate=f'Phase {phase}: %{{y:.1f}} V<br>%{{x}}<extra></extra>'
        ))
    
    # Add nominal voltage and limits
    nominal_voltage = 400
    for voltage, label, color in [
        (nominal_voltage, "Nominal Voltage", "#6c757d"),
        (nominal_voltage * 1.05, "+5%", "#dc3545"),
        (nominal_voltage * 0.95, "-5%", "#dc3545")
    ]:
        fig.add_hline(
            y=voltage,
            line_dash="dash",
            line_color=color,
            annotation=dict(
                text=label,
                xref="paper",
                x=1,
                y=voltage,
                showarrow=False,
                font=dict(color=color)
            )
        )
    
    # Update y-axis range to match image
    fig.update_layout(
        yaxis=dict(
            range=[nominal_voltage * 0.9, nominal_voltage * 1.1]
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
