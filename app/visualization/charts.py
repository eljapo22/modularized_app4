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
        
        # Create base chart with exact same dimensions as voltage chart
        chart = alt.Chart(df_current).mark_line(
            color='blue'
        ).encode(
            x=alt.X('timestamp:T', 
                   title='Time',
                   axis=alt.Axis(grid=True, labelFontSize=11, titleFontSize=12)),
            y=alt.Y('Current:Q', 
                   scale=alt.Scale(domain=[30, 70]),
                   title='Current (A)',
                   axis=alt.Axis(grid=True, labelFontSize=11, titleFontSize=12))
        ).properties(
            width='container',
            height=200,  
            padding={"left": 45, "right": 20, "top": 10, "bottom": 40}  
        )
        
        # Use container with fixed height to ensure consistent spacing
        with st.container():
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
            
        # Constants for voltage thresholds
        nominal_voltage = 400
        upper_limit = nominal_voltage * 1.05  # +5%
        lower_limit = nominal_voltage * 0.95  # -5%
        
        # Display metrics for voltage thresholds
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Upper Limit",
                value=f"{upper_limit:.0f}V",
                delta="+5%",
                delta_color="inverse"
            )
        with col2:
            st.metric(
                label="Nominal",
                value=f"{nominal_voltage:.0f}V"
            )
        with col3:
            st.metric(
                label="Lower Limit",
                value=f"{lower_limit:.0f}V",
                delta="-5%",
                delta_color="inverse"
            )
        
        # Create mock data with phases moving together
        timestamps = results_df['timestamp']
        n_points = len(timestamps)
        
        # Create a base voltage variation that all phases will follow
        base_variation = np.cumsum(np.random.uniform(-0.1, 0.1, n_points))  # Create smooth random walk
        base_variation = base_variation - np.mean(base_variation)  # Center around zero
        base_variation = base_variation * (22.5 / np.max(np.abs(base_variation)))  # Scale to ±22.5V
        base_voltage = nominal_voltage + base_variation
        
        # Fixed phase offsets
        phase_offsets = {
            'Phase R': 0.5,
            'Phase Y': -0.3,
            'Phase B': 0.2
        }
        
        # Generate data for each phase
        df_phases = pd.DataFrame({
            'timestamp': timestamps,
            'Phase R': base_voltage + phase_offsets['Phase R'],
            'Phase Y': base_voltage + phase_offsets['Phase Y'],
            'Phase B': base_voltage + phase_offsets['Phase B']
        })
        
        # Melt the dataframe for Altair
        df_melted = df_phases.melt(
            id_vars=['timestamp'],
            var_name='Phase',
            value_name='Voltage'
        )
        
        # Create base chart
        base = alt.Chart(df_melted).encode(
            x=alt.X('timestamp:T', title='Time'),
            y=alt.Y('Voltage:Q', 
                   scale=alt.Scale(domain=[370, 415]),
                   title='Voltage (V)')
        )
        
        # Add phase lines
        phase_lines = base.mark_line().encode(
            color=alt.Color('Phase:N')
        )
        
        # Add reference lines
        ref_data = pd.DataFrame({
            'voltage': [lower_limit, nominal_voltage, upper_limit],
            'type': ['Lower Limit', 'Nominal', 'Upper Limit']
        })
        
        ref_lines = alt.Chart(ref_data).mark_rule(
            strokeDash=[4, 4],
            opacity=0.5
        ).encode(
            y='voltage:Q',
            color=alt.condition(
                alt.datum.type == 'Nominal',
                alt.value('gray'),
                alt.value('red')
            )
        )
        
        # Combine charts
        chart = alt.layer(
            phase_lines, ref_lines
        ).properties(
            width='container',
            height=250
        ).configure_axis(
            grid=True
        )
        
        # Display the chart
        st.altair_chart(chart, use_container_width=True)
        
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
    cols = st.columns(2)
    with cols[0]:
        create_tile("Current Over Time", "")
        display_current_time_series(df)
    with cols[1]:
        create_tile("Voltage Over Time", "")
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
            create_tile("Power Consumption Over Time", "")
            display_power_time_series(customer_df)

        # Voltage and Current Section
        st.markdown("### Voltage and Current")
        current_col, voltage_col = st.columns(2)
        
        with current_col:
            create_tile("Current Over Time", "")
            display_current_time_series(customer_df)
            
        with voltage_col:
            create_tile("Voltage Over Time", "")
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

def parse_load_range(range_str: str) -> tuple:
    """Parse load range string (e.g. '50%-80%') into tuple of floats."""
    try:
        lower, upper = range_str.replace('%', '').split('-')
        return float(lower), float(upper)
    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing load range '{range_str}': {str(e)}")
        return None, None
