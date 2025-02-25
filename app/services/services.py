# Standard library imports
import logging
import logging.handlers
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Optional, List, Dict, Tuple, Any
import traceback
import sys

# Third-party imports
import pandas as pd
import streamlit as st

# Local imports
from app.config.database_config import (
    TRANSFORMER_DATA_QUERY,
    TRANSFORMER_DATA_RANGE_QUERY,
    CUSTOMER_DATA_QUERY,
    TRANSFORMER_LIST_QUERY,
    CUSTOMER_AGGREGATION_QUERY,
    FEEDER_NUMBERS,
    DECIMAL_PLACES,
    init_db_pool,
    execute_query
)
from app.utils.data_validation import validate_transformer_data, analyze_trends
from app.models.data_models import (
    TransformerData,
    CustomerData,
    AlertData
)

# Initialize logger with module name
logger = logging.getLogger(__name__)

# Ensure logger has at least one handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

"""
Combined services for the Transformer Loading Analysis Application
"""

class CloudDataService:
    """Service for handling transformer and customer data in cloud environment"""
    
    def __init__(self):
        """Initialize the service"""
        logger.info("CloudDataService initialized")
    
    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        return [f"Feeder {num}" for num in FEEDER_NUMBERS]

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
                    # Return a default list of transformers for this feeder
                    default_ids = [f"S1F{feeder_num}ATF{i:03d}" for i in range(1, 11)]
                    logger.info(f"Using default transformer IDs: {default_ids}")
                    return default_ids
                
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
        """Get list of transformer IDs for a feeder"""
        try:
            if not feeder:
                return []
                
            # Extract feeder number from string (e.g. "Feeder 1" -> 1)
            feeder_num = int(feeder.split()[-1])
            
            # Get transformer IDs for this feeder
            return self.get_transformer_ids(feeder_num)
            
        except Exception as e:
            logger.error(f"Error getting load options: {str(e)}")
            return []

    def get_transformer_data(self, transformer_id: str, query_date: date, hour: int) -> Optional[pd.DataFrame]:
        """Get transformer data for a specific date and hour"""
        try:
            # Extract feeder number from transformer ID
            feeder_num = int(transformer_id.split('F')[1][0])
            if feeder_num not in FEEDER_NUMBERS:
                raise ValueError(f"Invalid feeder number: {feeder_num}")
                
            # Use the correct table name format
            table = f'"Transformer Feeder {feeder_num}"'
            logger.debug(f"Querying table: {table}")
            query = TRANSFORMER_DATA_QUERY.format(table_name=table)
            results = execute_query(query, (transformer_id, query_date, hour))
            
            if not results:
                logger.warning(f"No data found for transformer {transformer_id} on {query_date} at hour {hour}")
                return None
                
            df = pd.DataFrame(results)
            return validate_transformer_data(df)
            
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            return None

    def get_transformer_data_range(
        self,
        start_date: date,
        end_date: date,
        feeder: str,
        transformer_id: str
    ) -> Optional[pd.DataFrame]:
        """Get transformer data for a date range"""
        try:
            if not all([start_date, end_date, feeder, transformer_id]):
                return None
            
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])
            if feeder_num not in FEEDER_NUMBERS:
                raise ValueError(f"Invalid feeder number: {feeder_num}")
                
            # Use the correct table name format
            table = f'"Transformer Feeder {feeder_num}"'
            
            # Convert dates to timestamps for the query
            start_ts = datetime.combine(start_date, datetime.min.time())
            end_ts = datetime.combine(end_date, datetime.max.time())
            
            # Query data
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            results = execute_query(query, (transformer_id, start_ts, end_ts))
            
            if not results:
                logger.warning(
                    f"No data found for transformer {transformer_id} "
                    f"between {start_date} and {end_date}"
                )
                return None
                
            # Convert to DataFrame and validate
            df = pd.DataFrame(results)
            return validate_transformer_data(df)
            
        except Exception as e:
            logger.error(f"Error getting transformer data range: {str(e)}")
            return None

    def get_customer_data(
        self,
        transformer_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        feeder: Optional[int] = None
    ) -> Optional[CustomerData]:
        """Get customer data for a specific transformer"""
        try:
            if not transformer_id:
                logger.error("No transformer ID provided")
                return None
                
            # Extract feeder number from transformer ID if not provided
            if feeder is None and transformer_id.startswith('S1F'):
                try:
                    feeder = int(transformer_id[3])
                except (IndexError, ValueError):
                    logger.warning(f"Could not extract feeder number from transformer ID: {transformer_id}")
                    return None
            
            if feeder not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder}")
                return None
                
            table = f'"Customer Feeder {feeder}"'
            
            # Build query with date range if provided
            if start_date and end_date:
                query = CUSTOMER_DATA_QUERY.format(
                    table_name=table,
                    transformer_id=transformer_id,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat()
                )
            else:
                query = CUSTOMER_DATA_QUERY.format(
                    table_name=table,
                    transformer_id=transformer_id,
                    start_date='2024-01-01',
                    end_date='2024-06-28'
                )
                
            results = execute_query(query)
            
            if not results:
                logger.warning(f"No customer data found for transformer {transformer_id}")
                return None
                
            # Convert results to CustomerData model
            df = pd.DataFrame(results)
            
            return CustomerData(
                index_level_0=df['index_level_0'].tolist(),
                current_a=df['current_a'].tolist(),
                customer_id=df['customer_id'].tolist(),
                hour=df['hour'].tolist(),
                power_factor=df['power_factor'].tolist(),
                power_kva=df['power_kva'].tolist(),
                power_kw=df['power_kw'].tolist(),
                size_kva=df['size_kva'].tolist(),
                timestamp=df['timestamp'].tolist(),
                transformer_id=df['transformer_id'].tolist(),
                voltage_v=df['voltage_v'].tolist()
            )
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return None

