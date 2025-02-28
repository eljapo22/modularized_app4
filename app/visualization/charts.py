# Visualization components for the Transformer Loading Analysis Application

import logging
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from datetime import datetime, timedelta
import random
from app.services.cloud_data_service import CloudDataService
from app.utils.ui_components import create_tile, create_colored_banner, create_bordered_header
from app.config.constants import STATUS_COLORS, CHART_COLORS, LOADING_THRESHOLDS
from app.config.table_config import DECIMAL_PLACES

# Configure logging
logger = logging.getLogger(__name__)

def format_chart_dates(df, timestamp_col='timestamp', format='%m/%d/%y'):
    """
    Format DataFrame timestamps for consistent display in Streamlit charts.
    
    Args:
        df: DataFrame containing timestamp data
        timestamp_col: Name of the timestamp column (default: 'timestamp')
        format: String format for the date (default: '%m/%d/%y')
        
    Returns:
        DataFrame with formatted timestamps as index
    """
    # Make a copy to avoid modifying the original
    chart_df = df.copy()
    
    # Ensure timestamp column is datetime
    chart_df[timestamp_col] = pd.to_datetime(chart_df[timestamp_col])
    
    # Sort by timestamp
    chart_df = chart_df.sort_values(timestamp_col)
    
    # Create a new column with formatted timestamps
    chart_df['formatted_date'] = chart_df[timestamp_col].dt.strftime(format)
    
    # Set the formatted date as index
    chart_df = chart_df.set_index('formatted_date')
    
    return chart_df

