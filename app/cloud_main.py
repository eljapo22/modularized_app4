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
from app.visualization.charts import display_customer_tab, display_power_time_series, display_current_time_series, display_voltage_time_series

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
        
        # Initialize services
        data_service = CloudDataService()
        
        # Sidebar
        st.sidebar.title("Transformer Selection")
        
        # Get available transformer IDs
        transformer_ids = data_service.get_transformer_ids()
        transformer_id = st.sidebar.selectbox("Select Transformer", transformer_ids)
        
        # Add toggle for chart type
        chart_type = st.sidebar.radio(
            "Select Chart Type",
            ["Power Consumption Over Time", "Loading Condition Status"]
        )
        
        if transformer_id:
            # Get data
            df = data_service.get_transformer_data(transformer_id)
            
            if not df.empty:
                st.title(f"Transformer Analysis: {transformer_id}")
                
                # Display appropriate chart based on selection
                if chart_type == "Power Consumption Over Time":
                    display_power_time_series(df)
                else:
                    logger.info(f"Fetching data for date range: {start_date} to {end_date}")
                    
                    # Get transformer data
                    transformer_data = data_service.get_transformer_data_range(
                        transformer_id,
                        start_date,
                        end_date
                    )
                    
                    if transformer_data is not None and not transformer_data.empty:
                        logger.info(f"Transformer data loaded successfully: {len(transformer_data)} records")
                        
                        # Display loading status and check alerts if needed
                        display_loading_status(transformer_data)
                        
                        # Automatically check alerts if unusual values detected
                        if any(transformer_data['loading_percentage'] >= 80):  # Alert threshold
                            current_time = datetime.now()
                            
                            # Only trigger if no pending alert or different transformer
                            if (not st.session_state.alert_state['pending'] or 
                                st.session_state.alert_state['transformer_id'] != transformer_id):
                                
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
                                        'transformer_id': transformer_id,
                                        'loading': max_loading,
                                        'timestamp': current_time
                                    })
                                    logger.info(f"Alert state updated for transformer {transformer_id}")
                        
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
                                create_tile("Transformer ID", transformer_id)
                            with col2:
                                create_tile("Customers", "0")
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

                            # Display current and voltage charts side by side
                            current_col, voltage_col = create_two_column_charts()
                            
                            with current_col:
                                create_section_header("Current Over Time")
                                display_current_time_series(transformer_data)
                                
                            with voltage_col:
                                create_section_header("Voltage Over Time")
                                display_voltage_time_series(transformer_data)
                        
                        with customer_tab:
                            st.warning("No customer data available for the selected period")
                    else:
                        st.warning("No transformer data available for the selected criteria.")
            else:
                st.warning("No data available for selected transformer.")
    
    except Exception as e:
        logger.error(f"Application error: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("An error occurred while running the application")

if __name__ == "__main__":
    main()
