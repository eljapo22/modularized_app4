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
        
        # Create header banner
        create_banner("Transformer Loading Analysis Dashboard")
        
        # Handle URL parameters from alert links
        params = st.query_params
        alert_view = params.get("view") == "alert"
        alert_transformer = params.get("id")
        alert_time = params.get("alert_time")
        
        if alert_time:
            alert_datetime = datetime.fromisoformat(alert_time)
            initial_date = alert_datetime.date()
            initial_hour = alert_datetime.hour
        else:
            initial_date = datetime.now().date()
            initial_hour = 12
            
        # Create sidebar
        with st.sidebar:
            st.markdown("## Analysis Parameters")
            
            # Date selection
            selected_date = st.date_input(
                "Select Date",
                value=initial_date,
                key="date_selector"
            )
            
            # Hour selection
            selected_hour = st.number_input(
                "Select Hour (0-23)",
                min_value=0,
                max_value=23,
                value=initial_hour,
                key="hour_selector"
            )
            
            # Get feeder from transformer ID if coming from alert
            initial_feeder = int(alert_transformer[2]) if alert_transformer else 1
            
            # Feeder selection
            selected_feeder = st.selectbox(
                "Select Feeder",
                options=[1, 2, 3, 4],
                value=initial_feeder,
                key="feeder_selector"
            )
            
            # Transformer selection
            transformers = data_service.get_transformer_ids(selected_feeder)
            selected_transformer = st.selectbox(
                "Select Transformer",
                options=transformers,
                value=alert_transformer if alert_transformer in transformers else transformers[0],
                key="transformer_selector"
            )
            
            # Alert button
            st.markdown("---")
            st.markdown("## Alerts")
            if st.button("Search & Alert", key="alert_button"):
                with st.spinner("Sending alerts..."):
                    alert_service.process_alerts(
                        selected_date,
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
                selected_date,
                selected_hour,
                selected_feeder
            )
        
        with tab2:
            # Create data section
            create_section_banner("Raw Data")
            
            # Get and display transformer data
            transformer_data = data_service.get_transformer_data(
                selected_date,
                selected_hour,
                selected_feeder,
                selected_transformer
            )
            if transformer_data is not None:
                st.dataframe(transformer_data)
            else:
                st.warning("No transformer data available for the selected parameters.")
            
            # Get and display customer data
            customer_data = data_service.get_customer_data(
                selected_transformer,
                selected_date,
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
