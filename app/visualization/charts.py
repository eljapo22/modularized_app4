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
            transformer_df = pd.DataFrame({'y': [size_kva]})
            
            # Add the transformer size line
            transformer_line = alt.Chart(transformer_df).mark_rule(
                color='red',
                strokeDash=[4, 4]
            ).encode(y='y:Q')

            # Add text annotation for transformer size
            transformer_text = alt.Chart(transformer_df).mark_text(
                color='red',
                align='right',
                dx=-5,
                fontSize=11,
                fontWeight='bold'
            ).encode(
                y='y:Q',
                text=alt.value(f'Transformer Size: {size_kva:.0f} kVA')
            )

            # Combine all layers
            chart = alt.layer(
                power_line,
                transformer_line,
                transformer_text
            ).properties(
                width='container',
                height=250
            )
        else:
            chart = power_line.properties(
                width='container',
                height=250
            )

        # Display the chart
        st.altair_chart(chart, use_container_width=True)

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
            
        # Create DataFrame for display
        df_current = pd.DataFrame({
            'timestamp': results_df['timestamp'],
            'Current (A)': results_df['current_a']
        }).set_index('timestamp')
        
        # Display the line chart
        st.line_chart(
            df_current,
            use_container_width=True,
            height=250
        )
        
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
        
        # Create mock data with phases moving together but with individual variations
        timestamps = results_df['timestamp']
        n_points = len(timestamps)
        
        # Base variation pattern (slower changes)
        t = np.linspace(0, 4*np.pi, n_points)  # Slower oscillation
        base_variation = np.sin(t) * 2  # Base variation of ±2V
        
        # Add some random walk component for more realism
        random_walk = np.cumsum(np.random.normal(0, 0.05, n_points))
        random_walk = random_walk - np.mean(random_walk)  # Center around zero
        random_walk = random_walk * (1 / np.max(np.abs(random_walk)))  # Scale to ±1V
        
        # Combine base variation with random walk
        base_voltage = nominal_voltage + base_variation + random_walk
        
        # Generate individual phase variations with fixed offsets and small individual noise
        df_phases = pd.DataFrame({
            'timestamp': timestamps,
            'Phase R': base_voltage + 0.5 + np.random.normal(0, 0.1, n_points),
            'Phase Y': base_voltage - 0.3 + np.random.normal(0, 0.1, n_points),
            'Phase B': base_voltage + 0.2 + np.random.normal(0, 0.1, n_points)
        })
        
        # Display the chart using native Streamlit
        st.line_chart(
            df_phases.set_index('timestamp')[['Phase R', 'Phase Y', 'Phase B']],
            use_container_width=True,
            height=250
        )
        
        # Add reference lines using markdown
        st.markdown(
            f'<hr style="border: 1px dashed red; margin-top: -125px; opacity: 0.5;">', # Upper limit
            unsafe_allow_html=True
        )
        st.markdown(
            f'<hr style="border: 1px dashed gray; margin-top: -125px; opacity: 0.5;">', # Nominal
            unsafe_allow_html=True
        )
        st.markdown(
            f'<hr style="border: 1px dashed red; margin-top: -125px; opacity: 0.5;">', # Lower limit
            unsafe_allow_html=True
        )
        
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
        display_current_time_series(df, is_transformer_view=True)
    with cols[1]:
        create_tile("Voltage Over Time", "")
        display_voltage_time_series(df)

def display_customer_tab(customer_df: pd.DataFrame):
    """Display customer data visualization."""
    if len(customer_df) == 0:
        st.warning("No customer data available")
        return

    # Get latest values
    latest = customer_df.iloc[-1]
    
    # Calculate loading percentage based on power consumption
    nominal_power = 400  # Example nominal power, adjust as needed
    customer_df['loading_percentage'] = (customer_df['power_kw'] / nominal_power) * 100
    
    # Round values according to spec
    customer_df['power_kw'] = customer_df['power_kw'].round(3)  
    customer_df['current_a'] = customer_df['current_a'].round(3)  
    customer_df['voltage_v'] = customer_df['voltage_v'].round(1)  
    customer_df['loading_percentage'] = customer_df['loading_percentage'].round(1)

    # Display customer metrics in tiles
    st.markdown("### Customer Metrics")
    cols = st.columns(4)
    with cols[0]:
        create_tile(
            "Power",
            f"{latest['power_kw']} kW"  
        )
    with cols[1]:
        create_tile(
            "Current",
            f"{latest['current_a']} A"  
        )
    with cols[2]:
        create_tile(
            "Voltage",
            f"{latest['voltage_v']} V"  
        )
    with cols[3]:
        create_tile(
            "Loading Status",
            f"{customer_df['loading_percentage'].iloc[-1]:.1f}%"  
        )
    
    # Display customer charts
    st.markdown("### Power Consumption")
    display_power_consumption(customer_df)
    
    st.markdown("### Current")
    display_current_time_series(customer_df)
    
    st.markdown("### Voltage")
    display_voltage_time_series(customer_df)
    
    st.markdown("### Loading Status")
    display_loading_status_line_chart(customer_df)
    
    # Display customer table
    st.markdown("### Customer Details")
    st.dataframe(
        customer_df[['timestamp', 'power_kw', 'voltage_v', 'current_a', 'loading_percentage']].sort_values('timestamp', ascending=False),
        use_container_width=True
    )

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
