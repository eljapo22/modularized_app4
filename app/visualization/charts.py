# Visualization components for the Transformer Loading Analysis Application

import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile
from app.config.constants import STATUS_COLORS
import altair as alt
import numpy as np
import plotly.graph_objects as go
from typing import Optional

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
        valid_diffs = valid_diffs.fillna(True, inplace=False)  # Keep first point
        df = df[valid_diffs]
        
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
        
        # Validate load_range format
        if 'load_range' in df.columns:
            # Keep only valid load ranges (format: XX%-YY%)
            valid_ranges = df['load_range'].str.match(r'^\d+%-\d+%$')
            if valid_ranges is not None:
                valid_ranges = valid_ranges.fillna(False, inplace=False)
                df = df[valid_ranges]
            
            # Forward fill missing load ranges
            df['load_range'] = df['load_range'].ffill()

    return df

def display_power_time_series(results_df: pd.DataFrame, size_kva: float = None):
    """Display power time series visualization."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid power data available for the selected time range")
            return

        # Create base power chart
        base = alt.Chart(results_df).encode(
            x=alt.X('timestamp:T', title='Time'),
            y=alt.Y('power_kw:Q', title='Power (kW)')
        )
        
        # Add the power consumption line
        power_line = base.mark_line(color='blue')

        # Add transformer size reference if provided
        if size_kva is not None:
            # Create a DataFrame for the transformer size
            transformer_df = pd.DataFrame({
                'x': [results_df['timestamp'].max()],  # Position at the rightmost point
                'y': [size_kva]
            })
            
            # Add the transformer size line
            transformer_line = alt.Chart(transformer_df).mark_rule(
                color='red',
                strokeDash=[4, 4]
            ).encode(y='y:Q')

            # Add text annotation for transformer size on the right
            transformer_text = alt.Chart(transformer_df).mark_text(
                color='red',
                align='left',  # Align to the left of the point
                baseline='middle',
                dx=5,  # Small offset to the right
                fontSize=11,
                fontWeight='bold',
                text=f'Transformer Size: {size_kva:.0f} kVA'
            ).encode(
                x='x:T',  # Position at the rightmost timestamp
                y='y:Q'
            )

            # Combine all layers
            chart = alt.layer(
                power_line,
                transformer_line,
                transformer_text
            ).properties(
                width='container',
                height=250
            ).configure_axis(
                grid=True
            )
        else:
            chart = power_line.properties(
                width='container',
                height=250
            ).configure_axis(
                grid=True
            )

        # Display the chart
        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying power time series: {str(e)}")
        st.error("Error displaying power time series chart")

def display_current_time_series(results_df: pd.DataFrame):
    """Display current time series visualization."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid current data available for the selected time range")
            return
            
        # Create mock data
        timestamps = results_df['timestamp']
        n_points = len(timestamps)
        
        # Create current variation
        base_variation = np.cumsum(np.random.uniform(-0.1, 0.1, n_points))
        base_variation = base_variation - np.mean(base_variation)
        base_variation = base_variation * (10 / np.max(np.abs(base_variation)))  # Scale to ±10A
        current = 50 + base_variation  # Center around 50A
        
        # Generate data
        df_current = pd.DataFrame({
            'timestamp': timestamps,
            'Current': current
        })
        
        # Display section title
        st.markdown("#### Current Over Time")
        
        # Create base chart with exact same dimensions and style as voltage chart
        chart = alt.Chart(df_current).mark_line(
            color='blue',
            strokeWidth=2
        ).encode(
            x=alt.X('timestamp:T', 
                   title='Time',
                   axis=alt.Axis(
                       grid=True,
                       gridOpacity=0.5,
                       labelFontSize=11,
                       titleFontSize=12,
                       tickCount=10,
                       gridWidth=0.5
                   )),
            y=alt.Y('Current:Q', 
                   scale=alt.Scale(domain=[30, 70], nice=True),
                   title='Current (A)',
                   axis=alt.Axis(
                       grid=True,
                       gridOpacity=0.5,
                       labelFontSize=11,
                       titleFontSize=12,
                       tickCount=5,
                       gridWidth=0.5
                   ))
        ).properties(
            width='container',
            height=300,
            padding={"left": 45, "right": 20, "top": 10, "bottom": 30}
        ).configure_view(
            strokeWidth=0
        )
        
        # Add empty space to match voltage metrics height
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        
        # Create a container with full width
        with st.container():
            # Display the chart with full width
            st.altair_chart(chart, use_container_width=True)
        
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
            
        # Create mock data
        timestamps = results_df['timestamp']
        n_points = len(timestamps)
        
        # Create voltage variation
        base_variation = np.cumsum(np.random.uniform(-0.1, 0.1, n_points))
        base_variation = base_variation - np.mean(base_variation)
        base_variation = base_variation * (10 / np.max(np.abs(base_variation)))  # Scale to ±10V
        voltage = 400 + base_variation  # Center around 400V
        
        # Generate data
        df_voltage = pd.DataFrame({
            'timestamp': timestamps,
            'Voltage': voltage
        })
        
        # Display section title
        st.markdown("#### Voltage Over Time")
        
        # Create base chart with exact same dimensions and style as current chart
        base_chart = alt.Chart(df_voltage).mark_line(
            color='blue',
            strokeWidth=2
        ).encode(
            x=alt.X('timestamp:T', 
                   title='Time',
                   axis=alt.Axis(
                       grid=True,
                       gridOpacity=0.5,
                       labelFontSize=11,
                       titleFontSize=12,
                       tickCount=10,
                       gridWidth=0.5
                   )),
            y=alt.Y('Voltage:Q', 
                   scale=alt.Scale(domain=[380, 420], nice=True),
                   title='Voltage (V)',
                   axis=alt.Axis(
                       grid=True,
                       gridOpacity=0.5,
                       labelFontSize=11,
                       titleFontSize=12,
                       tickCount=5,
                       gridWidth=0.5
                   ))
        ).properties(
            width='container',
            height=300
        )
        
        # Create voltage limits
        upper_limit = 420
        nominal = 400
        lower_limit = 380
        
        # Add reference lines
        reference_lines = alt.Chart(pd.DataFrame({
            'y': [upper_limit, nominal, lower_limit],
            'color': ['red', 'gray', 'red'],
            'dash': ['dashed', 'dashed', 'dashed']
        })).mark_rule(
            strokeDash=[5, 5]
        ).encode(
            y='y:Q',
            color=alt.Color('color:N', scale=None),
            strokeDash='dash:N'
        )
        
        # Combine charts and add padding to match current chart
        chart = alt.layer(base_chart, reference_lines).properties(
            width='container',
            height=300,
            padding={"left": 45, "right": 20, "top": 10, "bottom": 30}
        ).configure_view(
            strokeWidth=0
        )
        
        # Display voltage metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div style='text-align: left; padding: 5px 0;'>
                    <span style='color: red; font-size: 12px;'>Upper Limit</span><br/>
                    <span style='color: red; font-size: 16px; font-weight: 500;'>{upper_limit}V</span>
                    <span style='color: red; font-size: 11px;'> (+5%)</span>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div style='text-align: center; padding: 5px 0;'>
                    <span style='color: gray; font-size: 12px;'>Nominal</span><br/>
                    <span style='color: gray; font-size: 16px; font-weight: 500;'>{nominal}V</span>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div style='text-align: right; padding: 5px 0;'>
                    <span style='color: red; font-size: 12px;'>Lower Limit</span><br/>
                    <span style='color: red; font-size: 16px; font-weight: 500;'>{lower_limit}V</span>
                    <span style='color: red; font-size: 11px;'> (-5%)</span>
                </div>
            """, unsafe_allow_html=True)
            
        # Create a container with full width
        with st.container():
            # Display the chart with full width
            st.altair_chart(chart, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error displaying voltage time series: {str(e)}")
        st.error("Error displaying voltage time series chart")

def display_current_and_voltage_charts(results_df: pd.DataFrame):
    """Display current and voltage time series visualizations side by side."""
    try:
        # Create two columns for the charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Current Chart
            display_current_time_series(results_df)
            
        with col2:
            # Voltage Chart
            display_voltage_time_series(results_df)
                
    except Exception as e:
        logger.error(f"Error displaying current and voltage charts: {str(e)}")
        st.error("Error displaying charts")

def display_loading_status_line_chart(results_df: pd.DataFrame):
    """Display loading status as a line chart with threshold indicators."""
    try:
        # Normalize and validate data
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid loading data available for the selected time range")
            return
            
        # Create DataFrame for display
        df_loading = pd.DataFrame({
            'timestamp': results_df['timestamp'],
            'Loading Status (%)': results_df['loading_percentage']
        }).set_index('timestamp')
        
        # Get unique load ranges and parse them
        if 'load_range' in results_df.columns:
            unique_ranges = results_df['load_range'].unique()
            thresholds = []
            for range_str in unique_ranges:
                lower, upper = parse_load_range(range_str)
                if lower is not None and upper is not None:
                    thresholds.extend([
                        (upper, f'Upper Bound', f'{upper}%', 'off'),
                        (lower, f'Lower Bound', f'{lower}%', 'normal')
                    ])
        else:
            # Fallback to default thresholds
            thresholds = [
                (120, 'Critical', '120%', 'off'),
                (100, 'Overloaded', '100%', 'off'),
                (80, 'Warning', '80%', 'normal'),
                (50, 'Pre-Warning', '50%', 'normal')
            ]
        
        # Display thresholds as metrics in columns
        cols = st.columns(len(thresholds))
        for i, (value, label, display_value, delta_color) in enumerate(sorted(thresholds, key=lambda x: x[0], reverse=True)):
            with cols[i]:
                st.metric(label, display_value, delta_color=delta_color)
        
        # Display current load range if available
        if 'load_range' in results_df.columns:
            current_range = results_df['load_range'].iloc[-1]
            st.caption(f"Current Load Range: {current_range}")
        
        # Display the line chart
        st.line_chart(
            df_loading,
            use_container_width=True,
            height=250
        )
        
    except Exception as e:
        logger.error(f"Error displaying loading status: {str(e)}")
        st.error("Error displaying loading status chart")

def display_power_consumption(results_df: pd.DataFrame):
    """Display power consumption visualization."""
    try:
        # Normalize timestamps
        results_df = normalize_timestamps(results_df)
        
        if len(results_df) == 0:
            st.warning("No valid power consumption data available")
            return
            
        # Create DataFrame for display
        df_power = pd.DataFrame({
            'timestamp': results_df['timestamp'],
            'Power (kW)': results_df['power_kw']
        }).set_index('timestamp')
        
        # Display current power consumption
        current_power = results_df['power_kw'].iloc[-1]
        st.metric("Current Power Consumption", f"{current_power:.2f} kW")
        
        # Display the line chart
        st.line_chart(
            df_power,
            use_container_width=True,
            height=250
        )
        
    except Exception as e:
        logger.error(f"Error displaying power consumption: {str(e)}")
        st.error("Error displaying power consumption visualization")

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
            "Power (kW)",
            f"{latest['power_kw']:.1f}",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Power (kVA)",
            f"{latest['power_kva']:.1f}",
            is_clickable=True
        )
    with cols[3]:
        create_tile(
            "Current",
            f"{latest['current_a']:.1f} A",
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
        display_power_time_series(df, size_kva=df['size_kva'].iloc[0] if 'size_kva' in df.columns else None)

    # Create section for voltage and current
    st.markdown("### Voltage and Current")
    
    # Create two columns for current and voltage
    current_col, voltage_col = st.columns(2)
    
    with current_col:
        display_current_time_series(df)
        
    with voltage_col:
        display_voltage_time_series(df)

def display_customer_tab(customer_df: pd.DataFrame):
    """Display customer data visualization."""
    try:
        if customer_df.empty:
            st.warning("No customer data available")
            return

        # Create section for customer details
        st.markdown("### Customer Details")
        
        # Display customer metrics in a grid
        col1, col2, col3, col4 = st.columns(4)
        
        # Get customer ID if available, otherwise use placeholder
        customer_id = customer_df['customer_id'].iloc[0] if 'customer_id' in customer_df.columns else "N/A"
        
        with col1:
            create_tile("Customer ID", customer_id)
        with col2:
            create_tile("Feeder", "Feeder 1")  # From table name in logs
        with col3:
            create_tile("Records", f"{len(customer_df):,}")
        with col4:
            create_tile("Date Range", f"{customer_df['timestamp'].min().strftime('%Y-%m-%d')} to {customer_df['timestamp'].max().strftime('%Y-%m-%d')}")

        # Power Analysis Section
        st.markdown("### Power Analysis")
        with st.container():
            display_power_time_series(customer_df)

        # Voltage and Current Section
        st.markdown("### Voltage and Current")
        
        # Create two columns for current and voltage
        current_col, voltage_col = st.columns(2)
        
        with current_col:
            display_current_time_series(customer_df)
            
        with voltage_col:
            display_voltage_time_series(customer_df)

    except Exception as e:
        logger.error(f"Error in customer tab: {str(e)}")
        st.error("Error displaying customer data. Please check the data format and try again.")

def display_voltage_over_time(results_df: pd.DataFrame):
    # Display voltage over time chart
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage over time visualization.")
        return

    # Create figure
    # Create mock data for three phases with smaller variations
    timestamps = results_df['timestamp']
    nominal_voltage = 400
    
    # Generate slightly different variations for each phase (reduced amplitude)
    df_phases = pd.DataFrame({
        'timestamp': timestamps,
        'Phase R': nominal_voltage + np.sin(np.linspace(0, 2*np.pi, len(timestamps))) * 2,
        'Phase Y': nominal_voltage + np.sin(np.linspace(2*np.pi/3, 8*np.pi/3, len(timestamps))) * 2,
        'Phase B': nominal_voltage + np.sin(np.linspace(4*np.pi/3, 10*np.pi/3, len(timestamps))) * 2
    })
    
    # Display threshold metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Upper Limit", f"{nominal_voltage * 1.05:.0f}V", "+5%", delta_color="inverse")
    with col2:
        st.metric("Nominal", f"{nominal_voltage:.0f}V")
    with col3:
        st.metric("Lower Limit", f"{nominal_voltage * 0.95:.0f}V", "-5%", delta_color="inverse")
        
    # Display the line chart
    st.line_chart(
        df_phases.set_index('timestamp'),
        use_container_width=True,
        height=250
    )

def display_loading_status(df: pd.DataFrame, size_kva: Optional[float] = None) -> None:
    """Display loading condition status chart with thresholds.
    
    Args:
        df: DataFrame containing transformer data with loading_percentage and load_range
        size_kva: Transformer size in kVA
    """
    if df is None or df.empty:
        st.warning("No data available to display loading status")
        return

    # Create loading status figure
    fig = go.Figure()

    # Add loading percentage line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['loading_percentage'],
        name='Loading %',
        mode='lines+markers',
        line=dict(color='#2E86C1', width=2),
        hovertemplate='%{y:.1f}%<br>Range: %{text}<extra></extra>',
        text=df['load_range']  # Show load_range in hover
    ))

    # Add threshold lines with their ranges
    thresholds = [
        (120, 'Critical (>120%)', '#dc3545'),
        (100, 'Overloaded (100%-120%)', '#fd7e14'),
        (80, 'Warning (80%-100%)', '#ffc107'),
        (50, 'Pre-Warning (50%-80%)', '#6f42c1')
    ]

    for threshold, label, color in thresholds:
        fig.add_hline(
            y=threshold,
            line=dict(color=color, width=1, dash='dash'),
            annotation=dict(
                text=label,
                xref='x',  # Changed from 'paper' to 'x'
                x=1.02,
                y=threshold,
                showarrow=False,
                font=dict(size=10, color=color)
            )
        )

    # Update layout
    fig.update_layout(
        height=400,
        showlegend=True,
        hovermode='x unified',
        xaxis_title='Time',
        yaxis_title='Loading (%)',
        yaxis=dict(
            range=[0, max(150, df['loading_percentage'].max() * 1.1)],
            gridcolor='rgba(0,0,0,0.1)'
        ),
        plot_bgcolor='white',
        margin=dict(l=0, r=0, t=20, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

def parse_load_range(range_str: str) -> tuple:
    """Parse load range string (e.g. '50%-80%') into tuple of floats."""
    try:
        lower, upper = range_str.replace('%', '').split('-')
        return float(lower), float(upper)
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing load range '{range_str}': {str(e)}")
        return None, None

def create_tile(title: str, value: str, background_color: str = "#F8F9FA"):
    """Create a metric tile with consistent styling."""
    st.markdown(
        f"""
        <div style="
            background-color: {background_color};
            padding: 10px 15px;
            border-radius: 5px;
            margin: 5px 0;
            height: 100%;
            width: 100%;
        ">
            <p style="color: #666; margin: 0; font-size: 14px;">{title}</p>
            <p style="color: #333; margin: 5px 0 0 0; font-size: 20px; font-weight: 500;">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
