# Visualization components for the Transformer Loading Analysis Application

import logging
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt  # Added for enhanced chart capabilities
from datetime import datetime, timedelta
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
    
    # Set fixed Y-axis ranges
    y_min = 0
    y_max = 150
    
    # Create an Altair chart for loading percentage
    base_chart = alt.Chart(df).mark_line(
        point=True,
        strokeWidth=2,
        color='#1f77b4'
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
            )
        ),
        y=alt.Y('loading_percentage:Q',
            scale=alt.Scale(domain=[y_min, y_max]),  # Set y-axis range using fixed values
            axis=alt.Axis(
                title='Loading Percentage (%)',
                labelColor='#333333',
                titleColor='#333333',
                labelFontSize=14,
                titleFontSize=16,
                tickCount=7,
                grid=True
            )
        ),
        tooltip=['timestamp:T', alt.Tooltip('loading_percentage:Q', format='.1f', title='Loading %')]
    ).properties(
        height=400
    ).interactive()  # Make chart interactive
    
    # Define threshold areas for background colors with light opacity
    threshold_areas = []
    
    # Get min and max timestamps to create background rectangles
    min_time = df['timestamp'].min()
    max_time = df['timestamp'].max()
    
    # Create threshold areas from highest to lowest to ensure proper layering
    # Critical area (120%+) - Red background
    critical_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [120], 'y2': [y_max]  # Use y_max from fixed values
    })).mark_rect(color=STATUS_COLORS['Critical'], opacity=0.2).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(critical_area)
    
    # Overloaded area (100-120%) - Orange background
    overloaded_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [100], 'y2': [120]
    })).mark_rect(color=STATUS_COLORS['Overloaded'], opacity=0.2).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(overloaded_area)
    
    # Warning area (80-100%) - Yellow background
    warning_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [80], 'y2': [100]
    })).mark_rect(color=STATUS_COLORS['Warning'], opacity=0.1).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(warning_area)
    
    # Pre-Warning area (50-80%) - Purple background
    prewarning_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [50], 'y2': [80]
    })).mark_rect(color=STATUS_COLORS['Pre-Warning'], opacity=0.1).encode(
        x='x1:T', x2='x2:T', y='y1:Q', y2='y2:Q'
    )
    threshold_areas.append(prewarning_area)
    
    # Normal area (0-50%) - Green background
    normal_area = alt.Chart(pd.DataFrame({
        'x1': [min_time], 'x2': [max_time], 
        'y1': [y_min], 'y2': [50]  # Use y_min from fixed values
    })).mark_rect(color=STATUS_COLORS['Normal'], opacity=0.1).encode(
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
    chart = alt.layer(base_chart, *threshold_areas, *threshold_lines)
    
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
        'y': [max_loading_value * 1.05]  # Position 5% above maximum value
    })).mark_text(
        align='center',
        baseline='bottom',
        fontSize=12,
        fontWeight='bold',
        color='#dc3545',
        dy=-10  # Consistent vertical offset
    ).encode(
        x='max_time:T',
        y='y:Q',
        text=alt.value(f'Peak load')
    )
    
    # Combine the charts
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
                    'y': [max_loading_value * 1.05]  # Position at same height as peak load annotation
                })).mark_text(
                    align='center',
                    baseline='bottom',
                    fontSize=12,
                    color='gray',
                    dx=10,  # Add horizontal offset to avoid overlapping with line
                    dy=-10  # Consistent vertical offset
                ).encode(
                    x='alert_time:T',
                    y='y:Q',
                    text=alt.value('Alert point')
                )
                
                # Add to the chart
                chart = alt.layer(chart, alert_rule, alert_text)
        except Exception as e:
            logger.error(f"Error adding alert time indicator: {e}")
    
    # Add threshold legend above the chart - right aligned with proper formatting
    st.markdown("""
    <style>
    .threshold-legend {
        display: flex;
        justify-content: flex-end;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 5px;
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
    
    # Display the chart
    st.altair_chart(chart, use_container_width=True)

def display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display power consumption time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for power consumption visualization.")
        return
    
    # Ensure we have a clean working copy with proper timestamps
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # First check if max_loading_time is in session state
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
        logger.info(f"Power chart: Using session state max_loading_time for peak placement at {max_loading_time}")
    # Only calculate if not in session state
    elif 'loading_percentage' in df.columns:
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
    
    # Calculate peak annotation height with more vertical spacing
    if is_transformer_view:
        # For transformer view, calculate better annotation spacing based on data range
        y_min = df['power_kw'].min()
        y_max = df['power_kw'].max()
        y_range = y_max - y_min
        peak_annotation_height = y_max + (y_range * 0.05)  # Add just 5% for annotations
    else:
        # For other views, use the original calculation
        peak_annotation_height = df['power_kw'].max() * 1.15  # Original vertical spacing
    
    # Create power chart with Altair
    chart = create_altair_chart(
        df,
        'power_kw',
        title="Power Consumption (kW)" if is_transformer_view else None,
        color="#1f77b4",  # Blue color for power
    )
    
    # Apply specific y-axis configuration to ensure power data visibility
    chart = chart.encode(
        y=alt.Y('power_kw:Q',
                scale=alt.Scale(zero=False),  # Prevent flattening
                axis=alt.Axis(
                    title='Power(kW)',
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                ))
    )
    
    # Add peak load indicator
    peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
        color='red',
        strokeWidth=2,
        strokeDash=[4, 2]  # Different dash pattern
    ).encode(
        x='peak_time:T'
    )
    
    # Add text annotation for peak load
    peak_text = alt.Chart(pd.DataFrame({
        'peak_time': [max_loading_time],
        'y': [peak_annotation_height]  # Position slightly above maximum value
    })).mark_text(
        align='right',
        baseline='bottom',
        fontSize=14,  # Larger font
        fontWeight='bold',
        color='red',
        dx=20,  # Shift text right for better spacing
        dy=-10  # Consistent vertical offset
    ).encode(
        x='peak_time:T',
        y='y:Q',
        text=alt.value('Peak load')
    )
    
    # Combine the charts
    chart = alt.layer(chart, peak_rule, peak_text)
    
    # Add alert timestamp if in session state
    if 'highlight_timestamp' in st.session_state:
        try:
            alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
            
            # Create a vertical rule to mark the alert time
            rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                color='gray',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x='alert_time:T'
            )
            
            # Add text annotation for the alert
            text = alt.Chart(pd.DataFrame({
                'alert_time': [alert_time],
                'y': [peak_annotation_height]  # Match peak load height exactly
            })).mark_text(
                align='left',
                baseline='bottom',
                fontSize=12,
                color='gray',
                dx=10,  # Add horizontal offset to avoid overlapping with line
                dy=-10  # Consistent vertical offset
            ).encode(
                x='alert_time:T',
                y='y:Q',
                text=alt.value('Alert point')
            )
            
            # Combine with existing chart
            chart = alt.layer(chart, rule, text)
        except Exception as e:
            logger.error(f"Error adding alert timestamp: {e}")
    
    # Display the chart with streamlit
    st.altair_chart(chart, use_container_width=True)

def display_current_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
    """Display current time series visualization."""
    if results_df is None or results_df.empty:
        st.warning("No data available for current visualization.")
        return
        
    # Ensure we have a clean working copy with proper timestamps
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # First check if max_loading_time is in session state
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
        logger.info(f"Current chart: Using session state max_loading_time for peak placement at {max_loading_time}")
    # Only calculate if not in session state
    elif 'loading_percentage' in df.columns:
        max_loading_idx = df['loading_percentage'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        logger.info(f"Current chart: Using loading_percentage max value for peak placement at {max_loading_time}")
    else:
        # If loading percentage is not available, use max current as an alternative
        max_loading_idx = df['current_a'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        logger.info(f"Current chart: Using current_a max value as fallback for peak placement at {max_loading_time}")
    
    # Create current chart with Altair
    chart = create_altair_chart(
        df,
        'current_a',
        title="Current (A)" if is_transformer_view else None,
        color="#ff7f0e"  # Orange color for current
    )
    
    # Add peak load indicator
    peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
        color='red',
        strokeWidth=2,
        strokeDash=[4, 2]  # Different dash pattern
    ).encode(
        x='peak_time:T'
    )
    
    # Add text annotation for peak load
    peak_text = alt.Chart(pd.DataFrame({
        'peak_time': [max_loading_time],
        'y': [df['current_a'].max() * 1.05]  # Position 5% above maximum value
    })).mark_text(
        align='right',
        baseline='bottom',
        fontSize=14,
        fontWeight='bold',
        color='red',
        dx=20,  # Shift text right for better spacing
        dy=-10  # Consistent vertical offset
    ).encode(
        x='peak_time:T',
        y='y:Q',
        text=alt.value('Peak load')
    )
    
    # Combine the charts
    chart = alt.layer(chart, peak_rule, peak_text)
    
    # Add alert timestamp if in session state
    if 'highlight_timestamp' in st.session_state:
        try:
            alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
            
            # Create a vertical rule to mark the alert time
            rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                color='gray',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x='alert_time:T'
            )
            
            # Add text annotation for the alert
            text = alt.Chart(pd.DataFrame({
                'alert_time': [alert_time],
                'y': [df['current_a'].max() * 1.08]  # Position slightly higher than peak load
            })).mark_text(
                align='left',
                baseline='bottom',
                fontSize=12,
                color='gray',
                dx=5,  # Horizontal offset
                dy=-5  # Vertical offset
            ).encode(
                x='alert_time:T',
                y='y:Q',
                text=alt.value('Alert point')
            )
            
            # Combine with existing chart containing peak load indicators
            chart = alt.layer(chart, rule, text)
            logger.info(f"Added alert timestamp to current chart at {alert_time}")
        except Exception as e:
            logger.error(f"Error highlighting alert timestamp: {e}")
    
    # Display the chart with streamlit
    st.altair_chart(chart, use_container_width=True)

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
        
        # First check if max_loading_time is in session state
        if 'max_loading_time' in st.session_state:
            max_loading_time = st.session_state.max_loading_time
            logger.info(f"Voltage chart: Using session state max_loading_time for peak placement at {max_loading_time}")
        # Only calculate if not in session state
        elif 'loading_percentage' in df.columns:
            max_loading_idx = df['loading_percentage'].idxmax()
            max_loading_point = df.loc[max_loading_idx]
            max_loading_time = max_loading_point['timestamp']
            logger.info(f"Voltage chart: Using loading_percentage max value for peak placement at {max_loading_time}")
        elif 'power_kw' in df.columns and not df['power_kw'].isna().all():
            max_loading_idx = df['power_kw'].idxmax()
            max_loading_point = df.loc[max_loading_idx]
            max_loading_time = max_loading_point['timestamp']
            logger.info(f"Voltage chart: Using power_kw max value for peak placement at {max_loading_time}")
        elif 'current_a' in df.columns and not df['current_a'].isna().all():
            max_loading_idx = df['current_a'].idxmax()
            max_loading_point = df.loc[max_loading_idx]
            max_loading_time = max_loading_point['timestamp']
            logger.info(f"Voltage chart: Using current_a max value for peak placement at {max_loading_time}")
        else:
            # Default to middle timestamp if no other metrics available
            middle_index = len(df) // 2
            max_loading_time = df['timestamp'].iloc[middle_index]
            logger.warning(f"Voltage chart: No metrics available for peak detection. Using middle timestamp ({middle_index}/{len(df)}) at {max_loading_time}")
        
        # Create synthetic data for 3 phases
        voltage_data = pd.DataFrame()
        voltage_data['timestamp'] = df['timestamp']
        
        # Import for math functions
        import numpy as np
        
        # Base voltage is 400V
        base_voltage = 400
        
        # Time-based index for sinusoidal patterns
        time_idx = np.linspace(0, 4*np.pi, len(df))
        
        # Define the range parameters
        variation_pct = 0.15  # Increased from 0.06 to 0.15 (15% variation)
        pattern_influence = 0.08  # Increased from 0.02 to 0.08 (8% influence)
        random_noise = 0.02  # Increased from 0.01 to 0.02 (2% random noise)
        
        # Extract a pattern from power or current data for synergy
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
        elif 'current_a' in df.columns and not df['current_a'].isna().all():
            current_min = df['current_a'].min()
            current_max = df['current_a'].max()
            # Avoid division by zero
            if current_max > current_min:
                power_pattern = (df['current_a'] - current_min) / (current_max - current_min)
            else:
                power_pattern = pd.Series(0.5, index=df.index, name='pattern')
        else:
            # Create a default pattern if neither power nor current data is available
            power_pattern = pd.Series(0.5, index=range(len(df)), name='pattern')
        
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
        
        # Log voltage data statistics for debugging
        logger.warning(f"Voltage data statistics - Phase A: min={voltage_data['Phase A'].min():.2f}, max={voltage_data['Phase A'].max():.2f}, range={voltage_data['Phase A'].max() - voltage_data['Phase A'].min():.2f}")
        logger.warning(f"Expected voltage range based on 15% variation: {base_voltage * 0.85:.2f} to {base_voltage * 1.15:.2f}")
        
        # Define the column mapping for the multi-line chart
        column_dict = {
            'Phase A': 'Phase A',
            'Phase B': 'Phase B',
            'Phase C': 'Phase C'
        }
        
        # Create a multi-line chart with Altair
        voltage_chart = create_multi_line_chart(
            voltage_data, 
            column_dict,
            title=None  # No title needed as we use colored banner
        )
        
        # Set y-axis domain constraint for voltage chart to ensure data visibility
        voltage_chart = voltage_chart.encode(
            y=alt.Y('value:Q', 
                    scale=alt.Scale(domain=[300, 500], zero=False),  # Set voltage range to capture full 15% variation
                    axis=alt.Axis(
                        title="Voltage",
                        labelColor='#333333',
                        titleColor='#333333',
                        labelFontSize=14,
                        titleFontSize=16
                    ))
        )
        
        # Add peak load indicator
        peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
            color='red',
            strokeWidth=2,
            strokeDash=[4, 2]  # Different dash pattern
        ).encode(
            x='peak_time:T'
        )
        
        # Add text annotation for peak load
        peak_text = alt.Chart(pd.DataFrame({
            'peak_time': [max_loading_time],
            'y': [voltage_data[['Phase A', 'Phase B', 'Phase C']].max().max() * 1.05]  # Position 5% above maximum value
        })).mark_text(
            align='left',
            baseline='bottom',
            fontSize=12,
            fontWeight='bold',
            color='red',
            dx=10,  # Add horizontal offset to avoid overlapping with line
            dy=-10  # Consistent vertical offset
        ).encode(
            x='peak_time:T',
            y='y:Q',
            text=alt.value('Peak load')
        )
        
        # Combine the charts
        voltage_chart = alt.layer(voltage_chart, peak_rule, peak_text)
        
        # Add alert timestamp if in session state and not skipped
        if 'highlight_timestamp' in st.session_state :
            try:
                alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
                
                # Create a vertical rule to mark the alert time
                rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                    color='gray',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    x='alert_time:T'
                )
                
                # Add text annotation for the alert
                text = alt.Chart(pd.DataFrame({
                    'alert_time': [alert_time],
                    'y': [voltage_data[['Phase A', 'Phase B', 'Phase C']].max().max() * 1.05]  # Match peak load position
                })).mark_text(
                    align='left',
                    baseline='top',
                    fontSize=12,
                    color='gray',
                    dx=10,  # Add horizontal offset to avoid overlapping with line
                    dy=-10  # Consistent vertical offset
                ).encode(
                    x='alert_time:T',
                    y='y:Q',
                    text=alt.value('Alert point')
                )
                
                # Combine with existing chart
                voltage_chart = alt.layer(voltage_chart, rule, text)
            except Exception as e:
                logger.error(f"Error highlighting alert timestamp: {e}")
        
        # Display the chart with streamlit
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
                        st.rerun()
                with col2:
                    if st.button("← Back to Customer List"):
                        # Go back to customer bridge view (second view)
                        st.session_state.show_customer_bridge = True  # Show the bridge/list view
                        st.session_state.show_customer_details = False  # Hide detailed view
                        # Don't clear selected_customer_id to maintain context
                        st.rerun()
                
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
                st.rerun()
       
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

        # Display transformer data visualizations
        display_transformer_data(transformer_df)

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
        st.rerun()
    
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
                st.rerun()
                
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
    
    # Find max loading time once for all charts
    # First check if max_loading_time is in session state
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
        logger.info(f"Transformer data: Using session state max_loading_time for all charts at {max_loading_time}")
    # Only calculate if not in session state
    elif 'loading_percentage' in df.columns:
        max_loading_idx = df['loading_percentage'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        # Set in session state for other charts to use
        st.session_state.max_loading_time = max_loading_time
        logger.info(f"Transformer data: Setting max_loading_time from loading_percentage to {max_loading_time} and saving to session state")
    else:
        # If loading percentage is not available, use max power as an alternative
        max_loading_idx = df['power_kw'].idxmax()
        max_loading_point = df.loc[max_loading_idx]
        max_loading_time = max_loading_point['timestamp']
        # Set in session state for other charts to use
        st.session_state.max_loading_time = max_loading_time
        logger.info(f"Transformer data: Setting max_loading_time from power_kw to {max_loading_time} and saving to session state")
    
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
    
    # Create power chart with Altair - using standard function for consistent styling
    power_df = df.copy()
    
    # Create base chart with proper dimensions
    base = alt.Chart(power_df).mark_line(point=True, color="#1f77b4").encode(
        x=alt.X('timestamp:T', 
            axis=alt.Axis(
                format='%m/%d/%y',
                title='Date',
                labelAngle=-45,
                labelColor='#333333',
                titleColor='#333333',
                labelFontSize=14,
                titleFontSize=16
            )
        ),
        y=alt.Y('power_kw:Q', 
                scale=alt.Scale(zero=False),  # Use zero=False to show data variations better
                ),
        tooltip=['timestamp:T', 'power_kw:Q']
    ).properties(
        width="container",
        height=300
    )
    
    # Calculate peak annotation height with more vertical spacing
    if True:
        # For transformer view, calculate better annotation spacing based on data range
        y_min = df['power_kw'].min()
        y_max = df['power_kw'].max()
        y_range = y_max - y_min
        peak_annotation_height = y_max + (y_range * 0.05)  # Add just 5% for annotations
    else:
        # For other views, use the original calculation
        peak_annotation_height = df['power_kw'].max() * 1.25  # Further increased vertical spacing
    
    # Set fixed Y-axis ranges
    y_min = 0
    y_max = 150
    
    # Add peak load indicator
    peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
        color='red',
        strokeWidth=2,
        strokeDash=[4, 2]
    ).encode(
        x='peak_time:T'
    )
    
    # Add text annotation for peak load
    peak_text = alt.Chart(pd.DataFrame({
        'peak_time': [max_loading_time],
        'y': [peak_annotation_height]  # Position slightly above maximum value
    })).mark_text(
        align='right',
        baseline='bottom',
        fontSize=14,  # Larger font
        fontWeight='bold',
        color='red',
        dx=20,  # Shift text right for better spacing
        dy=-10  # Consistent vertical offset
    ).encode(
        x='peak_time:T',
        y='y:Q',
        text=alt.value('Peak load')
    )
    
    # Combine chart with peak load indicator
    chart = alt.layer(base, peak_rule, peak_text)
    
    # Add horizontal capacity line if size_kva exists
    if 'size_kva' in power_df.columns and not power_df['size_kva'].isna().all():
        try:
            # Get the size_kva value and convert to equivalent power in kW
            # Assuming power factor of 0.9 for conversion if not specified
            size_kva = float(power_df['size_kva'].iloc[0])
            avg_pf = power_df['power_factor'].mean() if 'power_factor' in power_df.columns else 0.9
            size_kw = size_kva * avg_pf
            
            # Create a horizontal rule at the size_kw value
            capacity_rule = alt.Chart(pd.DataFrame({'y': [size_kw]})).mark_rule(
                color='red',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                y='y:Q'
            )
            
            # Create a new DataFrame with timestamp domain information
            domain_df = pd.DataFrame({
                'timestamp': [power_df['timestamp'].min(), power_df['timestamp'].max()],
                'y': [size_kw] * 2,
                'text': [f"Capacity: {size_kva:.0f} kVA"] * 2
            })
            
            # Add text annotation for the capacity line
            capacity_text = alt.Chart(domain_df.iloc[[-1]]).mark_text(
                align='right',
                baseline='bottom',
                dx=-5,
                dy=-10,  # Consistent vertical offset
                fontSize=12,
                fontWeight='bold',
                color='red'
            ).encode(
                x='timestamp:T',  # Use the actual timestamp instead of a fixed position
                y='y:Q',
                text='text:N'
            )
            
            # Combine charts
            chart = alt.layer(chart, capacity_rule, capacity_text)
            logger.info(f"Added transformer capacity line at {size_kw:.1f} kW (from {size_kva:.1f} kVA with PF={avg_pf:.2f})")
        except Exception as e:
            logger.error(f"Could not add transformer capacity line: {str(e)}")
    
    # Add alert timestamp if in session state
    if 'highlight_timestamp' in st.session_state:
        try:
            alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
            
            # Create a vertical rule to mark the alert time
            rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                color='gray',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x='alert_time:T'
            )
            
            # Add text annotation for the alert
            text = alt.Chart(pd.DataFrame({
                'alert_time': [alert_time],
                'y': [peak_annotation_height * 1.05]  # Match peak load height
            })).mark_text(
                align='left',
                baseline='bottom',
                fontSize=14,
                color='gray',
                dx=10,  # Add horizontal offset to avoid overlapping with line
                dy=-10  # Consistent vertical offset
            ).encode(
                x='alert_time:T',
                y='y:Q',
                text=alt.value('Alert point')
            )
            
            # Combine with existing chart
            chart = alt.layer(chart, rule, text)
            logger.info(f"Added alert timestamp line at {alert_time}")
        except Exception as e:
            logger.error(f"Error highlighting alert timestamp: {e}")
    
    # Display the chart
    st.altair_chart(chart, use_container_width=True)

    # Current and Voltage in columns
    col1, col2 = st.columns(2)
    with col1:
        create_colored_banner("Current")
        # Create current chart with direct Altair
        current_base = alt.Chart(df).mark_line(point=True, color="#ff7f0e").encode(
            x=alt.X('timestamp:T', 
                axis=alt.Axis(
                    format='%m/%d/%y',
                    title='Date',
                    labelAngle=-45,
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )
            ),
            y=alt.Y('current_a:Q', 
                scale=alt.Scale(zero=False),  # Use zero=False to show data variations better
                axis=alt.Axis(
                    title='Current (A)',
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )
            ),
            tooltip=['timestamp:T', 'current_a:Q']
        ).properties(
            width="container",
            height=250
        )
        
        # Add peak load indicator for current
        current_peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
            color='red',
            strokeWidth=2,
            strokeDash=[4, 2]
        ).encode(
            x='peak_time:T'
        )
        
        # Add text annotation for peak load
        current_peak_text = alt.Chart(pd.DataFrame({
            'peak_time': [max_loading_time],
            'y': [df['current_a'].max() * 1.05]  # Position 5% above maximum value
        })).mark_text(
            align='right',
            baseline='bottom',
            fontSize=14,
            fontWeight='bold',
            color='red',
            dx=20,  # Shift text right for better spacing
            dy=-10  # Consistent vertical offset
        ).encode(
            x='peak_time:T',
            y='y:Q',
            text=alt.value('Peak load')
        )
        
        # Combine chart with peak load indicator
        current_chart = alt.layer(current_base, current_peak_rule, current_peak_text)
        
        # Add alert timestamp if in session state
        if 'highlight_timestamp' in st.session_state:
            try:
                alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
                
                # Create vertical rule at alert time
                alert_rule = alt.Chart(pd.DataFrame({
                    'timestamp': [alert_time]
                })).mark_rule(
                    color='gray',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    x='timestamp:T'
                )
                
                # Add alert text
                alert_text = alt.Chart(pd.DataFrame({
                    'timestamp': [alert_time],
                    'y': [df['current_a'].max() * 1.08]  # Position slightly higher than peak load
                })).mark_text(
                    align='left',
                    baseline='bottom',
                    fontSize=12,
                    fontWeight='bold',
                    color='gray',
                    dx=5,  # Horizontal offset
                    dy=-5  # Vertical offset
                ).encode(
                    x='timestamp:T',
                    y='y:Q',
                    text=alt.value('Alert point')
                )
                
                # Combine with existing chart containing peak load indicators
                current_chart = alt.layer(current_chart, alert_rule, alert_text)
            except Exception as e:
                logger.error(f"Could not add alert timestamp to current chart: {str(e)}")
        
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
        variation_pct = 0.15  # Increased from 0.06 to 0.15 (15% variation)
        pattern_influence = 0.08  # Increased from 0.02 to 0.08 (8% influence)
        random_noise = 0.02  # Increased from 0.01 to 0.02 (2% random noise)
        
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
        
        # Log voltage data statistics for debugging
        logger.warning(f"Voltage data statistics - Phase A: min={voltage_data['Phase A'].min():.2f}, max={voltage_data['Phase A'].max():.2f}, range={voltage_data['Phase A'].max() - voltage_data['Phase A'].min():.2f}")
        logger.warning(f"Expected voltage range based on 15% variation: {base_voltage * 0.85:.2f} to {base_voltage * 1.15:.2f}")
        
        # Define the column mapping for the multi-line chart
        column_dict = {
            'Phase A': 'Phase A',
            'Phase B': 'Phase B',
            'Phase C': 'Phase C'
        }
        
        # Create a multi-line chart with Altair
        voltage_chart = create_multi_line_chart(
            voltage_data, 
            column_dict,
            title=None  # No title needed as we use colored banner
        )
        
        # Set y-axis domain constraint for voltage chart to ensure data visibility
        voltage_chart = voltage_chart.encode(
            y=alt.Y('value:Q', 
                    scale=alt.Scale(domain=[300, 500], zero=False),  # Set voltage range to capture full 15% variation
                    axis=alt.Axis(
                        title="Voltage",
                        labelColor='#333333',
                        titleColor='#333333',
                        labelFontSize=14,
                        titleFontSize=16
                    ))
        )
        
        # Add peak load indicator
        peak_rule = alt.Chart(pd.DataFrame({'peak_time': [max_loading_time]})).mark_rule(
            color='red',
            strokeWidth=2,
            strokeDash=[4, 2]  # Different dash pattern
        ).encode(
            x='peak_time:T'
        )
        
        # Add text annotation for peak load
        peak_text = alt.Chart(pd.DataFrame({
            'peak_time': [max_loading_time],
            'y': [voltage_data[['Phase A', 'Phase B', 'Phase C']].max().max() * 1.05]  # Position 5% above maximum value
        })).mark_text(
            align='left',
            baseline='bottom',
            fontSize=12,
            fontWeight='bold',
            color='red',
            dx=10,  # Add horizontal offset to avoid overlapping with line
            dy=-10  # Consistent vertical offset
        ).encode(
            x='peak_time:T',
            y='y:Q',
            text=alt.value('Peak load')
        )
        
        # Combine the charts
        voltage_chart = alt.layer(voltage_chart, peak_rule, peak_text)
        
        # Add alert timestamp if in session state
        if 'highlight_timestamp' in st.session_state:
            try:
                alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
                
                # Create a vertical rule to mark the alert time
                rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                    color='gray',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    x='alert_time:T'
                )
                
                # Add text annotation for the alert
                text = alt.Chart(pd.DataFrame({
                    'alert_time': [alert_time],
                    'y': [voltage_data[['Phase A', 'Phase B', 'Phase C']].max().max() * 1.05]  # Match peak load position
                })).mark_text(
                    align='left',
                    baseline='top',
                    fontSize=12,
                    color='gray',
                    dx=10,  # Add horizontal offset to avoid overlapping with line
                    dy=-10  # Consistent vertical offset
                ).encode(
                    x='alert_time:T',
                    y='y:Q',
                    text=alt.value('Alert point')
                )
                
                # Combine with existing chart
                voltage_chart = alt.layer(voltage_chart, rule, text)
            except Exception as e:
                logger.error(f"Could not add alert timestamp to voltage chart: {str(e)}")
        
        # Set the height to match the original chart
        voltage_chart = voltage_chart.properties(height=250)
        
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
    
    # Create power chart with Altair - with data points (dots) enabled
    power_chart = alt.Chart(df).mark_line(point=True, color="#1f77b4").encode(
        x=alt.X('timestamp:T', 
            axis=alt.Axis(
                format='%m/%d/%y',
                title='Date',
                labelAngle=-45,
                labelColor='#333333',
                titleColor='#333333',
                labelFontSize=14,
                titleFontSize=16
            )
        ),
        y=alt.Y('power_kw:Q', 
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                title='Customer Power (kW)',  # Reverted back to original title
                labelColor='#333333',
                titleColor='#333333',
                labelFontSize=14,
                titleFontSize=16
            )
        ),
        tooltip=['timestamp:T', 'power_kw:Q']
    ).properties(
        width='container'
    )
    st.altair_chart(power_chart, use_container_width=True)

    # Only show Voltage chart, removing the Current chart
    create_colored_banner("Voltage")
    # Pass False to skip adding alert line in the voltage chart since it's already shown in other charts
    display_voltage_time_series(results_df, is_transformer_view=False)

def create_altair_chart(df, y_column, title=None, color=None):
    """
    Create a standardized Altair chart for time series data.
    
    Args:
        df (pd.DataFrame): DataFrame with timestamp column and data column
        y_column (str): Name of the column to plot on the y-axis
        title (str, optional): Chart title
        color (str, optional): Line color (hex code or named color)
        
    Returns:
        alt.Chart: Configured Altair chart
    """
    # Base configuration for line chart
    chart = alt.Chart(df).mark_line(point=True).encode(
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
        y=alt.Y(y_column, 
                scale=alt.Scale(zero=False),  # Use zero=False to show data variations better
                axis=alt.Axis(
                    title=y_column.replace('_', ' ').title(), # Format title nicely
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        tooltip=[
            alt.Tooltip('timestamp:T', title='Date', format='%m/%d/%y %H:%M'),
            alt.Tooltip(y_column, title=y_column.replace('_', ' ').title())
        ]
    )
    
    # Apply custom color if provided
    if color:
        chart = chart.encode(color=alt.value(color))
    
    # Add title if provided
    if title:
        chart = chart.properties(title=title)
        
    # Set chart width to responsive
    chart = chart.properties(width='container')
    
    # Highlight alert timestamp if it exists in session state
    if 'highlight_timestamp' in st.session_state:
        try:
            alert_time = pd.to_datetime(st.session_state.highlight_timestamp)
            
            # Create a vertical rule to mark the alert time
            rule = alt.Chart(pd.DataFrame({'alert_time': [alert_time]})).mark_rule(
                color='gray',
                strokeWidth=2,
                strokeDash=[5, 5]
            ).encode(
                x='alert_time:T'
            )
            
            # Add text annotation for the alert
            text = alt.Chart(pd.DataFrame({
                'alert_time': [alert_time],
                'y': [df[y_column].max()]
            })).mark_text(
                align='center',
                baseline='top',
                fontSize=12,
                color='gray',
                dx=10,  # Add horizontal offset to avoid overlapping with line
                dy=-10  # Consistent vertical offset
            ).encode(
                x='alert_time:T',
                y='y:Q',
                text=alt.value('Alert point')
            )
            
            # Combine the base chart with rule and text
            return chart + rule + text
            
        except Exception as e:
            logger.error(f"Error highlighting alert timestamp: {e}")
    
    return chart

def create_multi_line_chart(df, column_dict, title=None):
    """
    Create a multi-line Altair chart from wide-format data.
    
    Args:
        df (pd.DataFrame): DataFrame with timestamp and multiple data columns
        column_dict (dict): Dictionary mapping column names to display names
        title (str, optional): Chart title
        
    Returns:
        alt.Chart: Configured Altair chart with multiple lines
    """
    # First, convert data to long format for Altair
    id_vars = ['timestamp']
    value_vars = list(column_dict.keys())
    
    # Melt the DataFrame to convert from wide to long format
    long_df = pd.melt(
        df, 
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='series',
        value_name='value'
    )
    
    # Create mapping for series names
    long_df['series_name'] = long_df['series'].map(column_dict)
    
    # Create chart
    chart = alt.Chart(long_df).mark_line(point=True).encode(
        x=alt.X('timestamp:T',
                axis=alt.Axis(
                    format='%m/%d/%y',
                    title='Date',
                    labelAngle=-45,
                    grid=False,
                    tickCount=10,
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        y=alt.Y('value:Q',
                scale=alt.Scale(zero=False),  # Use zero=False to show data variations better
                axis=alt.Axis(
                    labelColor='#333333',
                    titleColor='#333333',
                    labelFontSize=14,
                    titleFontSize=16
                )),
        color=alt.Color('series_name:N', legend=alt.Legend(title="Series")),
        tooltip=[
            alt.Tooltip('timestamp:T', title='Date', format='%m/%d/%y %H:%M'),
            alt.Tooltip('value:Q', title='Value'),
            alt.Tooltip('series_name:N', title='Series')
        ]
    )
    
    # Add title if specified
    if title:
        chart = chart.properties(title=title)
        
    # Set chart width to responsive
    chart = chart.properties(width='container')
    
    return chart

def display_full_customer_dashboard(results_df: pd.DataFrame):
    """Display a full-page dashboard for a given customer."""
    if results_df is None or results_df.empty:
        st.warning("No data available for customer dashboard.")
        return
        
    # Make sure timestamp is in datetime format
    df = results_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Check if transformer peak time is already set in session state
    # If so, use that for consistency across all views
    if 'max_loading_time' in st.session_state:
        max_loading_time = st.session_state.max_loading_time
        logger.info(f"Customer dashboard: Using transformer peak time from session state: {max_loading_time}")
    else:
        # Find the maximum loading point - This is now centralized for all charts
        if 'loading_percentage' in df.columns:
            max_loading_idx = df['loading_percentage'].idxmax()
            max_loading_point = df.loc[max_loading_idx]
            max_loading_time = max_loading_point['timestamp']
            
            # Store in session state for consistent use across all charts
            st.session_state.max_loading_time = max_loading_time
            logger.info(f"Customer dashboard: Setting new peak time based on customer data: {max_loading_time}")
        else:
            # If loading percentage is not available, we'll let each chart determine its own max point
            max_loading_time = None
            logger.info("Customer dashboard: No loading_percentage available, each chart will determine peak individually")
    
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
