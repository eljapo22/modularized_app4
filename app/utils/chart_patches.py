import logging
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from app.visualization.charts import display_power_time_series, display_customer_data, display_transformer_data
from app.visualization.charts import format_chart_dates, normalize_timestamps

# Create a temporary patch for charts.py
def patch_transformer_charts():
    """
    Apply patches to the transformer charts rendering functions.
    This will:
    1. Increase vertical spacing above the power chart
    2. Make alert annotations match peak load annotations in height & style
    3. Update the capacity label to show kVA instead of kW
    """
    # Store the original function
    original_display_power_time_series = display_power_time_series
    
    # Define the patched function
    def patched_display_power_time_series(results_df: pd.DataFrame, is_transformer_view: bool = False):
        """Patched version with improved annotations"""
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
            logging.info(f"Power chart: Using loading_percentage max value for peak placement at {max_loading_time}")
        else:
            # If loading percentage is not available, use max power as an alternative
            max_loading_idx = df['power_kw'].idxmax()
            max_loading_point = df.loc[max_loading_idx]
            max_loading_time = max_loading_point['timestamp']
            logging.info(f"Power chart: Using power_kw max value as fallback for peak placement at {max_loading_time}")
        
        # Use session state max_loading_time if available - ensures consistency across charts
        if 'max_loading_time' in st.session_state:
            max_loading_time = st.session_state.max_loading_time
        
        # Calculate peak annotation height with more vertical spacing
        peak_annotation_height = df['power_kw'].max() * 1.15  # Increased vertical spacing
        
        # Create power chart with Altair
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
            y=alt.Y('power_kw:Q', 
                    scale=alt.Scale(zero=False),
                    axis=alt.Axis(
                        title='Power (kW)',
                        labelColor='#333333',
                        titleColor='#333333',
                        labelFontSize=14,
                        titleFontSize=16
                    )),
            tooltip=['timestamp:T', 'power_kw:Q']
        ).properties(
            title="Power Consumption (kW)" if is_transformer_view else None,
            width='container'
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
        
        # Add horizontal capacity line if size_kva exists
        if is_transformer_view and 'size_kva' in df.columns and not df['size_kva'].isna().all():
            try:
                # Get the size_kva value and convert to equivalent power in kW
                # Assuming power factor of 0.9 for conversion if not specified
                size_kva = float(df['size_kva'].iloc[0])
                avg_pf = df['power_factor'].mean() if 'power_factor' in df.columns else 0.9
                size_kw = size_kva * avg_pf
                
                # Create a horizontal rule at the size_kw value
                capacity_rule = alt.Chart(pd.DataFrame({'y': [size_kw]})).mark_rule(
                    color='red',
                    strokeWidth=2,
                    strokeDash=[5, 5]
                ).encode(
                    y='y:Q'
                )
                
                # Add text annotation for the capacity line
                capacity_text = alt.Chart(pd.DataFrame({
                    'timestamp': [df['timestamp'].max()],
                    'y': [size_kw],
                    'text': [f"Capacity: {size_kva:.1f}kVA"]  # Show kVA instead of kW
                })).mark_text(
                    align='right',
                    baseline='bottom',
                    dx=-5,
                    dy=-10,  # Consistent vertical offset
                    fontSize=12,
                    fontWeight='bold',
                    color='red'
                ).encode(
                    x='timestamp:T',
                    y='y:Q',
                    text='text:N'
                )
                
                # Combine with existing chart
                chart = alt.layer(chart, capacity_rule, capacity_text)
                logging.info(f"Added transformer capacity line at {size_kw:.1f} kW (from {size_kva:.1f} kVA with PF={avg_pf:.2f})")
            except Exception as e:
                logging.error(f"Could not add transformer capacity line: {str(e)}")
        
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
                    'y': [peak_annotation_height]  # Match peak load annotation height
                })).mark_text(
                    align='left',
                    baseline='bottom',
                    fontSize=14,  # Match peak load size
                    fontWeight='bold',
                    color='gray',
                    dy=-10  # Consistent vertical offset
                ).encode(
                    x='alert_time:T',
                    y='y:Q',
                    text=alt.value('Alert point')
                )
                
                # Combine with existing chart
                chart = alt.layer(chart, rule, text)
                logging.info(f"Added alert timestamp line at {alert_time}")
            except Exception as e:
                logging.error(f"Error highlighting alert timestamp: {e}")
        
        # Display the chart with streamlit
        st.altair_chart(chart, use_container_width=True)
    
    # Apply the patch
    import app.visualization.charts
    app.visualization.charts.display_power_time_series = patched_display_power_time_series
    return patched_display_power_time_series