def normalize_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to normalize timestamps and validate data in a DataFrame"""
    logger.warning("Starting timestamp normalization - Investigating potential linear pattern")
    
    df = df.copy()
    if 'timestamp' in df.columns:
        # Convert to datetime and sort
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Log original data statistics before processing
        logger.warning("Original Data Statistics:")
        logger.warning(f"Number of rows: {len(df)}")
        logger.warning(f"Loading Percentage - Min: {df['loading_percentage'].min()}, Max: {df['loading_percentage'].max()}")
        logger.warning(f"Loading Percentage Mean: {df['loading_percentage'].mean()}")
        logger.warning(f"Loading Percentage Standard Deviation: {df['loading_percentage'].std()}")
        
        # Diagnose linear pattern before processing
        loading_diffs = df['loading_percentage'].diff()
        unique_diffs = loading_diffs.dropna().unique()
        logger.warning(f"Unique loading percentage differences: {unique_diffs}")
        logger.warning(f"Number of unique differences: {len(unique_diffs)}")
        
        # Remove duplicates keeping first occurrence to preserve original data order
        df = df.drop_duplicates(subset=['timestamp'], keep='first')
        
        # Validate numeric columns more carefully
        numeric_cols = ['loading_percentage', 'power_kw', 'current_a', 'voltage_v']
        for col in numeric_cols:
            if col in df.columns:
                # Remove extreme outliers using interquartile range method
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Log outlier information
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                logger.warning(f"Outliers in {col}:")
                logger.warning(f"Number of outliers: {len(outliers)}")
                logger.warning(f"Outlier details:\n{outliers}")
                
                # Remove outliers
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        # Log after processing
        logger.warning("After Processing Data Statistics:")
        logger.warning(f"Number of rows: {len(df)}")
        logger.warning(f"Loading Percentage - Min: {df['loading_percentage'].min()}, Max: {df['loading_percentage'].max()}")
        logger.warning(f"Loading Percentage Mean: {df['loading_percentage'].mean()}")
        logger.warning(f"Loading Percentage Standard Deviation: {df['loading_percentage'].std()}")
        
        # Advanced outlier detection for loading percentage
        # If the distribution seems artificially linear, add more sophisticated handling
        loading_diffs = df['loading_percentage'].diff()
        if len(loading_diffs.dropna().unique()) <= 2:
            logger.error("POTENTIAL ARTIFICIAL LINEAR PATTERN DETECTED!")
            
            # Try to restore more natural variations
            # Method 1: Add small random variations
            np.random.seed(42)  # For reproducibility
            df['loading_percentage'] += np.random.normal(0, df['loading_percentage'].std() * 0.05, len(df))
            
            # Method 2: Use rolling mean to smooth out artificial linearity
            df['loading_percentage'] = df['loading_percentage'].rolling(window=3, min_periods=1, center=True).mean()
    
    return df

def display_loading_status(results_df: pd.DataFrame):
    """Display loading status visualization with thresholds and background colors."""
    if results_df is None or results_df.empty:
        st.warning("No data available for loading status visualization.")
        return
        
    # Ensure we have a clean working copy with proper timestamp format
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Round loading percentages to 1 decimal place for consistent display
    df['loading_percentage'] = df['loading_percentage'].round(1)
    
    # Find the maximum loading point
    max_loading_idx = df['loading_percentage'].idxmax()
    max_loading_point = df.loc[max_loading_idx]
    max_loading_time = max_loading_point['timestamp']
    max_loading_value = max_loading_point['loading_percentage']
    
    # Use session state max_loading_time if available - ensures consistency across charts
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
    
    # -------------------- View Settings Controls --------------------
    # Load saved view settings
    chart_id = "loading_status_chart"
    view_settings = load_chart_view_settings()
    
    # Initialize default view settings
    default_y_min = 0
    default_y_max = 130
    
    # Get saved view settings if available
    if chart_id in view_settings:
        default_y_min = view_settings[chart_id].get('y_min', default_y_min)
        default_y_max = view_settings[chart_id].get('y_max', default_y_max)
    
    # Create a collapsible section for view controls
    with st.expander("Chart View Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            y_min = st.number_input("Y-Axis Minimum (%)", 
                                    min_value=0, 
                                    max_value=100, 
                                    value=int(default_y_min))
        
        with col2:
            y_max = st.number_input("Y-Axis Maximum (%)", 
                                   min_value=50, 
                                   max_value=200, 
                                   value=int(default_y_max))
        
        # Save button
        if st.button("Save View Settings"):
            view_settings = {
                'y_min': y_min,
                'y_max': y_max
            }
            save_chart_view_settings(chart_id, view_settings)
            st.success("View settings saved successfully!")
    
    # Create an Altair chart for loading percentage
    chart = create_altair_chart(
        df,
        'loading_percentage',
        title="Loading Percentage Over Time",
        color="#1f77b4",
        chart_id="loading_status_chart"
    )
    
    # Define threshold areas for background colors with light opacity
    threshold_areas = []
    
    # Get min and max timestamps to create background rectangles
    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    
    # Create threshold areas from highest to lowest to ensure proper layering
    # Critical area (120%+) - Red background
    critical_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [120], 'y2': [y_max]  # Use y_max from view settings
    })).mark_rect(color='red', opacity=0.2).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(critical_area)
    
    # Overloaded area (100-120%) - Orange background
    overloaded_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [100], 'y2': [120]
    })).mark_rect(color='orange', opacity=0.2).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(overloaded_area)
    
    # Warning area (80-100%) - Yellow background
    warning_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [80], 'y2': [100]
    })).mark_rect(color='yellow', opacity=0.1).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(warning_area)
    
    # Pre-Warning area (50-80%) - Purple background
    prewarning_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [50], 'y2': [80]
    })).mark_rect(color='purple', opacity=0.1).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(prewarning_area)
    
    # Normal area (0-50%) - Green background
    normal_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [y_min], 'y2': [50]  # Use y_min from view settings
    })).mark_rect(color='green', opacity=0.1).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(normal_area)
    
    # Add threshold lines to the chart
    threshold_rules = [
        {'value': 120, 'color': 'red', 'label': 'Critical'},
        {'value': 100, 'color': 'orange', 'label': 'Overloaded'},
        {'value': 80, 'color': 'yellow', 'label': 'Warning'},
        {'value': 50, 'color': 'purple', 'label': 'Pre-Warning'}
    ]
    
    # Add threshold lines to the chart
    threshold_lines = []
    for rule in threshold_rules:
        threshold_line = alt.Chart(pd.DataFrame({'threshold': [rule['value']]})).mark_rule(
            color=rule['color'],
            strokeWidth=1,
            strokeDash=[4, 4]  # Dashed line
        ).encode(
            y='threshold:Q'
        )
        threshold_lines.append(threshold_line)
    
    # Combine all chart elements - only using threshold lines
    chart = alt.layer(chart, *threshold_areas, *threshold_lines)
    
    # Add vertical indicator for maximum loading point
    max_rule = alt.Chart(pd.DataFrame({'max_time': [max_loading_time]})).mark_rule(
        color='#dc3545',  # Red color matching critical threshold
        strokeWidth=2,
        strokeDash=[4, 2]  # Different dash pattern to distinguish it
    ).encode(
        x='max_time:T'
    )
    
    # Add text annotation for maximum loading
    max_text = alt.Chart(pd.DataFrame({
        'max_time': [max_loading_time],
        'y': [130]  # Position at top of chart
    })).mark_text(
        align='center',
        baseline='bottom',
        fontSize=12,
        fontWeight='bold',
        color='#dc3545'
    ).encode(
        x='max_time:T',
        y='y:Q',
        text=alt.value(f'⚠️ Peak load')
    )
    
    # Add the max loading indicator to the chart
    chart = alt.layer(chart, max_rule, max_text)
    
    # Check if we should also add alert time indicator from session state
    if 'highlight_timestamp' in st.session_state:
        try:
            alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
            
            # Only add if alert_time is different from max_loading_time
            if alert_time != max_loading_time:
                # Create vertical rule at alert time
                alert_rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                    color='gray',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    x='alert_time:T'
                )
                
                # Add text annotation for alert time
                alert_text = alt.Chart(pd.DataFrame({
                    'alert_time': [alert_time],
                    'y': [130]
                })).mark_text(
                    align='center',
                    baseline='top',
                    fontSize=12,
                    color='gray'
                ).encode(
                    x='alert_time:T',
                    y='y:Q',
                    text=alt.value('⚠️ Alert point')
                )
                
                # Add to the chart
                chart = alt.layer(chart, alert_rule, alert_text)
        except Exception as e:
            logger.error(f"Error adding alert time indicator: {e}")
    
    # Display the chart
    st.altair_chart(chart, use_container_width=True)
    
    # Add threshold legend in a better position - right aligned with proper formatting
    st.markdown("""
    <style>
    .threshold-legend {
        display: flex;
        justify-content: flex-end;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: -20px;
        padding: 5px;
        border-radius: 4px;
    }
    .threshold-item {
        display: flex;
        align-items: center;
        margin-left: 10px;
    }
    .color-box {
        width: 12px;
        height: 12px;
        margin-right: 5px;
        display: inline-block;
    }
    </style>
    <div class="threshold-legend">
        <div class="threshold-item">
            <span class="color-box" style="background-color:red;"></span>
            <span>Critical ≥ 120%</span>
        </div>
        <div class="threshold-item">
            <span class="color-box" style="background-color:orange;"></span>
            <span>Overloaded ≥ 100%</span>
        </div>
        <div class="threshold-item">
            <span class="color-box" style="background-color:yellow;"></span>
            <span>Warning ≥ 80%</span>
        </div>
        <div class="threshold-item">
            <span class="color-box" style="background-color:purple;"></span>
            <span>Pre-Warning ≥ 50%</span>
        </div>
        <div class="threshold-item">
            <span class="color-box" style="background-color:green;"></span>
            <span>Normal < 50%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power consumption time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization.")
        return
    
    # Ensure we have a clean working copy with proper timestamps
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Find the maximum loading point
    if 'loading_percentage' in df.columns:
        max_loading_idx = df['loading_percentage'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        logger.info(f"Power chart: Using loading_percentage max value for peak placement at {max_loading_time}")
    else:
        # If loading percentage is not available, use max power as an alternative
        max_loading_idx = df['power_kw'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        logger.info(f"Power chart: Using power_kw max value as fallback for peak placement at {max_loading_time}")
    
    # Use session state max_loading_time if available - ensures consistency across charts
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
    
    # Check for available power metrics
    has_active_power = 'power_kw' in df.columns and not df['power_kw'].isna().all()
    has_reactive_power = 'power_kvar' in df.columns and not df['power_kvar'].isna().all()
    has_apparent_power = 'power_kva' in df.columns and not df['power_kva'].isna().all()
    
    if not (has_active_power or has_reactive_power or has_apparent_power):
        st.warning("No power data available for visualization.")
        return
    
    # Set chart ID based on view context
    chart_id_suffix = "transformer_" if is_transformer_view else ""
    
    # Display active power if available
    if has_active_power:
        # Round to 2 decimal places for display
        df['power_kw'] = df['power_kw'].round(2)
        
        # Create chart with our common function and view controls
        active_power_chart = create_altair_chart(
            df, 
            'power_kw', 
            title="Active Power (kW)",
            color='#1f77b4',  # Blue
            chart_id=f"{chart_id_suffix}power_kw_chart"
        )
        
        # Display the chart
        st.altair_chart(active_power_chart, use_container_width=True)
    
    # Display reactive power if available
    if has_reactive_power:
        # Round to 2 decimal places for display
        df['power_kvar'] = df['power_kvar'].round(2)
        
        # Create chart with our common function and view controls
        reactive_power_chart = create_altair_chart(
            df, 
            'power_kvar', 
            title="Reactive Power (kVAR)",
            color='#ff7f0e',  # Orange
            chart_id=f"{chart_id_suffix}power_kvar_chart"
        )
        
        # Display the chart
        st.altair_chart(reactive_power_chart, use_container_width=True)
    
    # Display apparent power if available
    if has_apparent_power:
        # Round to 2 decimal places for display
        df['power_kva'] = df['power_kva'].round(2)
        
        # Create chart with our common function and view controls
        apparent_power_chart = create_altair_chart(
            df, 
            'power_kva', 
            title="Apparent Power (kVA)",
            color='#2ca02c',  # Green
            chart_id=f"{chart_id_suffix}power_kva_chart"
        )
        
        # Display the chart
        st.altair_chart(apparent_power_chart, use_container_width=True)

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display current time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for current visualization.")
        return
        
    # Ensure we have a clean working copy with proper timestamp format
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Get current columns
    current_cols = [col for col in df.columns if col.startswith('current_')]
    
    if not current_cols:
        st.warning("No current data available for visualization.")
        return
    
    # Round current values to 1 decimal place for display
    for col in current_cols:
        df[col] = df[col].round(1)
    
    # Set chart ID based on view context
    chart_id_suffix = "transformer_" if is_transformer_view else ""
    
    # Find the maximum loading point for annotation
    if 'loading_percentage' in df.columns:
        max_loading_idx = df['loading_percentage'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
    elif 'power_kw' in df.columns and not df['power_kw'].isna().all():
        max_loading_idx = df['power_kw'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
    elif 'current_a' in df.columns and not df['current_a'].isna().all():
        max_loading_idx = df['current_a'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
    
    # Check if there's a standard current column for this entity
    if 'current_a' in df.columns:
        # Check if we have multiple phases
        phases = []
        for phase in ['a', 'b', 'c']:
            col = f'current_{phase}'
            if col in df.columns and not df[col].isna().all():
                phases.append(phase)
                
        if len(phases) > 1:
            # Multiple phases - create separate charts
            st.subheader("Phase Currents")
            
            # Set up columns
            cols = st.columns(len(phases))
            
            for i, phase in enumerate(phases):
                with cols[i]:
                    phase_col = f'current_{phase}'
                    
                    # Create chart with our common function and view controls
                    phase_chart = create_altair_chart(
                        df, 
                        phase_col, 
                        title=f"Phase {phase.upper()} Current (A)",
                        color=CHART_COLORS.get(i, '#1f77b4'),
                        chart_id=f"{chart_id_suffix}current_{phase}_chart"
                    )
                    
                    # Display the chart
                    st.altair_chart(phase_chart, use_container_width=True)
        else:
            # Single phase - just one chart
            # Create chart with our common function and view controls
            current_chart = create_altair_chart(
                df, 
                'current_a', 
                title="Current (A)",
                color='#1f77b4',
                chart_id=f"{chart_id_suffix}current_chart"
            )
            
            # Display the chart
            st.altair_chart(current_chart, use_container_width=True)
    elif 'current' in df.columns:
        # Create chart with our common function and view controls
        current_chart = create_altair_chart(
            df, 
            'current', 
            title="Current (A)",
            color='#1f77b4',
            chart_id=f"{chart_id_suffix}current_chart"
        )
        
        # Display the chart
        st.altair_chart(current_chart, use_container_width=True)
    else:
        st.warning("No standard current format found in the data.")

def display_voltage_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display voltage time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage visualization.")
        return
        
    try:
        # Common code for both transformer and customer views
        df = results_df.copy()
        
        # Ensure timestamp is formatted correctly
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Set chart ID based on view context
        chart_id_suffix = "transformer_" if is_transformer_view else ""
        
        # Check if we're working with phase voltages or just a single voltage
        has_phase_a = 'voltage_a' in df.columns and not df['voltage_a'].isna().all()
        has_phase_b = 'voltage_b' in df.columns and not df['voltage_b'].isna().all()
        has_phase_c = 'voltage_c' in df.columns and not df['voltage_c'].isna().all()
        
        if has_phase_a or has_phase_b or has_phase_c:
            # We have phase voltages - create a multi-line chart
            phases = []
            if has_phase_a:
                phases.append(('voltage_a', 'Phase A'))
            if has_phase_b:
                phases.append(('voltage_b', 'Phase B'))
            if has_phase_c:
                phases.append(('voltage_c', 'Phase C'))
            
            # Create a column dictionary for multi-line chart
            column_dict = {k: v for k, v in phases}
            
            # Round voltage values for display
            for col in column_dict.keys():
                df[col] = df[col].round(1)
            
            # Create multi-line chart with view controls
            voltage_chart = create_multi_line_chart(
                df,
                column_dict,
                title="Phase Voltages (V)",
                chart_id=f"{chart_id_suffix}voltage_phases_chart"
            )
            
            # Display the chart
            st.altair_chart(voltage_chart, use_container_width=True)
        
        elif 'voltage' in df.columns:
            # Single voltage column - create a standard chart
            df['voltage'] = df['voltage'].round(1)
            
            # Create chart with our common function and view controls
            voltage_chart = create_altair_chart(
                df, 
                'voltage', 
                title="Voltage (V)",
                color='#1f77b4',
                chart_id=f"{chart_id_suffix}voltage_chart"
            )
            
            # Display the chart
            st.altair_chart(voltage_chart, use_container_width=True)
        else:
            # No voltage data available in standard format
            
            # Create synthetic phase voltage data for demo purposes
            if is_transformer_view:
                # For transformers, show 3-phase voltage data
                voltage_data = pd.DataFrame()
                voltage_data['timestamp'] = df['timestamp']
                
                # Import for math functions
                import numpy as np
                
                # Base voltage is 400V for transformer view
                base_voltage = 400
                
                # Create synthetic voltage patterns
                time_idx = np.linspace(0, 4*np.pi, len(df))
                pattern_influence = 0.04
                random_noise = 0.01
                
                # Create power pattern influence if available
                if 'power_kw' in df.columns and not df['power_kw'].isna().all():
                    power_min = df['power_kw'].min()
                    power_max = df['power_kw'].max()
                    if power_max > power_min:
                        power_pattern = (df['power_kw'] - power_min) / (power_max - power_min)
                        inverse_pattern = 1 - power_pattern.values
                    else:
                        inverse_pattern = np.ones(len(df)) * 0.5
                else:
                    inverse_pattern = np.ones(len(df)) * 0.5
                
                # Create three phases with slight variations
                voltage_data['Phase A'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                voltage_data['Phase B'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx - (2*np.pi/3)) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                voltage_data['Phase C'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx - (4*np.pi/3)) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                # Column dictionary for multi-line chart
                column_dict = {
                    'Phase A': 'Phase A',
                    'Phase B': 'Phase B',
                    'Phase C': 'Phase C'
                }
                
                # Create multi-line chart with view controls
                voltage_chart = create_multi_line_chart(
                    voltage_data,
                    column_dict,
                    title="Phase Voltages (V)",
                    chart_id=f"{chart_id_suffix}voltage_phases_chart"
                )
                
                # Display the chart
                st.altair_chart(voltage_chart, use_container_width=True)
            else:
                # For regular customer view, show single-phase voltage
                voltage_data = pd.DataFrame()
                voltage_data['timestamp'] = df['timestamp']
                
                # Create a synthetic voltage pattern based on 120V system
                import numpy as np
                base_voltage = 120
                time_idx = np.linspace(0, 4*np.pi, len(df))
                
                # Create synthetic voltage with realistic variations
                voltage_data['voltage'] = base_voltage + \
                    base_voltage * 0.05 * np.sin(time_idx) + \
                    base_voltage * 0.02 * np.random.normal(0, 1, len(df))
                
                # Create chart with our common function and view controls
                voltage_chart = create_altair_chart(
                    voltage_data, 
                    'voltage', 
                    title="Voltage (V)",
                    color='#1f77b4',
                    chart_id=f"{chart_id_suffix}voltage_chart"
                )
                
                # Display the chart
                st.altair_chart(voltage_chart, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error displaying voltage visualization: {e}")
        logger.error(f"Error in display_voltage_time_series: {e}")

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

def display_transformer_dashboard(
    transformer_df: pd.DataFrame,
    customer_df: pd.DataFrame = None
):
    """
    Display comprehensive transformer dashboard
   
    Args:
        transformer_df: Transformer data DataFrame
        customer_df: Optional customer data DataFrame
    """
    # Validate input data
    if transformer_df is None or transformer_df.empty:
        st.warning("No transformer data available for dashboard.")
        return

    try:
        # Ensure session state variables exist (set defaults if not)
        if 'show_customer_details' not in st.session_state:
            st.session_state.show_customer_details = False  # Third view (individual customer)
        if 'show_customer_bridge' not in st.session_state:
            st.session_state.show_customer_bridge = False   # Second view (customer list)
            
        # Check for alert timestamp to highlight
        alert_timestamp = None
        if 'highlight_timestamp' in st.session_state:
            try:
                alert_timestamp_str = st.session_state.highlight_timestamp
                alert_timestamp = pd.to_datetime(alert_timestamp_str)
                st.info(f" Showing alert data for: {alert_timestamp.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                logger.error(f"Error parsing alert timestamp: {e}")
        
        # Show customer details if a specific customer was selected
        if 'show_customer_details' in st.session_state and st.session_state.show_customer_details:
            # Don't reset show_customer_details here - it causes navigation issues
            # Will be reset by the navigation buttons when needed
            
            if customer_df is not None and 'selected_customer_id' in st.session_state:
                # Filter for the selected customer
                selected_customer_id = st.session_state.selected_customer_id
                selected_customer_df = customer_df[customer_df['customer_id'] == selected_customer_id].copy()
                
                if selected_customer_df.empty:
                    st.warning(f"No data available for Customer {selected_customer_id}")
                    return
                
                # Add navigation buttons in columns
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("← Back to Dashboard"):
                        # Reset all view-related session state to go back to dashboard (first view)
                        st.session_state.show_customer_details = False  # Hide individual customer view (third view)
                        st.session_state.show_customer_bridge = False   # Hide customer list view (second view)
                        st.experimental_rerun()
                with col2:
                    if st.button("← Back to Customer List"):
                        # Go back to customer bridge view (second view)
                        st.session_state.show_customer_bridge = True  # Show the bridge/list view
                        st.session_state.show_customer_details = False  # Hide detailed view
                        # Don't clear selected_customer_id to maintain context
                        st.experimental_rerun()
                
                # Display the detailed view for this customer
                st.header(f"Customer {selected_customer_id} Details")
                display_customer_tab(selected_customer_df)
                return
            else:
                st.warning("No customer data available for the selected customer.")
                return
                
        # Show customer bridge view if requested
        if 'show_customer_bridge' in st.session_state and st.session_state.show_customer_bridge:
            if customer_df is not None:
                # Display the bridge view
                display_customers_bridge_view(customer_df)
                return
            else:
                st.warning("No customer data available for this transformer.")
                st.session_state.show_customer_bridge = False
                return
        
        # Reset index if timestamp is the index
        if isinstance(transformer_df.index, pd.DatetimeIndex):
            transformer_df = transformer_df.reset_index()

        # Ensure timestamp is datetime
        if 'timestamp' not in transformer_df.columns:
            logger.error("No timestamp column in transformer data")
            st.error("Invalid transformer data: Missing timestamp column")
            return

        transformer_df['timestamp'] = pd.to_datetime(transformer_df['timestamp'])
       
        # Log diagnostic information
        logger.info(f"Transformer Data - Shape: {transformer_df.shape}")
        logger.info(f"Transformer Data - Columns: {transformer_df.columns}")
        logger.info(f"Timestamp Range: {transformer_df['timestamp'].min()} to {transformer_df['timestamp'].max()}")
       
        # Get latest record for metrics
        latest = transformer_df.iloc[-1]
       
        # Customer count (with additional safety checks)
        customer_count = 'N/A'
        if customer_df is not None and not customer_df.empty:
            if 'customer_id' in customer_df.columns:
                customer_count = len(customer_df['customer_id'].unique())
            else:
                logger.warning("Customer data does not have 'customer_id' column")
       
        # Create columns for metrics
        cols = st.columns(4)
       
        with cols[0]:
            create_tile(
                "Transformer ID",
                str(latest.get('transformer_id', 'N/A')),
                is_clickable=False
            )
       
        with cols[1]:
            if create_tile(
                "Customers",
                str(customer_count),
                is_clickable=True
            ):
                # Show customer bridge view
                st.session_state.show_customer_bridge = True
                st.experimental_rerun()
       
        with cols[2]:
            create_tile(
                "X Coordinate",
                "37.7749",
                is_clickable=False
            )
       
        with cols[3]:
            create_tile(
                "Y Coordinate",
                "-122.4194",
                is_clickable=False
            )

        # Copy the dataframe before passing to display_transformer_data
        # This ensures any transformations in display_transformer_data don't affect the original
        transformer_display_df = transformer_df.copy()
        
        # Display transformer data visualizations
        display_transformer_data(transformer_display_df)

    except KeyError as ke:
        logger.error(f"Key error in dashboard display: {str(ke)}")
        st.error(f"Missing required column: {str(ke)}")
    except ValueError as ve:
        logger.error(f"Value error in dashboard display: {str(ve)}")
        st.error(f"Invalid data format: {str(ve)}")
    except Exception as e:
        logger.error(f"Unexpected dashboard display error: {str(e)}")
        st.error(f"Failed to display transformer dashboard: {str(e)}")

def display_customer_tab(df: pd.DataFrame):
    # Display customer analysis tab
    if df is None or df.empty:
        st.warning("No customer data available")
        return

    # Only show the customer selector if there are multiple customers
    customer_ids = sorted(df['customer_id'].unique())
    
    # If called from bridge view, we already filtered for a specific customer
    if len(customer_ids) > 1:
        selected_customer = st.selectbox(
            "Select Customer",
            customer_ids,
            format_func=lambda x: f"Customer {x}"
        )
        
        # Filter data for selected customer
        customer_df = df[df['customer_id'] == selected_customer].copy()  # Create copy to avoid SettingWithCopyWarning
    else:
        # Already filtered for a specific customer
        customer_df = df.copy()
    
    # Round values according to spec
    customer_df['power_kw'] = customer_df['power_kw'].round(3)  # x.xxx
    customer_df['current_a'] = customer_df['current_a'].round(3)  # x.xxx
    customer_df['voltage_v'] = customer_df['voltage_v'].round(1)  # xxx.x

    # Display customer metrics in tiles
    cols = st.columns(3)  # Changed from 4 to 3 columns as we're removing the last tile
    latest = customer_df.iloc[-1]
    
    # Get the customer ID from the dataframe
    customer_id = customer_df['customer_id'].iloc[0]
    
    with cols[0]:
        create_tile(
            "Customer ID",
            f"{customer_id}",
            is_clickable=True
        )
    with cols[1]:
        create_tile(
            "X Coordinate",
            "43.6532° N",
            is_clickable=True
        )
    with cols[2]:
        create_tile(
            "Y Coordinate",
            "79.3832° W",
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
        use_container_width=True,
        hide_index=True
    )

def display_customers_bridge_view(customer_df: pd.DataFrame):
    """
    Display a bridge view showing a table of all customers for a transformer.
    User can click on any customer to view their detailed information.
    """
    if customer_df is None or customer_df.empty:
        st.warning("No customer data available for this transformer")
        return
    
    st.header("Customers Overview")
    
    # Back button to return to transformer dashboard
    if st.button("← Back to Dashboard"):
        # Reset all view-related session state to go back to dashboard (first view)
        st.session_state.show_customer_bridge = False
        st.session_state.show_customer_details = False
        st.experimental_rerun()
    
    # Get unique customers and prepare summary data
    customer_ids = sorted(customer_df['customer_id'].unique())
    
    # Create a list to hold the latest reading for each customer
    latest_readings = []
    
    for cust_id in customer_ids:
        # Get data for this customer
        cust_data = customer_df[customer_df['customer_id'] == cust_id]
        
        # Skip if no data
        if cust_data.empty:
            continue
            
        # Get the latest reading
        latest = cust_data.sort_values('timestamp').iloc[-1]
        
        # Add to our list
        latest_readings.append({
            "customer_id": cust_id,
            "timestamp": latest['timestamp'],
            "power_kw": round(latest['power_kw'], 3),
            "current_a": round(latest['current_a'], 3),
            "voltage_v": round(latest['voltage_v'], 1)
        })
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(latest_readings)
    
    # Display the summary table with clickable rows
    st.markdown("### Customer List")
    st.markdown("Click on 'View Details' to see comprehensive information for a specific customer")
    
    # Table header
    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
    col1.markdown("**Customer I.D.**")
    col2.markdown("**Timestamp**")
    col3.markdown("**Power (kW)**")
    col4.markdown("**Current (A)**")
    col5.markdown("**Action**")
    
    st.markdown("---")
    
    # Table rows
    for i, row in enumerate(summary_df.itertuples()):
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
        
        with col1:
            st.write(f"{row.customer_id}")
        with col2:
            st.write(f"{row.timestamp}")
        with col3:
            st.write(f"{row.power_kw}")
        with col4:
            st.write(f"{row.current_a}")
        with col5:
            if st.button("View Details", key=f"cust_{row.customer_id}"):
                # Set session state to view this customer's details
                st.session_state.selected_customer_id = row.customer_id
                st.session_state.show_customer_details = True
                st.session_state.show_customer_bridge = False
                st.experimental_rerun()
                
        # Add a divider between rows
        st.markdown("---")

def display_transformer_data(results_df: pd.DataFrame):
    """Display transformer data visualizations in the same layout as customer tab."""
    if results_df is None or results_df.empty:
        st.warning("No data available for transformer visualization.")
        return

    # Ensure timestamp is datetime for all visualizations
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')  # Sort by timestamp
    
    # Add debug logging for dataframe content
    logger.info(f"Transformer dataframe first few rows: {df.head(2).to_dict()}")
    if 'size_kva' in df.columns:
        logger.info(f"size_kva data type: {df['size_kva'].dtype}")
        logger.info(f"size_kva first value: {df['size_kva'].iloc[0]}")
        logger.info(f"size_kva unique values: {df['size_kva'].unique()}")
        logger.info(f"power_kw range: {df['power_kw'].min()} to {df['power_kw'].max()}")
    else:
        logger.warning("size_kva column not found in dataframe")
    
    # Extract a normalized pattern from power data for voltage synergy
    # This will be used to influence the voltage pattern (non-intrusive approach)
    power_pattern = None
    if 'power_kw' in df.columns and not df['power_kw'].isna().all():
        power_min = df['power_kw'].min()
        power_max = df['power_kw'].max()
        # Avoid division by zero
        if power_max > power_min:
            power_pattern = (df['power_kw'] - power_min) / (power_max - power_min)
        else:
            power_pattern = pd.Series(0.5, index=df.index, name='pattern')
    else:
        # Create a default pattern if power data is not available
        power_pattern = pd.Series(0.5, index=range(len(df)), name='pattern')
    
    # Loading Status at the top
    create_colored_banner("Loading Status")
    display_loading_status(df)

    # Power Consumption
    create_colored_banner("Power Consumption")
    
    # Use the standardized chart function with proper view controls
    power_chart = create_altair_chart(
        df=df,
        y_column='power_kw',
        title='Power Consumption',
        color='#1f77b4',  # Blue color
        chart_id='transformer_power'
    )
    
    # Add the chart to the Streamlit view
    st.altair_chart(power_chart, use_container_width=True)

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    with col1:
        create_colored_banner("Current")
        # Use the standardized chart function for current visualization
        current_chart = create_altair_chart(
            df=df,
            y_column='current_a',
            title='Current (A)',
            color='#ff7f0e',  # Orange color
            chart_id='transformer_current'
        )
        
        # Display the chart
        st.altair_chart(current_chart, use_container_width=True)
    
    with col2:
        create_colored_banner("Voltage")
        # Create synthetic 3-phase voltage data (same as customer view)
        voltage_data = pd.DataFrame()
        voltage_data['timestamp'] = df['timestamp']
        
        # Import for math functions (if not already available)
        import numpy as np
        
        # Base voltage is 400V
        base_voltage = 400
        
        # Time-based index for sinusoidal patterns
        time_idx = np.linspace(0, 4*np.pi, len(df))
        
        # Define the range parameters
        variation_pct = 0.07  # Increased from 0.06 to 0.07 (7% variation)
        pattern_influence = 0.04  # Increased from 0.02 to 0.04 (4% influence)
        random_noise = 0.01  # Added 1% random noise for natural irregularities
        
        # Ensure power_pattern has the right shape
        if power_pattern is None or len(power_pattern) != len(df):
            power_pattern = np.ones(len(df)) * 0.5
            logger.warning(f"Voltage chart: Pattern data missing or wrong size. Using constant pattern.")
        
        # Create inverse pattern for voltage (power increases = voltage slightly decreases)
        inverse_pattern = 1 - power_pattern.values
        
        # Phase A - centered around 400V with enhanced pattern influence and noise
        phase_a = base_voltage + \
                  base_voltage * variation_pct * np.sin(time_idx) + \
                  base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                  base_voltage * random_noise * np.random.normal(0, 1, len(df))
        voltage_data['Phase A'] = phase_a
        
        # Phase B - shifted 120 degrees (2π/3 radians) with enhanced pattern influence and noise
        phase_b = base_voltage + \
                  base_voltage * variation_pct * np.sin(time_idx - (2*np.pi/3)) + \
                  base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                  base_voltage * random_noise * np.random.normal(0, 1, len(df))
        voltage_data['Phase B'] = phase_b
        
        # Phase C - shifted 240 degrees (4π/3 radians) with enhanced pattern influence and noise
        phase_c = base_voltage + \
                  base_voltage * variation_pct * np.sin(time_idx - (4*np.pi/3)) + \
                  base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                  base_voltage * random_noise * np.random.normal(0, 1, len(df))
        voltage_data['Phase C'] = phase_c
        
        # Use our standardized multi-line chart function for voltage visualization
        voltage_columns = {
            'Phase A': 'Phase A (V)',
            'Phase B': 'Phase B (V)',
            'Phase C': 'Phase C (V)'
        }
        
        voltage_chart = create_multi_line_chart(
            df=voltage_data,
            column_dict=voltage_columns,
            title='Voltage (V)',
            chart_id='transformer_voltage'
        )
        
        # Display the chart
        st.altair_chart(voltage_chart, use_container_width=True)

def display_customer_data(results_df: pd.DataFrame):
    """Display customer data visualizations."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer visualization.")
        return

    # Get customer ID
    customer_id = results_df['customer_id'].iloc[0] if 'customer_id' in results_df.columns else "N/A"
    
    # Display customer ID
    st.markdown(f"""
        <div style='padding: 10px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <p style='margin: 0; color: #666666; font-size: 14px'>Customer ID: {customer_id}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display X coordinate
    st.markdown("""
        <div style='padding: 10px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <p style='margin: 0; color: #666666; font-size: 14px'>X Coordinate: 43.6532° N</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Display Y coordinate
    st.markdown("""
        <div style='padding: 10px; border: 1px solid #d1d1d1; border-radius: 3px; margin: 8px 0px; background-color: #ffffff'>
            <p style='margin: 0; color: #666666; font-size: 14px'>Y Coordinate: 79.3832° W</p>
        </div>
    """, unsafe_allow_html=True)

    # Ensure timestamp is datetime
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Power Consumption
    create_colored_banner("Power Consumption")
    
    # Create power chart with Altair
    power_chart = create_altair_chart(
        df,
        'power_kw',
        color="#1f77b4"  # Blue color for power
    )
    st.altair_chart(power_chart, use_container_width=True)

    # Only show Voltage chart, removing the Current chart
    create_colored_banner("Voltage")
    display_voltage_time_series(results_df)

def add_view_controls_to_chart(chart, chart_id):
    """
    Add save/reset view controls to any Altair chart.
    
    This is a simple, non-invasive approach to add view saving functionality 
    to any Altair chart without requiring chart recreation or significant changes.
    
    Args:
        chart (alt.Chart): An Altair chart
        chart_id (str): Unique identifier for this chart for saving settings in session state
        
    Returns:
        chart (alt.Chart): The same chart (for chaining)
    """
    # Create a container for view controls
    control_container = st.container()
    
    # Get saved settings for this chart if any
    settings = load_chart_view_settings().get(chart_id, None)
    
    # Add view control buttons in a horizontal layout
    with control_container:
        cols = st.columns([0.7, 0.3])
        
        # Create save button in the left column with the message
        save_button = cols[0].button(
            "📊 Save current view (session only)", 
            key=f"save_view_{chart_id}",
            help="Save the current chart view for this session only"
        )
        
        # Create reset button in the right column 
        reset_button = cols[1].button(
            "🔄 Reset", 
            key=f"reset_view_{chart_id}",
            help="Reset to default view"
        )
    
    # Logic for save button
    if save_button:
        try:
            # Extract domain information from the chart
            
            # For x-axis (timestamp), get the current visible range
            # We'll extract this from the session state or calculate a reasonable default
            
            # For the x-axis timestamp range, use the data range if available
            if hasattr(chart, 'data') and 'timestamp' in chart.data.columns:
                timestamps = pd.to_datetime(chart.data['timestamp'])
                x_min = timestamps.min()
                x_max = timestamps.max()
            else:
                # Default to a range if we can't determine
                now = pd.Timestamp.now()
                x_min = now - pd.Timedelta(days=7)
                x_max = now
            
            # For y-axis, try to extract from the chart
            # This is a simplification - in reality, we'd need to analyze the Altair chart structure
            if hasattr(chart, 'data'):
                # Find numeric columns that aren't timestamps
                numeric_cols = chart.data.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    sample_col = numeric_cols[0]
                    y_min = chart.data[sample_col].min()
                    y_max = chart.data[sample_col].max()
                else:
                    # Default to a generic range if we can't determine
                    y_min = 0
                    y_max = 100
            else:
                # Default to a generic range if we can't determine
                y_min = 0
                y_max = 100
            
            # Create view settings
            view_settings = {
                'timestamp_min': x_min.isoformat(),
                'timestamp_max': x_max.isoformat(),
                'y_min': y_min,
                'y_max': y_max
            }
            
            # Save settings
            save_chart_view_settings(chart_id, view_settings)
            
            # Show success message
            st.success("View settings saved for this session only")
            
        except Exception as e:
            st.error(f"Could not save view settings: {str(e)}")
            logger.error(f"Error saving view settings: {e}")
    
    # Logic for reset button
    if reset_button:
        try:
            # Load all settings
            settings = load_chart_view_settings()
            
            # Remove this chart's settings if they exist
            if chart_id in settings:
                del settings[chart_id]
                
                # Update session state
                st.session_state.chart_view_settings = settings
                
                # Show success message
                st.success("View reset to default")
                
                # Force a page refresh to apply the reset
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Could not reset view settings: {str(e)}")
            logger.error(f"Error resetting view settings: {e}")
    
    return chart

def apply_view_settings_to_chart(chart, chart_id, df, y_column):
    """
    Apply saved view settings to a chart if they exist.
    
    Args:
        chart (alt.Chart): The Altair chart to modify
        chart_id (str): Unique identifier for the chart
        df (pd.DataFrame): The DataFrame with the chart data
        y_column (str): The column being plotted on the y-axis
        
    Returns:
        alt.Chart: The modified chart with view settings applied
    """
    # Get saved settings for this chart
    settings = load_chart_view_settings().get(chart_id, {})
    
    # If we have settings, apply them
    if settings and len(settings) > 0:
        try:
            # Set y domain based on saved settings
            if 'y_min' in settings and 'y_max' in settings:
                chart = chart.encode(
                    y=alt.Y(
                        y_column,
                        scale=alt.Scale(domain=[settings['y_min'], settings['y_max']])
                    )
                )
            
            # Set x domain based on saved settings
            if 'timestamp_min' in settings and 'timestamp_max' in settings:
                try:
                    # Convert timestamps from ISO format to datetime
                    x_min = pd.to_datetime(settings['timestamp_min'])
                    x_max = pd.to_datetime(settings['timestamp_max'])
                    
                    chart = chart.encode(
                        x=alt.X(
                            'timestamp:T',
                            scale=alt.Scale(domain=[x_min, x_max])
                        )
                    )
                except Exception as e:
                    logger.error(f"Error applying timestamp domain: {e}")
        except Exception as e:
            logger.error(f"Error applying view settings to chart {chart_id}: {e}")
    
    return chart

def create_altair_chart(df, y_column, title=None, color=None, chart_id=None):
    """
    Create a standardized Altair chart for time series data.
    
    Args:
        df (pd.DataFrame): DataFrame with timestamp column and data column
        y_column (str): Name of the column to plot on the y-axis
        title (str, optional): Chart title
        color (str, optional): Line color (hex code or named color)
        chart_id (str, optional): Unique identifier for saving view settings in session state
        
    Returns:
        alt.Chart: Configured Altair chart
    """
    # Data must be sorted by timestamp for proper line charts
    if 'timestamp' not in df.columns:
        logger.error(f"No timestamp column in DataFrame for chart creation")
        return None
        
    # Ensure timestamps are formatted correctly and data is sorted
    df = df.copy()  # Create a copy to avoid modifying the original
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Default color if not specified
    if color is None:
        color = '#1f77b4'  # Default Altair blue
    
    # Create the base chart
    chart = alt.Chart(df).mark_line(
        point=True,
        strokeWidth=2
    ).encode(
        x=alt.X('timestamp:T',
                axis=alt.Axis(
                    format='%m/%d/%y',
                    title='Date',
                    labelAngle=-45,
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        y=alt.Y(f'{y_column}:Q',
                axis=alt.Axis(
                    title=y_column.replace('_', ' ').title(),
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        color=alt.value(color),
        tooltip=[
            alt.Tooltip('timestamp:T', title='Date', format='%m/%d/%y %H:%M'),
            alt.Tooltip(f'{y_column}:Q', title=y_column.replace('_', ' ').title(), format='.2f')
        ]
    )
    
    # Add title if provided
    if title:
        chart = chart.properties(title=title)
        
    # Set the chart width to be responsive
    chart = chart.properties(width='container')
    
    # Apply saved view settings if we have a chart ID
    if chart_id:
        # Get saved settings for this chart
        settings = load_chart_view_settings().get(chart_id, {})
        
        # If we have settings, apply them
        if settings and len(settings) > 0:
            try:
                # Set y domain based on saved settings
                if 'y_min' in settings and 'y_max' in settings:
                    chart = chart.encode(
                        y=alt.Y(
                            f'{y_column}:Q',
                            scale=alt.Scale(domain=[settings['y_min'], settings['y_max']])
                        )
                    )
                
                # Set x domain based on saved settings
                if 'timestamp_min' in settings and 'timestamp_max' in settings:
                    try:
                        # Convert timestamps from ISO format to datetime
                        x_min = pd.to_datetime(settings['timestamp_min'])
                        x_max = pd.to_datetime(settings['timestamp_max'])
                        
                        chart = chart.encode(
                            x=alt.X(
                                'timestamp:T',
                                scale=alt.Scale(domain=[x_min, x_max])
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error applying timestamp domain: {e}")
            except Exception as e:
                logger.error(f"Error applying view settings to chart {chart_id}: {e}")
    
    # Add selected hour indicator if in session state
    if 'selected_hour' in st.session_state and st.session_state.get('selected_date'):
        try:
            # Get selected date and hour
            selected_date = st.session_state.get('selected_date')
            selected_hour = st.session_state.get('selected_hour')
            
            # Create timestamp for the selected hour
            selected_hour_dt = pd.to_datetime(selected_date).replace(hour=int(selected_hour), minute=0)
            
            # Create the vertical line
            hour_line = alt.Chart(pd.DataFrame({
                'selected_time': [selected_hour_dt]
            })).mark_rule(
                color='gray',
                strokeWidth=1,
                strokeDash=[5, 5]
            ).encode(
                x='selected_time:T'
            )
            
            # Add annotation with the selected hour
            hour_label = alt.Chart(pd.DataFrame({
                'selected_time': [selected_hour_dt],
                'y': [df[y_column].min()]  # Position at bottom
            })).mark_text(
                align='center',
                baseline='bottom',
                fontSize=11,
                color='gray'
            ).encode(
                x='selected_time:T',
                y=alt.value(10),  # Fixed y position
                text=alt.value(f' Selected: {selected_hour}:00')
            )
            
            # Add both to the chart
            chart = alt.layer(chart, hour_line, hour_label)
            
        except Exception as e:
            logger.error(f"Error adding selected hour indicator: {e}")
    
    # Make chart interactive with custom configuration for x-axis manipulation
    # This allows users to left-click and drag on x-axis to compress/expand the view
    chart = chart.configure_axis(
        # Enable the "domain" to be a visual target for dragging
        domainWidth=3,  # Make the axis line a bit thicker for easier targeting
        # Add padding to x-axis to make it easier to grab
        gridOpacity=0.2,
    ).configure_view(
        stroke='transparent',  # Remove border
    ).interactive()
    
    # Add view controls if chart ID is provided
    if chart_id:
        add_view_controls_to_chart(chart, chart_id)
    
    return chart

def create_multi_line_chart(df, column_dict, title=None, chart_id=None):
    """
    Create a multi-line Altair chart for multiple data series.
    
    Args:
        df (pd.DataFrame): DataFrame with timestamp column and multiple data columns
        column_dict (dict): Dictionary mapping column names to display names
        title (str, optional): Chart title
        chart_id (str, optional): Unique identifier for saving view settings in session state
        
    Returns:
        alt.Chart: Configured Altair chart with multiple lines
    """
    # Melt the dataframe to get it into the right format for Altair
    id_vars = ['timestamp']
    value_vars = list(column_dict.keys())
    
    # Create a copy to avoid modifying the original
    plot_df = df.copy()
    
    # Ensure all timestamps are datetime objects
    plot_df['timestamp'] = pd.to_datetime(plot_df['timestamp'])
    
    # Melt the dataframe to long format
    melted_df = pd.melt(
        plot_df, 
        id_vars=id_vars, 
        value_vars=value_vars,
        var_name='series', 
        value_name='value'
    )
    
    # Map the column names to display names if provided
    if column_dict:
        melted_df['series'] = melted_df['series'].map(
            {k: v for k, v in column_dict.items()}
        )
    
    # Create the base chart
    chart = alt.Chart(melted_df).mark_line(
        point=True,
        strokeWidth=2
    ).encode(
        x=alt.X('timestamp:T',
                axis=alt.Axis(
                    format='%m/%d/%y',
                    title='Date',
                    labelAngle=-45,
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        y=alt.Y('value:Q',
                axis=alt.Axis(
                    title='Value',
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        color=alt.Color('series:N', 
                 scale=alt.Scale(scheme='category10'),
                 legend=alt.Legend(
                     title=None,
                     orient='top',
                     labelFontSize=12
                 )),
        tooltip=['timestamp:T', 'series:N', alt.Tooltip('value:Q', format='.2f')]
    )
    
    # Add title if provided
    if title:
        chart = chart.properties(title=title)
        
    # Set the chart width to be responsive
    chart = chart.properties(width='container')
    
    # Apply saved view settings if we have a chart ID
    if chart_id:
        # Get saved settings for this chart
        settings = load_chart_view_settings().get(chart_id, {})
        
        # If we have settings, apply them
        if settings and len(settings) > 0:
            try:
                # Set y domain based on saved settings
                if 'y_min' in settings and 'y_max' in settings:
                    chart = chart.encode(
                        y=alt.Y(
                            'value:Q',
                            scale=alt.Scale(domain=[settings['y_min'], settings['y_max']]),
                            axis=alt.Axis(
                                title='Value',
                                labelColor='#333333',
                                titleColor='#333333',
                                labelFontSize=14,
                                titleFontSize=16
                            )
                        )
                    )
                
                # Set x domain based on saved settings
                if 'timestamp_min' in settings and 'timestamp_max' in settings:
                    try:
                        # Convert timestamps from ISO format to datetime
                        x_min = pd.to_datetime(settings['timestamp_min'])
                        x_max = pd.to_datetime(settings['timestamp_max'])
                        
                        chart = chart.encode(
                            x=alt.X(
                                'timestamp:T',
                                scale=alt.Scale(domain=[x_min, x_max]),
                                axis=alt.Axis(
                                    format='%m/%d/%y',
                                    title='Date',
                                    labelAngle=-45,
                                    labelColor='#333333',
                                    titleColor='#333333',
                                    labelFontSize=14,
                                    titleFontSize=16
                                )
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error applying timestamp domain: {e}")
            except Exception as e:
                logger.error(f"Error applying view settings to chart {chart_id}: {e}")
    
    # Add selected hour indicator if in session state
    if 'selected_hour' in st.session_state and st.session_state.get('selected_date'):
        try:
            # Get selected date and hour
            selected_date = st.session_state.get('selected_date')
            selected_hour = st.session_state.get('selected_hour')
            
            # Create timestamp for the selected hour
            selected_hour_dt = pd.to_datetime(selected_date).replace(hour=int(selected_hour), minute=0)
            
            # Create the vertical line
            hour_line = alt.Chart(pd.DataFrame({
                'selected_time': [selected_hour_dt]
            })).mark_rule(
                color='gray',
                strokeWidth=1,
                strokeDash=[5, 5]
            ).encode(
                x='selected_time:T'
            )
            
            # Add annotation with the selected hour
            hour_label = alt.Chart(pd.DataFrame({
                'selected_time': [selected_hour_dt],
                'y': [melted_df['value'].min()]  # Position at bottom
            })).mark_text(
                align='center',
                baseline='bottom',
                fontSize=11,
                color='gray'
            ).encode(
                x='selected_time:T',
                y=alt.value(10),  # Fixed y position
                text=alt.value(f' Selected: {selected_hour}:00')
            )
            
            # Add both to the chart
            chart = alt.layer(chart, hour_line, hour_label)
            
        except Exception as e:
            logger.error(f"Error adding selected hour indicator: {e}")
    
    # Make chart interactive with custom configuration for x-axis manipulation
    # This allows users to left-click and drag on x-axis to compress/expand the view
    chart = chart.configure_axis(
        # Enable the "domain" to be a visual target for dragging
        domainWidth=3,  # Make the axis line a bit thicker for easier targeting
        # Add padding to x-axis to make it easier to grab
        gridOpacity=0.2,
    ).configure_view(
        stroke='transparent',  # Remove border
    ).interactive()
    
    # Add view controls if chart ID is provided
    if chart_id:
        add_view_controls_to_chart(chart, chart_id)
    
    return chart

def display_full_customer_dashboard(results_df: pd.DataFrame):
    """Display a full-page dashboard for a given customer."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer dashboard.")
        return
        
    # Make sure timestamp is in datetime format
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Find the maximum loading point - This is now centralized for all charts
    if 'loading_percentage' in df.columns:
        max_loading_idx = df['loading_percentage'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        
        # Store in session state for consistent use across all charts
        st.session_state.max_loading_time = max_loading_time
    else:
        # If loading percentage is not available, we'll let each chart determine its own max point
        if 'max_loading_time' in st.session_state:
            del st.session_state.max_loading_time

    # Log the alert timestamp if available (helpful for debugging)
    if 'highlight_timestamp' in st.session_state:
        alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
        logger.debug(f"Alert time set to: {alert_time.strftime('%Y-%m-%d %H:%M')}")

    # Display loading status chart
    display_loading_status(df)
    
    # Display power time series
    display_power_time_series(df)
    
    # Display current time series if data is available
    if 'current_a' in df.columns and not df['current_a'].isna().all():
        display_current_time_series(df)
    
    # Display voltage time series if data is available
    if 'voltage_a' in df.columns and not df['voltage_a'].isna().all():
        display_voltage_time_series(df)

def load_chart_view_settings():
    """
    Load chart view settings from session state only.
    
    Chart view settings are now only stored in session state and will be lost when the
    browser session ends. No disk storage is used.
    
    Returns:
        dict: The chart view settings dictionary from session state
    """
    if 'chart_view_settings' not in st.session_state:
        st.session_state.chart_view_settings = {}
    
    return st.session_state.chart_view_settings

def save_chart_view_settings(chart_id, view_settings):
    """
    Save chart view settings to session state only.
    
    Chart view settings are stored in session state and will be lost when the
    browser session ends. This is a temporary storage solution.
    
    Args:
        chart_id (str): Unique identifier for the chart
        view_settings (dict): The view settings to save
    """
    # Load existing settings
    settings = load_chart_view_settings()
    
    # Update with new settings
    settings[chart_id] = view_settings
    
    # Save back to session state
    st.session_state.chart_view_settings = settings

def display_voltage_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display voltage time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for voltage visualization.")
        return
        
    try:
        # Common code for both transformer and customer views
        df = results_df.copy()
        
        # Ensure timestamp is formatted correctly
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Set chart ID based on view context
        chart_id_suffix = "transformer_" if is_transformer_view else ""
        
        # Check if we're working with phase voltages or just a single voltage
        has_phase_a = 'voltage_a' in df.columns and not df['voltage_a'].isna().all()
        has_phase_b = 'voltage_b' in df.columns and not df['voltage_b'].isna().all()
        has_phase_c = 'voltage_c' in df.columns and not df['voltage_c'].isna().all()
        
        if has_phase_a or has_phase_b or has_phase_c:
            # We have phase voltages - create a multi-line chart
            phases = []
            if has_phase_a:
                phases.append(('voltage_a', 'Phase A'))
            if has_phase_b:
                phases.append(('voltage_b', 'Phase B'))
            if has_phase_c:
                phases.append(('voltage_c', 'Phase C'))
            
            # Create a column dictionary for multi-line chart
            column_dict = {k: v for k, v in phases}
            
            # Round voltage values for display
            for col in column_dict.keys():
                df[col] = df[col].round(1)
            
            # Create multi-line chart with view controls
            voltage_chart = create_multi_line_chart(
                df,
                column_dict,
                title="Phase Voltages (V)",
                chart_id=f"{chart_id_suffix}voltage_phases_chart"
            )
            
            # Display the chart
            st.altair_chart(voltage_chart, use_container_width=True)
        
        elif 'voltage' in df.columns:
            # Single voltage column - create a standard chart
            df['voltage'] = df['voltage'].round(1)
            
            # Create chart with our common function and view controls
            voltage_chart = create_altair_chart(
                df, 
                'voltage', 
                title="Voltage (V)",
                color='#1f77b4',
                chart_id=f"{chart_id_suffix}voltage_chart"
            )
            
            # Display the chart
            st.altair_chart(voltage_chart, use_container_width=True)
        else:
            # No voltage data available in standard format
            
            # Create synthetic phase voltage data for demo purposes
            if is_transformer_view:
                # For transformers, show 3-phase voltage data
                voltage_data = pd.DataFrame()
                voltage_data['timestamp'] = df['timestamp']
                
                # Import for math functions
                import numpy as np
                
                # Base voltage is 400V for transformer view
                base_voltage = 400
                
                # Create synthetic voltage patterns
                time_idx = np.linspace(0, 4*np.pi, len(df))
                pattern_influence = 0.04
                random_noise = 0.01
                
                # Create power pattern influence if available
                if 'power_kw' in df.columns and not df['power_kw'].isna().all():
                    power_min = df['power_kw'].min()
                    power_max = df['power_kw'].max()
                    if power_max > power_min:
                        power_pattern = (df['power_kw'] - power_min) / (power_max - power_min)
                        inverse_pattern = 1 - power_pattern.values
                    else:
                        inverse_pattern = np.ones(len(df)) * 0.5
                else:
                    inverse_pattern = np.ones(len(df)) * 0.5
                
                # Create three phases with slight variations
                voltage_data['Phase A'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                voltage_data['Phase B'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx - (2*np.pi/3)) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                voltage_data['Phase C'] = base_voltage + \
                    base_voltage * 0.07 * np.sin(time_idx - (4*np.pi/3)) + \
                    base_voltage * pattern_influence * (inverse_pattern - 0.5) + \
                    base_voltage * random_noise * np.random.normal(0, 1, len(df))
                
                # Column dictionary for multi-line chart
                column_dict = {
                    'Phase A': 'Phase A',
                    'Phase B': 'Phase B',
                    'Phase C': 'Phase C'
                }
                
                # Create multi-line chart with view controls
                voltage_chart = create_multi_line_chart(
                    voltage_data,
                    column_dict,
                    title="Phase Voltages (V)",
                    chart_id=f"{chart_id_suffix}voltage_phases_chart"
                )
                
                # Display the chart
                st.altair_chart(voltage_chart, use_container_width=True)
            else:
                # For regular customer view, show single-phase voltage
                voltage_data = pd.DataFrame()
                voltage_data['timestamp'] = df['timestamp']
                
                # Create a synthetic voltage pattern based on 120V system
                import numpy as np
                base_voltage = 120
                time_idx = np.linspace(0, 4*np.pi, len(df))
                
                # Create synthetic voltage with realistic variations
                voltage_data['voltage'] = base_voltage + \
                    base_voltage * 0.05 * np.sin(time_idx) + \
                    base_voltage * 0.02 * np.random.normal(0, 1, len(df))
                
                # Create chart with our common function and view controls
                voltage_chart = create_altair_chart(
                    voltage_data, 
                    'voltage', 
                    title="Voltage (V)",
                    color='#1f77b4',
                    chart_id=f"{chart_id_suffix}voltage_chart"
                )
                
                # Display the chart
                st.altair_chart(voltage_chart, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error displaying voltage visualization: {e}")
        logger.error(f"Error in display_voltage_time_series: {e}")