class CloudAlertService:
    """Service for handling alerts in cloud environment"""
    
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
    
    def _get_status_color(self, loading_pct: float) -> Tuple[str, str]:
        """Get status and color based on loading percentage"""
        if loading_pct >= 120:
            return "Critical", "red"
        elif loading_pct >= 100:
            return "Overloaded", "orange"
        elif loading_pct >= 80:
            return "Warning", "yellow"
        elif loading_pct >= 50:
            return "Pre-Warning", "blue"
        else:
            return "Normal", "green"
    
    def _select_alert_point(self, results_df: pd.DataFrame) -> pd.Series:
        """Select the point to alert on"""
        # Get the row with the highest loading percentage
        max_loading_idx = results_df['loading_percentage'].idxmax()
        return results_df.loc[max_loading_idx]
    
    def _create_deep_link(
        self,
        start_date: date,
        end_date: date,
        transformer_id: str,
        hour: int = None,
        feeder: int = None
    ) -> str:
        """Create deep link back to app with context"""
        base_url = self.app_url
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'transformer_id': transformer_id
        }
        if hour is not None:
            params['hour'] = hour
        if feeder is not None:
            params['feeder'] = f"Feeder {feeder}"
            
        # Build query string
        query = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query}"
    
    def _create_email_content(
        self,
        data: pd.Series,
        status: str,
        color: str,
        deep_link: str
    ) -> str:
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
        # Format timestamp for display
        timestamp = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""
        <html>
            <body>
                <h2>Transformer Loading Alert</h2>
                <p>A transformer has exceeded its loading threshold:</p>
                
                <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Attribute</th>
                        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Transformer ID</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{data['transformer_id']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Status</td>
                        <td style="padding: 12px; border: 1px solid #ddd; color: {color};">{status}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Loading Percentage</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{data['loading_percentage']:.2f}%</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Power (kW)</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{data['power_kw']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Current (A)</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{data['current_a']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Voltage (V)</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{data['voltage_v']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border: 1px solid #ddd;">Timestamp</td>
                        <td style="padding: 12px; border: 1px solid #ddd;">{timestamp}</td>
                    </tr>
                </table>
                
                <p>Click the link below to view detailed analysis:</p>
                <p><a href="{deep_link}">View in Dashboard</a></p>
                
                <p style="color: #666; font-size: 12px;">
                    This is an automated alert from the Transformer Loading Analysis System.
                    Please do not reply to this email.
                </p>
            </body>
        </html>
        """
        return html
    
    def _send_email(self, msg: MIMEMultipart):
        """Send email using Gmail SMTP with app password"""
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.email, self.app_password)
                smtp.send_message(msg)
                logger.info("Alert email sent successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False
    
    def check_and_send_alerts(
        self,
        results_df: pd.DataFrame,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        hour: Optional[int] = None,
        feeder: Optional[int] = None,
        recipient: str = None
    ):
        """Check loading conditions and send alert if needed"""
        try:
            if not self.email_enabled:
                st.warning("Email alerts are disabled. Check Gmail app password configuration.")
                return
                
            if results_df.empty:
                st.warning("No data available for alert analysis")
                return
                
            # Get the point to alert on
            alert_point = self._select_alert_point(results_df)
            loading_pct = alert_point['loading_percentage']
            
            # Get status and color
            status, color = self._get_status_color(loading_pct)
            
            # Create email if loading is above warning threshold
            if loading_pct >= 80:  # Warning threshold
                # Create deep link
                deep_link = self._create_deep_link(
                    start_date=start_date or date.today(),
                    end_date=end_date or date.today(),
                    transformer_id=alert_point['transformer_id'],
                    hour=hour,
                    feeder=feeder
                )
                
                # Create email content
                html_content = self._create_email_content(
                    data=alert_point,
                    status=status,
                    color=color,
                    deep_link=deep_link
                )
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"Transformer Alert: {status} Loading Detected"
                msg['From'] = self.email
                msg['To'] = recipient or self.email
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send email
                if self._send_email(msg):
                    st.success(f"Alert sent: {status} loading detected")
                else:
                    st.error("Failed to send alert email")
            else:
                st.info(f"No alerts needed. Current status: {status}")
                
        except Exception as e:
            logger.error(f"Error in check_and_send_alerts: {str(e)}")
            st.error("Failed to process alerts")

def get_alert_status(loading_pct: float) -> Tuple[str, str]:
    """Get alert status and color based on loading percentage"""
    if loading_pct >= 120:
        return "Critical", "red"
    elif loading_pct >= 100:
        return "Overloaded", "orange"
    elif loading_pct >= 80:
        return "Warning", "yellow"
    elif loading_pct >= 50:
        return "Pre-Warning", "blue"
    else:
        return "Normal", "green"

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    emoji_map = {
        "Critical": "🔴",
        "Overloaded": "🟠",
        "Warning": "🟡",
        "Pre-Warning": "🔵",
        "Normal": "🟢"
    }
    return emoji_map.get(status, "❓")
