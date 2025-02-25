"""
Combined services for the Transformer Loading Analysis Application
"""

# Standard library imports
import logging
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, time, timedelta
import smtplib
from typing import List, Optional, Dict, Tuple

# Third-party imports
import pandas as pd

# Local imports
from app.config.database_config import (
    TRANSFORMER_DATA_QUERY,
    TRANSFORMER_DATA_RANGE_QUERY,
    CUSTOMER_DATA_QUERY,
    TRANSFORMER_LIST_QUERY,
    CUSTOMER_AGGREGATION_QUERY
)
from app.config.table_config import (
    TRANSFORMER_TABLE_TEMPLATE,
    CUSTOMER_TABLE_TEMPLATE,
    FEEDER_NUMBERS,
    DECIMAL_PLACES
)
from app.utils.db_utils import (
    init_db_pool,
    execute_query
)
from app.utils.data_validation import validate_transformer_data, analyze_trends
from app.models.data_models import (
    TransformerData,
    CustomerData,
    AggregatedCustomerData
)

# Initialize logger
logger = logging.getLogger(__name__)

# Alert helper functions
def get_alert_status(loading_pct: float) -> tuple[str, str]:
    """Get alert status and color based on loading percentage"""
    if loading_pct >= 120:
        return 'Critical', '#dc3545'
    elif loading_pct >= 100:
        return 'Overloaded', '#fd7e14'
    elif loading_pct >= 80:
        return 'Warning', '#ffc107'
    elif loading_pct >= 50:
        return 'Pre-Warning', '#6f42c1'
    else:
        return 'Normal', '#198754'

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    return {
        'Critical': '🔴',
        'Overloaded': '🟠',
        'Warning': '🟡',
        'Pre-Warning': '🟣',
        'Normal': '🟢'
    }.get(status, '⚪')

