"""
Cloud-specific entry point for the Transformer Loading Analysis Application
Uses app.-prefixed imports required by Streamlit Cloud
"""
import streamlit as st
import logging
import traceback
from datetime import datetime, date, timedelta
import pandas as pd

from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import (
    CloudAlertService, 
    get_alert_status,
    analyze_loading_conditions
)  # Import for alert functionality
from app.utils.ui_utils import create_banner, display_transformer_dashboard
from app.utils.ui_components import create_section_header, create_tile, create_two_column_charts
from app.visualization.charts import display_customer_tab, display_power_time_series, display_current_time_series, display_voltage_time_series, display_loading_status_line_chart

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('transformer_alerts.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize alert state
        if 'alert_state' not in st.session_state:
            st.session_state.alert_state = {
                'pending': False,
                'transformer_id': None,
                'loading': None,
                'timestamp': None
            }
        
        # Initialize view mode in session state
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'simple'  # Default to simple view
            
        # Handle deep link parameters
        params = st.experimental_get_query_params()
        
        # If coming from alert link, pre-populate selections and set full view
        if 'view' in params and params['view'][0] == 'alert':
            transformer_id = params.get('id', [None])[0]
            feeder = params.get('feeder', ['Feeder 1'])[0]
            start_date = datetime.fromisoformat(params.get('start', [None])[0]).date() if 'start' in params else None
            end_date = datetime.fromisoformat(params.get('end', [None])[0]).date() if 'end' in params else None
            auto_search = params.get('auto_search', ['false'])[0].lower() == 'true'
            
            # Store in session state
            if 'selections' not in st.session_state:
                st.session_state.selections = {
                    'transformer_id': transformer_id,
                    'feeder': feeder,
                    'start_date': start_date,
                    'end_date': end_date,
                    'auto_search': auto_search
                }
                st.session_state.search_triggered = False
                st.session_state.view_mode = 'full'  # Switch to full view
        
        # Track session start
        logger.info("=== Starting new analysis session ===")
        
        # Initialize data service
        data_service = CloudDataService()
        logger.info("Services initialized successfully")

        # Get available date range
        min_date, max_date = data_service.get_available_dates()
        logger.info(f"Got date range: {min_date} to {max_date}")
            
        # Set page config
        st.set_page_config(
            page_title="Transformer Loading Analysis",
            page_icon="⚡",
            layout="wide"
        )
        
        create_banner("Transformer Loading Analysis")
        
        # Analysis Parameters in sidebar
        st.sidebar.header("Analysis Parameters")
        
        # Date range selection with default range
        default_start = st.session_state.selections.get('start_date', min_date) if 'selections' in st.session_state else min_date
        default_end = st.session_state.selections.get('end_date', min_date) if 'selections' in st.session_state else min_date
        
        dates = st.sidebar.date_input(
            "Select Date Range",
            value=[default_start, default_end],
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YY"  # Match graph format
        )
        
        # Ensure we have a start and end date
        if isinstance(dates, (datetime, date)):
            start_date = end_date = dates
        else:
            start_date, end_date = dates[0], dates[-1]  # Handle both list and tuple cases
        
        # Feeder and transformer selection
        feeder_options = data_service.get_feeder_options()
        selected_feeder = st.sidebar.selectbox(
            "Select Feeder",
            feeder_options,
            index=feeder_options.index(st.session_state.selections['feeder']) if 'selections' in st.session_state else 0
        )
        
        transformer_options = data_service.get_load_options(selected_feeder)
        selected_transformer = st.sidebar.selectbox(
            "Select Transformer",
            transformer_options,
            index=transformer_options.index(st.session_state.selections['transformer_id']) if 'selections' in st.session_state else 0
        )
        
        # Search button with icon
        search_clicked = st.sidebar.button(
            "🔍 Search" + (" 🔔" if st.session_state.alert_state.get('pending', False) else ""),
            type="primary",
            key="search_button"
        )
        
        # Auto-trigger search if coming from alert link
        if ('selections' in st.session_state and 
            st.session_state.selections.get('auto_search', False) and 
            not st.session_state.get('search_triggered', False)):
            search_clicked = True
            st.session_state.search_triggered = True
        
        logger.info(f"Search button clicked: {search_clicked}")
        
        # Main content area for visualization - Only show if in full view or search clicked
        if st.session_state.view_mode == 'full' or search_clicked:
            main_container = st.container()
            with main_container:
                if search_clicked:
                    logger.info(f"Processing search with parameters: date_range={start_date} to {end_date}, feeder={selected_feeder}, transformer={selected_transformer}")
                    
                    if not all([start_date, end_date, selected_feeder, selected_transformer]):
                        st.error("Please select all required parameters")
                    else:
                        logger.info(f"Fetching data for date range: {start_date} to {end_date}")
                        
                        # Get transformer data
                        transformer_data = data_service.get_transformer_data_range(
                            start_date,
                            end_date,
                            selected_feeder,
                            selected_transformer
                        )
                        if transformer_data is not None:
                            logger.info(f"Transformer data timestamp range: {transformer_data['timestamp'].min()} to {transformer_data['timestamp'].max()}")
                        
                        # Get customer data
                        customer_data = data_service.get_customer_data_range(
                            start_date,
                            end_date,
                            selected_feeder,
                            selected_transformer
                        )
                        if customer_data is not None:
                            logger.info(f"Customer data timestamp range: {customer_data['timestamp'].min()} to {customer_data['timestamp'].max()}")
                        
                        if transformer_data is not None and not transformer_data.empty:
                            logger.info(f"Transformer data loaded successfully: {len(transformer_data)} records")
                            
                            # Automatically check alerts if unusual values detected
                            if any(transformer_data['loading_percentage'] >= 80):  # Alert threshold
                                current_time = datetime.now()
                                
                                # Only trigger if no pending alert or different transformer
                                if (not st.session_state.alert_state['pending'] or 
                                    st.session_state.alert_state['transformer_id'] != selected_transformer):
                                    
                                    logger.info("High loading detected - checking alerts automatically")
                                    alert_service = CloudAlertService()
                                    alert_result = alert_service.check_and_send_alerts(
                                        transformer_data,
                                        start_date=start_date,
                                        alert_time=current_time
                                    )
                                    
                                    if alert_result:
                                        max_loading = transformer_data['loading_percentage'].max()
                                        st.session_state.alert_state.update({
                                            'pending': True,
                                            'transformer_id': selected_transformer,
                                            'loading': max_loading,
                                            'timestamp': current_time
                                        })
                                        logger.info(f"Alert state updated for transformer {selected_transformer}")
                            
                            # Display alert acknowledgment if pending
                            if st.session_state.alert_state['pending']:
                                with st.sidebar:
                                    with st.form("alert_acknowledgment"):
                                        st.warning(f"🚨 Alert Active")
                                        st.write(f"Transformer: {st.session_state.alert_state['transformer_id']}")
                                        st.write(f"Loading: {st.session_state.alert_state['loading']:.1f}%")
                                        st.write(f"Time: {st.session_state.alert_state['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                                        
                                        if st.form_submit_button("Acknowledge Alert"):
                                            st.session_state.alert_state['pending'] = False
                                            logger.info("Alert acknowledged by user")
                            
                            # Create tabs for transformer and customer data
                            transformer_tab, customer_tab = st.tabs(["📊 Transformer Data", "👥 Customer Data"])
                            
                            with transformer_tab:
                                # Display transformer details
                                create_section_header("Transformer Details")
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    create_tile("Transformer ID", selected_transformer)
                                with col2:
                                    create_tile("Customers", str(len(customer_data['customer_id'].unique()) if customer_data is not None else 0))
                                with col3:
                                    create_tile("Latitude", "45.5123")
                                with col4:
                                    create_tile("Longitude", "-79.3892")

                                # Display power consumption chart
                                create_section_header("Power Consumption Over Time")
                                display_power_time_series(
                                    transformer_data,
                                    size_kva=transformer_data['size_kva'].iloc[0] if 'size_kva' in transformer_data.columns else None
                                )

                                # Display loading status chart
                                if 'loading_percentage' in transformer_data.columns:
                                    st.subheader("Loading Status")
                                    
                                    # Get loading analytics
                                    loading_analytics = analyze_loading_conditions(transformer_data)
                                    
                                    # Create columns for metrics
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric("Peak Loading", f"{loading_analytics['peak_loading']:.1f}%")
                                        if isinstance(loading_analytics['peak_time'], (pd.Timestamp, datetime)):
                                            peak_time_str = loading_analytics['peak_time'].strftime('%Y-%m-%d %H:%M')
                                        else:
                                            peak_time_str = str(loading_analytics['peak_time'])
                                        st.caption(f"at {peak_time_str}")
                                        
                                    with col2:
                                        st.metric("Average Loading", f"{loading_analytics['average_loading']:.1f}%")
                                        
                                    with col3:
                                        if loading_analytics['sustained_overloads']:
                                            st.metric("Sustained Overloads", len(loading_analytics['sustained_overloads']))
                                            st.caption("Click for details ⬇️")
                                    
                                    # Show condition percentages
                                    st.write("Time spent in each condition:")
                                    percentages = loading_analytics['condition_percentages']
                                    condition_counts = loading_analytics.get('condition_counts', {})
                                    for condition, pct in percentages.items():
                                        status, color = get_alert_status(120 if condition == 'Critical' else 
                                                                       100 if condition == 'Overloaded' else
                                                                       80 if condition == 'Warning' else
                                                                       50 if condition == 'Pre-Warning' else 0)
                                        count = condition_counts.get(condition, 0)
                                        st.markdown(f"<span style='color: {color}'>{condition}</span>: {pct:.1f}% / {count} instances", unsafe_allow_html=True)
                                    
                                    # Show sustained overloads if any
                                    if loading_analytics['sustained_overloads']:
                                        with st.expander("Sustained Overloads (>1 hour)"):
                                            for overload in loading_analytics['sustained_overloads']:
                                                st.markdown(f"""
                                                - **Duration**: {overload['duration_hours']:.1f} hours
                                                - **Peak**: {overload['peak_loading']:.1f}%
                                                - **Period**: {overload['start'].strftime('%Y-%m-%d %H:%M')} to {overload['end'].strftime('%Y-%m-%d %H:%M')}
                                                """)
                                    
                                    # Display the chart
                                    display_loading_status_line_chart(transformer_data)

                                # Display current and voltage charts side by side
                                current_col, voltage_col = create_two_column_charts()
                                
                                with current_col:
                                    create_section_header("Current Over Time")
                                    display_current_time_series(transformer_data)
                                    
                                with voltage_col:
                                    create_section_header("Voltage Over Time")
                                    display_voltage_time_series(transformer_data)
                            
                            with customer_tab:
                                if customer_data is not None and not customer_data.empty:
                                    display_customer_tab(customer_data)
                                else:
                                    st.warning("No customer data available for the selected period")
                        else:
                            st.warning("No transformer data available for the selected criteria.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application")

if __name__ == "__main__":
    main()
