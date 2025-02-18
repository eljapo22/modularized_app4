"""
Table display components for the Transformer Loading Analysis Application
"""

import streamlit as st
import pandas as pd

def get_table_styles():
    """Get common table styles for pandas DataFrame"""
    return {
        'background-color': 'white',
        'color': '#2f4f4f',
        'font-family': '"Source Sans Pro", sans-serif',
        'text-align': 'left',
        'padding': '8px',
        'font-size': '14px',
        'border': '1px solid #e9ecef',
        'white-space': 'nowrap',
        'overflow': 'hidden',
        'text-overflow': 'ellipsis'
    }

def get_header_styles():
    """Get header styles for pandas DataFrame"""
    return [{
        'selector': 'th',
        'props': [
            ('background-color', '#f8f9fa'),
            ('color', '#2f4f4f'),
            ('font-weight', 'bold'),
            ('text-align', 'left'),
            ('padding', '8px'),
            ('font-size', '14px'),
            ('border', '1px solid #e9ecef'),
            ('white-space', 'nowrap')
        ]
    }]

def display_transformer_raw_data(results):
    """Display transformer raw data in a styled table"""
    if results is None or results.empty:
        st.warning("No transformer data available")
        return
        
    # Format the DataFrame
    display_df = results.copy()
    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Create a styled dataframe
    styled_df = display_df.style.format({
        'loading_percentage': '{:.1f}%',
        'power_kw': '{:.1f}',
        'current_a': '{:.1f}',
        'voltage_v': '{:.1f}',
        'power_factor': '{:.2f}'
    }).set_properties(**get_table_styles()).set_table_styles(get_header_styles())
    
    # Display the table with fixed height
    st.dataframe(
        styled_df,
        height=400,  # Fixed height with scrolling
        hide_index=True,
        use_container_width=True
    )

def display_customer_data(customer_data: pd.DataFrame):
    """Display customer data in a formatted table"""
    if customer_data is None or customer_data.empty:
        st.warning("No customer data available")
        return
        
    # Format the DataFrame
    display_df = customer_data.copy()
    
    # Create a styled dataframe
    styled_df = display_df.style.format({
        'customer_id': '{}',
        'meter_id': '{}',
        'consumption_kwh': '{:.1f}',
        'peak_demand_kw': '{:.1f}',
        'power_factor': '{:.2f}'
    }).set_properties(**get_table_styles()).set_table_styles(get_header_styles())
    
    # Display the table with fixed height
    st.dataframe(
        styled_df,
        height=300,  # Fixed height with scrolling
        hide_index=True,
        use_container_width=True
    )

def display_transformer_attributes(attributes, display_container=st):
    """Display transformer attributes in a styled table"""
    if attributes is None or attributes.empty:
        display_container.warning("No transformer attributes available")
        return
        
    # Format the DataFrame
    display_df = attributes.copy()
    
    # Create a styled dataframe
    styled_df = display_df.style.format({
        'transformer_id': '{}',
        'number_of_customers': '{:,.0f}',
        'total_consumption_kwh': '{:,.1f}',
        'peak_demand_kw': '{:.1f}',
        'average_power_factor': '{:.2f}'
    }).set_properties(**get_table_styles()).set_table_styles(get_header_styles())
    
    # Display the table
    display_container.dataframe(
        styled_df,
        height=200,  # Fixed height with scrolling
        hide_index=True,
        use_container_width=True
    )