class CloudDataService:
    """Service class for handling data operations in the cloud environment"""
    
    def __init__(self):
        """Initialize the data service"""
        try:
            logger.info("Initializing CloudDataService...")
            # Initialize database connection pool
            init_db_pool()
            logger.info("Database pool initialized successfully")
            
            # Cache for transformer IDs
            self._transformer_ids: Optional[List[str]] = None
            
            # Cache for available feeders
            self._available_feeders: Optional[List[str]] = None
            
            # Dataset date range
            self.min_date = date(2024, 1, 1)
            self.max_date = date(2024, 6, 28)
            
            logger.info(f"CloudDataService initialized with date range: {self.min_date} to {self.max_date}")
        except Exception as e:
            logger.error(f"Error initializing CloudDataService: {str(e)}")
            raise

    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        if self._available_feeders is None:
            logger.info("Getting feeder options...")
            self._available_feeders = [f"Feeder {num}" for num in FEEDER_NUMBERS]
            logger.info(f"Found {len(self._available_feeders)} feeders: {self._available_feeders}")
        return self._available_feeders

    def get_transformer_ids(self, feeder_num: int) -> List[str]:
        """Get list of transformer IDs for a specific feeder"""
        try:
            logger.info(f"Retrieving transformer IDs for feeder {feeder_num}...")
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                return []
            
            # Use the correct table name format
            table = f'"Transformer Feeder {feeder_num}"'
            logger.debug(f"Querying transformer IDs from table: {table}")
            
            try:
                query = TRANSFORMER_LIST_QUERY.format(table_name=table)
                results = execute_query(query)
                
                if results:
                    transformer_ids = [r['transformer_id'] for r in results]
                    logger.info(f"Found {len(transformer_ids)} transformers")
                    logger.debug(f"Transformer IDs: {transformer_ids}")
                    return sorted(transformer_ids)
                else:
                    logger.warning(f"No transformers found for feeder {feeder_num}")
                    return []
            except Exception as e:
                logger.error(f"Database error getting transformer IDs: {str(e)}")
                # Return a default list of transformers for this feeder
                default_ids = [f"S1F{feeder_num}ATF{i:03d}" for i in range(1, 11)]
                logger.info(f"Using default transformer IDs: {default_ids}")
                return default_ids
                
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_load_options(self, feeder: str) -> List[str]:
        """Get list of available transformer IDs"""
        try:
            logger.info(f"Retrieving transformer IDs for {feeder}...")
            # Extract feeder number from string like "Feeder 1"
            feeder_num = int(feeder.split()[-1])
            return self.get_transformer_ids(feeder_num)
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_available_dates(self) -> tuple[date, date]:
        """Get the available date range for data queries"""
        logger.info(f"Returning date range: {self.min_date} to {self.max_date}")
        return self.min_date, self.max_date

    def _format_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format numeric columns with proper decimal places"""
        if df is None or df.empty:
            return df
            
        # Apply formatting to each numeric column based on configuration
        for col, decimals in DECIMAL_PLACES.items():
            if col in df.columns:
                df[col] = df[col].round(decimals)
        
        return df

    def get_transformer_data(self, transformer_id: str, date: datetime, hour: int, feeder: str) -> Optional[pd.DataFrame]:
        """
        Get transformer data for a specific date and hour.
        
        Args:
            transformer_id (str): Transformer identifier
            date (datetime): The datetime object for the query
            hour (int): Hour of the day (0-23)
            feeder (str): Feeder identifier (e.g., "Feeder 1")
        
        Returns:
            Optional[pd.DataFrame]: DataFrame containing transformer data or None if no data found
        """
        try:
            # Extract just the date part for the query
            query_date = date.date() if isinstance(date, datetime) else date
            
            # Extract feeder number from string like "Feeder 1"
            feeder_num = int(feeder.split()[-1])
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                raise ValueError(f"Invalid feeder number: {feeder_num}")
                
            # Table name already includes quotes
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            logger.debug(f"Querying table: {table}")
            query = TRANSFORMER_DATA_QUERY.format(table_name=table)
            results = execute_query(query, (transformer_id, query_date, hour))
            
            if results and len(results) > 0:
                df = pd.DataFrame(results)
                df = self._format_numeric_columns(df)
                return df
            return None
            
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            raise

    def get_transformer_data_range(
        self,
        start_date: date, 
        end_date: date, 
        feeder: str, 
        transformer_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Get transformer data for a date range.
        """
        try:
            logger.info(f"Fetching transformer data for {transformer_id}")
            
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Convert dates to timestamps for the query
            start_ts = datetime.combine(start_date, time.min)
            end_ts = datetime.combine(end_date, time.max)
            
            # Execute query
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            params = (transformer_id, start_ts, end_ts)
            
            results = execute_query(query, params)
            if not results:
                return None
                
            # Convert to DataFrame and format
            df = pd.DataFrame(results)
            df = self._format_numeric_columns(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting transformer data range: {str(e)}")
            return None

    def get_customer_data(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date,
        feeder: str
    ) -> Optional[pd.DataFrame]:
        """Get customer data for analysis"""
        try:
            logger.info(f"Fetching customer data for {transformer_id}")
            
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Convert dates to timestamps
            start_ts = datetime.combine(start_date, time.min)
            end_ts = datetime.combine(end_date, time.max)
            
            # Execute query
            query = CUSTOMER_DATA_QUERY.format(table_name=table)
            params = (transformer_id, start_ts, end_ts)
            
            results = execute_query(query, params)
            if not results:
                return None
                
            # Convert to DataFrame and format
            df = pd.DataFrame(results)
            df = self._format_numeric_columns(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return None

    def get_aggregated_customer_data(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date,
        feeder: str
    ) -> Optional[pd.DataFrame]:
        """Get aggregated customer data"""
        try:
            logger.info(f"Fetching aggregated customer data for {transformer_id}")
            
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Convert dates to timestamps
            start_ts = datetime.combine(start_date, time.min)
            end_ts = datetime.combine(end_date, time.max)
            
            # Execute query
            query = CUSTOMER_AGGREGATION_QUERY.format(table_name=table)
            params = (transformer_id, start_ts, end_ts)
            
            results = execute_query(query, params)
            if not results:
                return None
                
            # Convert to DataFrame and format
            df = pd.DataFrame(results)
            df = self._format_numeric_columns(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting aggregated customer data: {str(e)}")
            return None

class CloudAlertService:
    def __init__(self):
        """Initialize the alert service"""
        # Set the app URL to the current cloud deployment
        self.app_url = "https://transformer-dashboard.streamlit.app"
        self.email = st.secrets.get("DEFAULT_EMAIL", "jhnapo2213@gmail.com")
        self.app_password = st.secrets.get("GMAIL_APP_PASSWORD")
        self.email_enabled = self.app_password is not None
        
        if not self.email_enabled:
            logger.warning("Email alerts disabled: Gmail app password not found in secrets")
        else:
            logger.info("Email alerts enabled")

    def _get_status_color(self, loading_pct: float) -> tuple:
        """Get status and color based on loading percentage"""
        if loading_pct >= 120:
            return "CRITICAL", "#dc3545", "🚨"
        elif loading_pct >= 100:
            return "OVERLOADED", "#fd7e14", "⚠️"
        elif loading_pct >= 80:
            return "WARNING", "#ffc107", "⚡"
        elif loading_pct >= 50:
            return "PRE-WARNING", "#6f42c1", "📊"
        else:
            return "NORMAL", "#198754", "✅"

    def _select_alert_point(self, results_df: pd.DataFrame) -> Optional[pd.Series]:
        """Select the point to alert on"""
        try:
            # Find the highest loading percentage
            max_loading_idx = results_df['loading_percentage'].idxmax()
            max_loading = results_df.iloc[max_loading_idx].copy()  # Use copy to avoid modifying original
            
            # Ensure we have the correct timestamp
            max_loading.name = results_df['timestamp'].iloc[max_loading_idx]
            
            # Log the max loading found
            logger.info(f"Found max loading: {max_loading['loading_percentage']:.1f}% at {max_loading.name}")
            
            # Only alert if loading is high enough
            if max_loading['loading_percentage'] >= 80:
                return max_loading
            else:
                logger.info(f"Max loading {max_loading['loading_percentage']:.1f}% below alert threshold (80%)")
                st.info(f"🔍 Maximum loading ({max_loading['loading_percentage']:.1f}%) is below alert threshold (80%)")
                return None
                
        except Exception as e:
            logger.error(f"Error selecting alert point: {str(e)}")
            return None

    def _create_deep_link(self, start_date: date, end_date: date, alert_time: datetime, transformer_id: str, hour: int = None, feeder: int = None) -> str:
        """Create deep link back to app with context"""
        # Create URL parameters with None checks
        params = {
            'view': 'alert',
            'id': transformer_id
        }
        
        # Only add dates if they exist
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
            
        # Add hour from parameter or alert time
        if hour is not None:
            params['hour'] = str(hour)
        elif alert_time:
            params['hour'] = str(alert_time.hour)
            
        # Add feeder if it exists
        if feeder is not None:
            params['feeder'] = str(feeder)
            
        # Create query string
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        return f"{self.app_url}?{query_string}"

    def _create_email_content(self, data: pd.Series, status: str, color: str, deep_link: str) -> str:
        """
        Create HTML content for alert email with context
        
        Args:
            data: Series with transformer data at alert point
            status: Status of the alert
            color: Color of the alert
            deep_link: Deep link back to app
            
        Returns:
            str: HTML content of the email
        """
        transformer_id = data['transformer_id']
        loading_pct = data['loading_percentage']
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2f4f4f;">Transformer Loading Alert {get_status_emoji(status)}</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: {color};">Status: {status}</h3>
                <p><strong>Transformer:</strong> {transformer_id}</p>
                <p><strong>Loading:</strong> {loading_pct:.1f}%</p>
                <p><strong>Alert Time:</strong> {data.name.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h4>Detailed Readings:</h4>
                <ul>
                    <li>Power: {data['power_kw']:.1f} kW</li>
                    <li>Current: {data['current_a']:.1f} A</li>
                    <li>Voltage: {data['voltage_v']:.1f} V</li>
                    <li>Power Factor: {data['power_factor']:.2f}</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{deep_link}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Loading History
                </a>
            </div>
            
            <p style="color: #6c757d; font-size: 12px; text-align: center;">
                This is an automated alert from your Transformer Loading Analysis System.<br>
                Click the button above to view the loading history leading up to this alert.
            </p>
        </div>
        """
        return html
    
    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using Gmail SMTP with app password"""
        try:
            logger.info(f"Attempting to send email to {msg['To']}")
            
            # Connect to Gmail's SMTP server
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.email, self.app_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info("Email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            if "Invalid login" in str(e):
                st.error("❌ Failed to login to Gmail. Please check your app password in secrets.toml")
            return False

    def check_and_send_alerts(
        self,
        results_df: pd.DataFrame,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        alert_time: Optional[datetime] = None,
        hour: Optional[int] = None,
        feeder: Optional[int] = None,
        recipient: str = None
    ) -> bool:
        """Check loading conditions and send alert if needed"""
        try:
            if results_df is None or results_df.empty:
                logger.warning("No data to check for alerts")
                return False
                
            # Select point to alert on
            alert_point = self._select_alert_point(results_df)
            if alert_point is None:
                return False
                
            # Get alert status and color
            status, color = get_alert_status(alert_point['loading_percentage'])
            
            # Create deep link back to app
            deep_link = self._create_deep_link(
                start_date=start_date,
                end_date=end_date,
                alert_time=alert_time or alert_point.name,
                transformer_id=alert_point['transformer_id'],
                hour=hour,
                feeder=feeder
            )
            
            # Create email content
            html_content = self._create_email_content(alert_point, status, color, deep_link)
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔔 Transformer Loading Alert - {status}"
            msg['From'] = self.email
            msg['To'] = recipient or self.email
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            if self.email_enabled:
                success = self._send_email(msg)
                if success:
                    st.success(f"✉️ Alert email sent successfully to {msg['To']}")
                return success
            else:
                logger.warning("Email alerts are disabled")
                st.warning("⚠️ Email alerts are disabled. Add GMAIL_APP_PASSWORD to secrets.toml to enable.")
                return False
                
        except Exception as e:
            logger.error(f"Error checking and sending alerts: {str(e)}")
            st.error(f"❌ Failed to send alert: {str(e)}")
            return False
