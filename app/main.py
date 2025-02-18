"""
Main application file for the Transformer Loading Analysis Application
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import warnings
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import logging
from services.data_service import (
    get_transformer_ids_for_feeder,
    get_analysis_results,
    get_available_dates,
    get_transformer_options,
    get_customer_data,
    get_transformer_attributes
)
from services.alert_service import process_alerts, test_alert_system
from utils.logging_utils import Timer, logger, log_performance
from visualization.charts import (
    display_loading_status_line_chart,
    display_power_time_series,
    display_current_time_series,
    display_voltage_over_time as charts_voltage_display
)
from visualization.tables import (
    display_transformer_raw_data,
    display_customer_data,
    display_transformer_attributes
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure the application
st.set_page_config(
    page_title="Transformer Loading Analysis",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Force light theme
st._config.set_option('theme.base', 'light')
st._config.set_option('theme.backgroundColor', '#ffffff')
st._config.set_option('theme.secondaryBackgroundColor', '#f8f9fa')
st._config.set_option('theme.textColor', '#2f4f4f')
st._config.set_option('theme.font', 'sans serif')

# Additional CSS for light theme
st.markdown("""
    <style>
        /* Global theme override */
        :root, .stApp, [data-testid="stAppViewContainer"] {
            background-color: white !important;
            color: #2f4f4f !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
            border-right: 1px solid #e9ecef !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #2f4f4f !important;
        }
        
        /* Buttons */
        .stButton button {
            background-color: #f0f2f6 !important;
            color: #2f4f4f !important;
            border: 1px solid #d1d5db !important;
        }
        
        /* Inputs */
        .stTextInput input, .stNumberInput input, .stDateInput input {
            background-color: white !important;
            color: #2f4f4f !important;
        }
        
        /* Remove dark mode elements */
        [data-testid="stToolbar"], [data-testid="stDecoration"], footer {
            display: none !important;
        }
        
        /* Improve sidebar dropdown styling */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child {
            background-color: white !important;
            border: 1px solid #cfd7df !important;
            border-radius: 4px !important;
            transition: border-color 0.15s ease-in-out !important;
        }
        
        /* Hover state for dropdowns */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child:hover {
            border-color: #a3aeb8 !important;
        }
        
        /* Focus state for dropdowns */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div:first-child:focus-within {
            border-color: #0d6efd !important;
            box-shadow: 0 0 0 1px #0d6efd !important;
        }
        
        /* Dropdown option container */
        [data-testid="stSidebar"] div[role="listbox"] {
            border: 1px solid #cfd7df !important;
            border-radius: 4px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        }
        
        /* Dropdown options */
        [data-testid="stSidebar"] div[role="option"] {
            padding: 8px 12px !important;
        }
        
        /* Selected option */
        [data-testid="stSidebar"] div[aria-selected="true"] {
            background-color: #e9ecef !important;
        }
        
        /* Date input styling */
        [data-testid="stSidebar"] .stDateInput > div[data-baseweb="input"] {
            background-color: white !important;
            border: 1px solid #cfd7df !important;
            border-radius: 4px !important;
            transition: border-color 0.15s ease-in-out !important;
        }
        
        /* Date input hover */
        [data-testid="stSidebar"] .stDateInput > div[data-baseweb="input"]:hover {
            border-color: #a3aeb8 !important;
        }
        
        /* Date input focus */
        [data-testid="stSidebar"] .stDateInput > div[data-baseweb="input"]:focus-within {
            border-color: #0d6efd !important;
            box-shadow: 0 0 0 1px #0d6efd !important;
        }
        
        /* Date input calendar icon */
        [data-testid="stSidebar"] .stDateInput div[role="button"] {
            padding: 0.375rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for database connection
if 'db_con' not in st.session_state:
    from core.database import get_database_connection
    with Timer("Database Connection"):
        st.session_state.db_con = get_database_connection()

# Disable discovery cache warning
warnings.filterwarnings('ignore', message='file_cache is unavailable when using oauth2client >= 4.0.0')

DEFAULT_RECIPIENT = "jhnapo2213@gmail.com"

def create_tile(title, value, has_multiline_title=False, is_clickable=False):
    """Create a styled tile using Streamlit components."""
    if is_clickable:
        col = st.container()
        with col:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    padding: 20px;
                    text-align: center;
                    margin: 5px;
                    height: 110px;
                    display: flex;
                    flex-direction: column;
                    background-color: #f8f9fa;
                    cursor: pointer;
                ">
                    <div style="
                        padding-bottom: 10px;
                        min-height: 35px;
                        display: flex;
                        align-items: flex-start;
                        justify-content: center;
                        padding-left: 0;
                    ">
                        <h3 style="
                            margin: 0;
                            padding: 0;
                            font-size: 0.8em;
                            color: #6B7280;
                            font-weight: normal;
                            line-height: 1.2;
                        ">{title}</h3>
                    </div>
                    <div style="
                        padding-top: 10px;
                        text-align: center;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    ">
                        <h1 style="
                            margin: 0;
                            padding: 0;
                            color: #0078d4;
                            font-size: 1.5em;
                            font-weight: 500;
                            line-height: 1;
                        ">{value}</h1>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Add invisible button over the tile
            st.markdown("""
                <style>
                [data-testid="stButton"] {
                    position: absolute;
                    margin-top: -120px;
                    width: calc(25% - 1rem);
                }
                [data-testid="stButton"] > button {
                    width: 100%;
                    height: 110px;
                    opacity: 0;
                    cursor: pointer;
                }
                </style>
            """, unsafe_allow_html=True)
            clicked = st.button("Click", key="customers_button")
            if clicked:
                st.query_params["tab"] = "customer"
                st.rerun()
            return clicked
    else:
        st.markdown(
            f"""
            <div style="
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 20px;
                text-align: center;
                margin: 5px;
                height: 110px;
                display: flex;
                flex-direction: column;
                background-color: #f8f9fa;
            ">
                <div style="
                    padding-bottom: {8 if has_multiline_title else 10}px;
                    min-height: {45 if has_multiline_title else 35}px;
                    display: flex;
                    align-items: flex-start;
                    justify-content: center;
                    padding-left: 0;
                ">
                    <h3 style="
                        margin: 0;
                        padding: 0;
                        font-size: 0.8em;
                        color: #6B7280;
                        font-weight: normal;
                        line-height: 1.2;
                    ">{title}</h3>
                </div>
                <div style="
                    padding-top: {8 if has_multiline_title else 10}px;
                    text-align: center;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                ">
                    <h1 style="
                        margin: 0;
                        padding: 0;
                        color: #0078d4;
                        font-size: 1.5em;
                        font-weight: 500;
                        line-height: 1;
                    ">{value}</h1>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def create_banner(title):
    """Create a banner with professional styling."""
    st.markdown(
        f'''
        <div style="
            padding: 8px 15px;
            margin: 0 0 15px 0;
            background-color: #f8f9fa;
            text-align: left;
            position: relative;
            width: 100%;
            box-sizing: border-box;
            border: 1px solid #cfd7df;
            border-radius: 4px;
        ">
            <h2 style="
                margin: 0;
                font-size: 1.1em;
                color: #374151;
                font-weight: 500;
            ">{title}</h2>
        </div>
        ''',
        unsafe_allow_html=True
    )

def create_section_banner(title):
    """Create a section banner with professional styling."""
    st.markdown(
        f'''
        <div style="
            padding: 5px 15px;
            margin: 10px 0;
            background-color: #f8f9fa;
            border-left: 5px solid #0078d4;
            border-radius: 0;
        ">
            <h3 style="
                margin: 0;
                font-size: 1.1em;
                color: #374151;
                font-weight: 500;
            ">{title}</h3>
        </div>
        ''',
        unsafe_allow_html=True
    )

def process_data(df):
    """Process the data for visualization"""
    if df is None or df.empty:
        return None

    try:
        logger.info("Starting data processing")
        
        # Log initial state
        logger.info(f"Initial columns: {df.columns.tolist()}")
        if 'size_kva' in df.columns:
            logger.info(f"Initial size_kva: {df['size_kva'].iloc[0]}")
        
        # Add mock data for missing fields
        if 'num_customers' not in df.columns:
            df['num_customers'] = 15  # Mock value
        if 'x_coordinate' not in df.columns:
            df['x_coordinate'] = 43.5123  # Mock value
        if 'y_coordinate' not in df.columns:
            df['y_coordinate'] = -79.3802  # Mock value
        
        # Add mock voltage data for three phases if not present
        for phase in ['a', 'b', 'c']:
            if f'voltage_{phase}_v' not in df.columns:
                # Generate slightly different mock voltage data for each phase
                base_voltage = 240 + np.random.normal(0, 0.5, len(df))
                offset = np.random.uniform(-1, 1)
                df[f'voltage_{phase}_v'] = base_voltage + offset

        # Calculate loading percentage
        if 'loading_percentage' not in df.columns:
            if 'size_kva' in df.columns:
                logger.info(f"Calculating loading percentage with size_kva: {df['size_kva'].iloc[0]}")
                df['loading_percentage'] = (df['power_kw'] / df['size_kva']) * 100
            else:
                logger.warning("Cannot calculate loading percentage - size_kva not found")
        
        # Add hour column for easier filtering
        df['hour'] = df['timestamp'].dt.hour
        
        # Log final state
        logger.info(f"Final columns: {df.columns.tolist()}")
        if 'size_kva' in df.columns:
            logger.info(f"Final size_kva: {df['size_kva'].iloc[0]}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}", exc_info=True)
        return None

import plotly.graph_objects as go

def display_power_time_series(df, selected_hour, is_transformer_view=False):
    """Display power consumption over time"""
    if df is None or df.empty:
        st.warning("No data available for power visualization")
        return
        
    fig = go.Figure()
    
    # Add power consumption trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['power_kw'],
        mode='lines',
        name='Power (kW)',
        line=dict(color='#1f77b4', width=1.5)
    ))

    # Add vertical line for selected hour
    if selected_hour is not None:
        # Find data for selected hour
        hour_data = df[df['timestamp'].dt.hour == selected_hour]
        if not hour_data.empty:
            # Add vertical line shape
            fig.add_shape(
                type="line",
                x0=hour_data['timestamp'].iloc[0],
                x1=hour_data['timestamp'].iloc[0],
                y0=0,
                y1=1,
                yref="paper",
                line=dict(
                    color="gray",
                    width=1,
                    dash="dash",
                )
            )
            
            # Add annotation separately
            fig.add_annotation(
                x=hour_data['timestamp'].iloc[0],
                y=1,
                yref="paper",
                text=f"Selected Hour: {selected_hour:02d}:00",
                textangle=-90,
                showarrow=False,
                xshift=10,
                yshift=0
            )

    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickformat='%H:%M'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            zeroline=False
        ),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

def display_current_time_series(df):
    """Display current over time"""
    if df is None or df.empty:
        st.warning("No data available for current visualization")
        return

    fig = go.Figure()
    
    # Add single current trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['current_a'],
        mode='lines',
        name='Current (A)',
        line=dict(color='#d62728', width=1.5)
    ))

    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=300,
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickformat='%H:%M'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            zeroline=False
        ),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

@log_performance
def main():
    """Main application function"""
    # Add custom CSS for layout fixes
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                margin-top: -2rem;
            }
            [data-testid="stSidebarNav"] {
                padding-top: 0rem;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
                padding-top: 0rem;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: #f8f9fa;
                border-radius: 4px;
                gap: 1px;
                padding: 0px 10px;
            }
            section[data-testid="stSidebarContent"] > div {
                padding-top: 1rem;
            }
            section[data-testid="stSidebarContent"] {
                padding-top: 0rem;
            }
            div[data-testid="stToolbar"] {
                visibility: hidden;
            }
            #MainMenu {
                visibility: hidden;
            }
            header {
                visibility: hidden;
            }
            </style>
    """, unsafe_allow_html=True)

    create_banner("Transformer Loading Analysis")

    # Get URL parameters
    params = st.query_params
    view_mode = params.get("view", "minimal")
    param_transformer = params.get("transformer")
    param_feeder = params.get("feeder")
    param_date = params.get("date")
    param_hour = params.get("hour")
    
    logger.info(f"View mode: {view_mode}")
    logger.info(f"URL parameters: {dict(params)}")
    
    # Initialize session state
    if 'selected_hour' not in st.session_state:
        st.session_state.selected_hour = int(param_hour) if param_hour else 0

    # Get available dates
    with Timer("Date Range"):
        start_date, end_date = get_available_dates()

    # Add top spacing for minimal view
    if view_mode == "minimal":
        st.markdown('<div style="height: 2rem"></div>', unsafe_allow_html=True)

    # Sidebar for search controls
    with st.sidebar:
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    background-color: #f8f9fa;
                    padding: 1rem;
                }
                section[data-testid="stSidebarNav"] {
                    padding-top: 0;
                }
                .block-container {
                    padding-top: 0;
                }
                .stTabs [data-baseweb="tab-list"] {
                    gap: 2px;
                }
                .stTabs [data-baseweb="tab"] {
                    height: 50px;
                    white-space: pre-wrap;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    gap: 1px;
                    padding: 0 10px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Search Controls")

        # Date selection
        selected_from_date = st.date_input(
            "From Date",
            value=datetime.strptime(param_date, "%Y-%m-%d").date() if param_date else end_date,
            min_value=start_date,
            max_value=end_date
        )

        # Add To Date for UI presentation
        st.date_input(
            "To Date",
            value=selected_from_date,
            min_value=start_date,
            max_value=end_date,
            disabled=True
        )

        # Hour selection
        selected_hour = st.time_input(
            "Time",
            value=datetime.strptime(f"{st.session_state.selected_hour}:00", "%H:%M").time(),
            help="Select hour for vertical line indicator"
        )
        st.session_state.selected_hour = selected_hour.hour

        # Feeder selection
        feeder_options = ["Feeder 1", "Feeder 2", "Feeder 3", "Feeder 4"]
        selected_feeder = st.selectbox(
            "Feeder",
            options=feeder_options,
            index=feeder_options.index(param_feeder) if param_feeder in feeder_options else 0
        )

        # Transformer selection
        transformer_options = get_transformer_options()
        if transformer_options:
            selected_transformer = st.selectbox(
                "Transformer",
                options=transformer_options,
                index=transformer_options.index(param_transformer) if param_transformer in transformer_options else 0
            )
        else:
            st.error("No transformers found")
            return

        # Get results first
        results_df = get_analysis_results(
            selected_transformer,
            selected_from_date
        ) if selected_transformer else None
        
        # Buttons
        col1, col2 = st.columns(2)
        with col1:
            reset_clicked = st.button("Reset", use_container_width=True)
        with col2:
            search_clicked = st.button("Search", type="primary", use_container_width=True)

        if reset_clicked:
            st.session_state.selected_hour = 0
            st.rerun()
            
        if search_clicked and results_df is not None:
            logger.info("Search button clicked")
            try:
                # Process alerts - this will send email with dashboard link
                process_alerts(results_df, selected_from_date, selected_hour.hour)
                st.success("Alert email sent successfully! Check your email for the dashboard link.")
            except Exception as e:
                st.error(f"Error processing alert: {str(e)}")

    # Full view mode handling
    if view_mode == "full":
        # Process data for visualization
        if results_df is not None:
            logger.info(f"Before process_data - Columns: {results_df.columns.tolist()}")
            if 'size_kva' in results_df.columns:
                logger.info(f"Before process_data - size_kva value: {results_df['size_kva'].iloc[0]}")
            else:
                logger.warning("Before process_data - size_kva column not found")
            
            results_df = process_data(results_df)
            logger.info(f"After process_data - Columns: {results_df.columns.tolist()}")
            if 'size_kva' in results_df.columns:
                logger.info(f"After process_data - size_kva value: {results_df['size_kva'].iloc[0]}")
                
                # Add transformer view flag to results_df after processing
                results_df.attrs['is_transformer_view'] = True
                logger.info("Set transformer view flag in DataFrame attributes")
            else:
                logger.warning("After process_data - size_kva column not found")
        
        # Create tabs
        tab1, tab2 = st.tabs(["Transformer", "Customer"])
        
        # Transformer tab content
        with tab1:
            if results_df is not None and not results_df.empty:
                # Display transformer details at the top with proper spacing
                st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
                create_section_banner("Transformer Details")
                st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
                
                # Get transformer attributes
                transformer_attrs = get_transformer_attributes(selected_transformer)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    create_tile(
                        "Transformer ID",
                        selected_transformer,
                        has_multiline_title=False
                    )
                with col2:
                    num_customers = transformer_attrs['number_of_customers'].iloc[0] if not transformer_attrs.empty else 0
                    create_tile(
                        "Customers",
                        str(num_customers),
                        has_multiline_title=False,
                        is_clickable=True
                    )
                with col3:
                    create_tile(
                        "X Coordinate",
                        "43.5123",
                        has_multiline_title=False
                    )
                with col4:
                    create_tile(
                        "Y Coordinate",
                        "-79.3802",
                        has_multiline_title=False
                    )

                st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
                
                # Power consumption chart - full width
                create_section_banner("Power Consumption Over Time")
                logger.info("Calling display_power_time_series with transformer view")
                logger.info(f"Results DataFrame columns: {results_df.columns.tolist()}")
                if 'size_kva' in results_df.columns:
                    logger.info(f"size_kva value before visualization: {results_df['size_kva'].iloc[0]}")
                display_power_time_series(results_df, st.session_state.selected_hour, is_transformer_view=True)

                st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

                # Current and Voltage charts side by side
                col1, col2 = st.columns(2)
                with col1:
                    create_section_banner("Current Over Time")
                    display_current_time_series(results_df)
                with col2:
                    create_section_banner("Voltage Over Time")
                    charts_voltage_display(results_df)

        # Customer tab content
        with tab2:
            logger.info("Rendering Customer tab")
            # Create a container for the customer view
            customer_view = st.container()
            
            with customer_view:
                # Top spacing
                st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
                
                # Get customer data
                with Timer("Customer Data Retrieval"):
                    logger.info(f"Fetching customer data for transformer {selected_transformer} on {selected_from_date}")
                    customer_df = get_customer_data(selected_transformer, selected_from_date) if selected_transformer else pd.DataFrame()
                
                # Customer Details section
                logger.info("Rendering Customer Details section")
                create_section_banner("Customer Details")
                st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
                
                # Summary tiles in columns
                logger.info("Creating summary tiles")
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate metrics with error handling
                try:
                    total_customers = len(customer_df['customer_id'].unique()) if not customer_df.empty else 0
                    avg_power = customer_df['power_kw'].mean() if not customer_df.empty else 0
                    peak_power = customer_df['power_kw'].max() if not customer_df.empty else 0
                    avg_pf = customer_df['power_factor'].mean() if not customer_df.empty else 0
                    
                    logger.info(f"Calculated metrics - Total Customers: {total_customers}, "
                              f"Avg Power: {avg_power:.1f}kW, Peak Power: {peak_power:.1f}kW, "
                              f"Avg PF: {avg_pf:.2f}")
                except Exception as e:
                    logger.error(f"Error calculating metrics: {str(e)}")
                    total_customers, avg_power, peak_power, avg_pf = 0, 0, 0, 0
                
                with col1:
                    create_tile(
                        "Total Customers",
                        str(total_customers),
                        has_multiline_title=False
                    )
                with col2:
                    create_tile(
                        "Average Power",
                        f"{avg_power:.1f} kW",
                        has_multiline_title=False
                    )
                with col3:
                    create_tile(
                        "Peak Power",
                        f"{peak_power:.1f} kW",
                        has_multiline_title=False
                    )
                with col4:
                    create_tile(
                        "Power Factor",
                        f"{avg_pf:.2f}",
                        has_multiline_title=False
                    )

                # Spacing between sections
                st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
                
                # Customer selection dropdown
                if not customer_df.empty:
                    customer_ids = sorted(customer_df['customer_id'].unique())
                    selected_customer = st.selectbox(
                        "Select Customer",
                        customer_ids,
                        format_func=lambda x: f"Customer {x}"
                    )
                    
                    # Filter data for selected customer
                    customer_data = customer_df[customer_df['customer_id'] == selected_customer].copy()
                    
                    # Power consumption chart - full width
                    create_section_banner("Power Consumption Over Time")
                    display_power_time_series(customer_data, st.session_state.selected_hour, is_transformer_view=False)

                    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

                    # Current and Voltage charts side by side
                    col1, col2 = st.columns(2)
                    with col1:
                        create_section_banner("Current Over Time")
                        display_current_time_series(customer_data)
                    with col2:
                        create_section_banner("Voltage Over Time")
                        charts_voltage_display(customer_data)

                # Customer Data section
                logger.info("Rendering Customer Data section")
                create_section_banner("Customer Data")
                
                if customer_df.empty:
                    logger.warning("No customer data available to display")
                    st.info("No customer data available. Please select a transformer and date range to view customer data.")
                else:
                    logger.info("Formatting customer data for display")
                    try:
                        # Format timestamp for display
                        display_df = customer_df.copy()
                        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                        
                        # Round numeric columns
                        numeric_cols = ['power_kw', 'current_a', 'power_factor']
                        display_df[numeric_cols] = display_df[numeric_cols].round(2)
                        
                        logger.info(f"Displaying data table with {len(display_df)} rows")
                        # Display the customer data table
                        st.dataframe(
                            display_df,
                            column_config={
                                "timestamp": "Timestamp",
                                "customer_id": "Customer ID",
                                "power_kw": "Power (kW)",
                                "current_a": "Current (A)",
                                "power_factor": "Power Factor",
                                "x_coordinate": "X Coordinate",
                                "y_coordinate": "Y Coordinate"
                            },
                            hide_index=True
                        )
                    except Exception as e:
                        logger.error(f"Error displaying customer data: {str(e)}", exc_info=True)
                        st.error("Error displaying customer data. Please try again or contact support.")
                
                logger.info("Customer tab rendering complete")
    elif view_mode == "minimal" and search_clicked:
        with st.spinner("Processing your request and sending email..."):
            try:
                if process_alerts(results_df, selected_from_date, st.session_state.selected_hour, [DEFAULT_RECIPIENT]):
                    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
                    st.success("""
                        ✅ Analysis complete! 
                        
                        An email has been sent to {} with the detailed analysis link.
                        Please check your inbox (and spam folder) for the transformer loading analysis.
                        
                        Note: The email may take a few minutes to arrive.
                        """.format(DEFAULT_RECIPIENT))
                else:
                    st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
                    raise Exception("Failed to process alerts")
            except Exception as e:
                st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)
                st.error(f"""
                    ❌ Error sending analysis email
                    
                    Please try again or contact support if the issue persists.
                    Error details: {str(e)}
                    """)

    # Add spacing at the bottom of the page
    st.markdown('<div style="height: 2rem"></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
