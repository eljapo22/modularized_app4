"""
Cloud-specific entry point for the Transformer Loading Analysis Application
"""

import streamlit as st
import logging
import traceback
from datetime import datetime
from app.services.cloud_data_service import CloudDataService
from app.services.cloud_alert_service import CloudAlertService
from app.visualization.charts import display_transformer_dashboard
from app.utils.ui_components import create_tile, create_banner, create_section_banner
from app.utils.performance import log_performance

# Configure page - must be first Streamlit command
st.set_page_config(page_title="Transformer Loading Analysis", layout="wide")

# Just hide the main content with CSS - no logic, no JavaScript, no session state
st.markdown("""
<style>
    /* Hide all main content */
    section.main > div {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Add custom CSS for tabs and sidebar
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F0F2F6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
    }
    section[data-testid="stSidebar"] > div {
        background-color: #F0F2F6;
        padding-top: 2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
    }
    div[data-testid="stSidebarNav"] {
        padding-top: 1rem;
    }
    div[data-testid="stSidebarNav"]::before {
        content: "Navigation";
        margin-left: 20px;
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@log_performance
def main():
    """Main application function for cloud environment"""
    try:
        # Initialize services
        data_service = CloudDataService()
        alert_service = CloudAlertService()
        
        # Ensure dashboard is always the first view by resetting relevant session state
        if 'app_initialized' not in st.session_state:
            # Reset any view-related session state on first load
            # Ensure we start with the transformer dashboard view (first view)
            st.session_state.show_customer_details = False  # Hide individual customer view (third view)
            st.session_state.show_customer_bridge = False   # Hide customer list/bridge view (second view)
            # Remove any selected customer to start fresh
            if 'selected_customer_id' in st.session_state:
                del st.session_state['selected_customer_id']
            st.session_state.app_initialized = True
        
        # Create header banner
        create_banner("Transformer Loading Analysis Dashboard")
        
        # Create sidebar
        with st.sidebar:
            st.markdown("## Analysis Parameters")
            
            # Date selection
            min_date, max_date = data_service.get_available_dates()
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="start_date_selector"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="end_date_selector"
                )
            
            # Hour selection
            selected_hour = st.number_input(
                "Select Hour (0-23)",
                min_value=0,
                max_value=23,
                value=12,
                key="hour_selector"
            )
            
            # Feeder selection
            selected_feeder = st.selectbox(
                "Select Feeder",
                options=[1, 2, 3, 4],
                key="feeder_selector"
            )
            
            # Transformer selection
            transformers = data_service.get_transformer_ids(selected_feeder)
            selected_transformer = st.selectbox(
                "Select Transformer",
                options=transformers,
                key="transformer_selector"
            )
            
            # Alert button
            st.markdown("---")
            st.markdown("## Alerts")
            if st.button("Search & Alert", key="alert_button"):
                with st.spinner("Sending alerts..."):
                    alert_service.process_alerts(
                        start_date,
                        selected_hour,
                        selected_feeder,
                        selected_transformer
                    )
                st.success("Alerts sent successfully!")
        
        # Create main content area with tabs
        tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Data"])
        
        with tab1:
            # Display transformer dashboard
            display_transformer_dashboard(
                data_service,
                selected_transformer,
                start_date,
                end_date,
                selected_feeder
            )
        
        with tab2:
            # Create data section
            create_section_banner("Raw Data")
            
            # Get and display transformer data
            transformer_data = data_service.get_transformer_data_range(
                start_date,
                end_date,
                f"Feeder {selected_feeder}",
                selected_transformer
            )
            if transformer_data is not None:
                st.dataframe(transformer_data)
            else:
                st.warning("No transformer data available for the selected parameters.")
            
            # Get and display customer data
            customer_data = data_service.get_customer_data(
                selected_transformer,
                start_date,
                selected_hour
            )
            if customer_data is not None:
                st.dataframe(customer_data)
            else:
                st.warning("No customer data available for the selected parameters.")
    
    except Exception as e:
        st.error("An error occurred while running the application.")
        logging.error(f"Application error: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
