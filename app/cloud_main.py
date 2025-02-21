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
from app.services.cloud_alert_service import CloudAlertService  # Import for alert functionality
from app.utils.ui_utils import create_banner, display_transformer_dashboard
from app.utils.ui_components import create_section_header, create_tile, create_two_column_charts
from app.visualization.charts import display_customer_tab, display_power_time_series, display_current_time_series, display_voltage_time_series, display_loading_status

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
        
        # Handle deep link parameters
        params = st.experimental_get_query_params()
        
        # If coming from alert link, pre-populate selections
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
        dates = st.sidebar.date_input(
            "Select Date Range",
            value=[min_date, min_date],  # Pass as list for range selection
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
        
        # Ensure we have a start and end date
        if isinstance(dates, (datetime, date)):
            start_date = end_date = dates
        else:
            start_date, end_date = dates[0], dates[-1]  # Handle both list and tuple cases
        
        # Feeder and transformer selection
        feeder_options = data_service.get_feeder_options()
        selected_feeder = st.sidebar.selectbox("Select Feeder", feeder_options)
        transformer_options = data_service.get_load_options(selected_feeder)
        selected_transformer = st.sidebar.selectbox(
            "Select Transformer",
            transformer_options
        )
        
        # Search button with icon
        search_clicked = st.sidebar.button(
            "🔍 Search" + (" 🔔" if st.session_state.alert_state.get('pending', False) else ""),
            type="primary",
            key="search_button"
        )
        logger.info(f"Search button clicked: {search_clicked}")
        
        # Main content area for visualization
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
                    customer_data = data_service.get_customer_data(
                        selected_transformer,
                        start_date,
                        end_date
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

                            # Initialize session state for view toggle if not exists
                            if 'show_power' not in st.session_state:
                                st.session_state.show_power = True

                            # Create columns for header and toggle
                            header_col, toggle_col = st.columns([0.9, 0.1])
                            
                            with header_col:
                                create_section_header("Power Consumption Over Time" if st.session_state.show_power else "Loading Condition Status")
                            
                            with toggle_col:
                                if st.button("↔"):
                                    st.session_state.show_power = not st.session_state.show_power

                            # Display appropriate chart based on toggle state
                            if st.session_state.show_power:
                                display_power_time_series(
                                    transformer_data,
                                    size_kva=transformer_data['size_kva'].iloc[0] if 'size_kva' in transformer_data.columns else None
                                )
                            else:
                                display_loading_status(
                                    transformer_data,
                                    size_kva=transformer_data['size_kva'].iloc[0] if 'size_kva' in transformer_data.columns else None
                                )

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
