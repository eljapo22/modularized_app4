# Standard library imports
import logging
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Optional, List
import sys
import re

# Third-party imports
import pandas as pd
import streamlit as st

# Local imports
from app.config.database_config import (
    FEEDER_NUMBERS,
    get_transformer_data,
    get_transformer_ids,
    execute_query,
    get_customer_data
)
from app.utils.data_validation import validate_transformer_data, analyze_trends
from app.models.data_models import (
    TransformerData,
    CustomerData,
    AlertData
)

# Get logger for this module
logger = logging.getLogger(__name__)

class CloudDataService:
    """Service for handling cloud data operations"""
    
    def __init__(self):
        """Initialize the service"""
        logger.info("CloudDataService initialized")
        # Cache for transformer IDs
        self._transformer_ids_cache = {}

    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        return [f"Feeder {num}" for num in FEEDER_NUMBERS]

    def get_transformer_ids(self, feeder: str) -> List[str]:
        """Get list of transformer IDs for a specific feeder"""
        try:
            # Extract feeder number
            if isinstance(feeder, str):
                match = re.search(r'\d+', feeder)
                if match:
                    feeder_num = int(match.group())
                else:
                    logger.error(f"Could not extract feeder number from: {feeder}")
                    return []
            elif isinstance(feeder, (int, float)):
                feeder_num = int(feeder)
            else:
                logger.error(f"Invalid feeder type: {type(feeder)}")
                return []

            # Check cache first
            if feeder_num in self._transformer_ids_cache:
                return self._transformer_ids_cache[feeder_num]
            
            # Get transformer IDs from database
            transformer_ids = get_transformer_ids(feeder_num)
            
            # Cache the results
            if transformer_ids:
                self._transformer_ids_cache[feeder_num] = transformer_ids
            
            return transformer_ids
            
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_transformer_data_range(self, start_date: date, end_date: date, feeder: str, transformer_id: str) -> pd.DataFrame:
        """Get transformer data for a date range"""
        try:
            # Extract feeder number
            if isinstance(feeder, str):
                match = re.search(r'\d+', feeder)
                if match:
                    feeder_num = int(match.group())
                else:
                    logger.error(f"Could not extract feeder number from: {feeder}")
                    return pd.DataFrame()
            elif isinstance(feeder, (int, float)):
                feeder_num = int(feeder)
            else:
                logger.error(f"Invalid feeder type: {type(feeder)}")
                return pd.DataFrame()

            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: Feeder {feeder_num}")
                return pd.DataFrame()
            
            # Get data from database
            transformer_data = get_transformer_data(
                transformer_id=transformer_id,
                query_date=start_date,
                feeder=feeder_num
            )
            
            if transformer_data.empty:
                logger.warning(f"No data found for transformer {transformer_id} on feeder {feeder_num}")
                return pd.DataFrame()
            
            return transformer_data
            
        except Exception as e:
            logger.error(f"Error in get_transformer_data_range: {str(e)}")
            return pd.DataFrame()

    def get_customer_data(self, start_date: date, end_date: date, feeder: str, transformer_id: str) -> pd.DataFrame:
        """Get customer data for a specific transformer and date range"""
        try:
            # Extract feeder number
            if isinstance(feeder, str):
                match = re.search(r'\d+', feeder)
                if match:
                    feeder_num = int(match.group())
                else:
                    logger.error(f"Could not extract feeder number from: {feeder}")
                    return pd.DataFrame()
            elif isinstance(feeder, (int, float)):
                feeder_num = int(feeder)
            else:
                logger.error(f"Invalid feeder type: {type(feeder)}")
                return pd.DataFrame()

            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: Feeder {feeder_num}")
                return pd.DataFrame()
            
            # Get data from database
            customer_data = get_customer_data(
                transformer_id=transformer_id,
                start_date=start_date,
                end_date=end_date,
                feeder=feeder_num
            )
            
            if customer_data.empty:
                logger.warning(f"No customer data found for transformer {transformer_id} on feeder {feeder_num}")
                return pd.DataFrame()
            
            return customer_data
            
        except Exception as e:
            logger.error(f"Error in get_customer_data: {str(e)}")
            return pd.DataFrame()

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

    def _get_status_color(self, loading_pct: float) -> str:
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
        if results_df.empty:
            return None
            
        # Get point with highest loading
        return results_df.iloc[results_df['loading_percentage'].idxmax()]

    def _create_deep_link(self, start_date: date, end_date: date, transformer_id: str, hour: int = None, feeder: int = None) -> str:
        """Create deep link back to app with context"""
        # Ensure we have both dates
        if not end_date:
            end_date = start_date
            
        # Format dates as ISO format for URL
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'transformer_id': transformer_id
        }
        
        # Add hour if specified
        if hour is not None:
            params['hour'] = str(hour)
            
        # Add feeder if specified
        if feeder is not None:
            params['feeder'] = str(feeder)
        
        # Create query string with URL encoding
        query = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        return f"{self.app_url}?{query}"

    def _create_email_content(self, data: pd.Series, status: str, color: str, deep_link: str) -> str:
        """Create HTML content for alert email"""
        timestamp = data['timestamp'].strftime('%Y-%m-%d %H:%M')
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #333;">Transformer Loading Alert ⚡</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="color: {color}; font-weight: bold; margin: 0;">Status: {status}</p>
                <p style="margin: 10px 0;">Transformer: {data['transformer_id']}</p>
                <p style="margin: 10px 0;">Loading: {data['loading_percentage']:.1f}%</p>
                <p style="margin: 10px 0;">Alert Time: {timestamp}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h3 style="color: #333;">Detailed Readings:</h3>
                <ul style="list-style-type: none; padding: 0;">
                    <li>Power: {data['power_kw']:.1f} kW</li>
                    <li>Current: {data['current_a']:.1f} A</li>
                    <li>Voltage: {data.get('voltage_v', 'N/A')} V</li>
                    <li>Power Factor: {data.get('power_factor', 'N/A'):.2f}</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{deep_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Loading History</a>
            </div>
            
            <p style="color: #666; font-size: 12px; text-align: center;">
                This is an automated alert from your Transformer Loading Analysis System.<br>
                Click the button above to view the loading history leading up to this alert.
            </p>
        </body>
        </html>
        """
        return html

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using Gmail SMTP with app password"""
        try:
            logger.info(f"Attempting to send email to {msg['To']}")
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.email, self.app_password)
                smtp.send_message(msg)
                
            logger.info("Email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def check_and_send_alerts(
            self,
            results_df: pd.DataFrame,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            hour: Optional[int] = None,
            feeder: Optional[int] = None,
            recipient: str = None
        ) -> bool:
        """Check loading conditions and send alert if needed"""
        try:
            if results_df.empty:
                logger.warning("No data available for alerts")
                return False
                
            # Select point to alert on
            alert_point = self._select_alert_point(results_df)
            if alert_point is None:
                logger.warning("No alert point found")
                return False
                
            # Get status and color
            loading_pct = alert_point['loading_percentage']
            status, color = self._get_status_color(loading_pct)
            
            if loading_pct < 80:
                st.info(f"No alerts needed. Current status: {status}")
                return False
                
            # Create deep link
            deep_link = self._create_deep_link(
                start_date=start_date,
                end_date=end_date,
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
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Transformer Alert: {status} Loading ({loading_pct:.1f}%)"
            msg['From'] = self.email
            msg['To'] = recipient or self.email
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            if self._send_email(msg):
                st.success(f"✉️ Alert sent: {status} loading detected")
                return True
            else:
                st.error("Failed to send alert")
                return False
                
        except Exception as e:
            logger.error(f"Error in check_and_send_alerts: {str(e)}")
            st.error("Failed to process alerts")
            return False

def get_alert_status(loading_pct: float) -> tuple[str, str]:
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
