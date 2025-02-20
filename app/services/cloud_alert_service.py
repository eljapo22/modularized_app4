"""
Cloud-specific alert service for the Transformer Loading Analysis Application
"""
import logging
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import pandas as pd
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

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

class CloudAlertService:
    def __init__(self):
        """Initialize the alert service"""
        self.gmail_creds = None
        try:
            # Get credentials from Streamlit secrets
            if "gmail" in st.secrets:
                self.gmail_creds = Credentials.from_authorized_user_info(
                    st.secrets["gmail"]
                )
        except Exception as e:
            logger.error(f"Error initializing Gmail credentials: {str(e)}")
    
    def create_email_content(self, transformer_data: pd.DataFrame, date: datetime, hour: int) -> str:
        """Create HTML email content with transformer data"""
        app_url = st.secrets.get("APP_URL", "https://your-app.streamlit.io")
        
        html_parts = []
        for _, row in transformer_data.iterrows():
            transformer_id = row['transformer_id']
            loading_pct = row['loading_percentage']
            status, color = get_alert_status(loading_pct)
            emoji = get_status_emoji(status)
            
            # Create deep link back to app
            alert_link = f"{app_url}?view=alert&id={transformer_id}"
            
            html_parts.append(f"""
            <div style="margin-bottom: 20px; font-family: Arial, sans-serif;">
                <h2 style="color: #2f4f4f;">Transformer Loading Alert</h2>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <h3>Transformer {transformer_id}</h3>
                    <p style="color: {color};">
                        {emoji} Status: {status}<br>
                        Loading: {loading_pct:.1f}%
                    </p>
                    
                    <h4>Current Readings:</h4>
                    <ul>
                        <li>Power: {row.get('power_kw', 'N/A'):.1f} kW</li>
                        <li>Current: {row.get('current_a', 'N/A'):.1f} A</li>
                        <li>Voltage: {row.get('voltage_v', 'N/A'):.1f} V</li>
                        <li>Power Factor: {row.get('power_factor', 'N/A'):.2f}</li>
                    </ul>
                    
                    <p>Time: {date.strftime('%Y-%m-%d')} {hour:02d}:00</p>
                    
                    <p>
                        <a href="{alert_link}" 
                           style="background-color: #0d6efd; color: white; padding: 10px 20px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Details
                        </a>
                    </p>
                </div>
            </div>
            """)
        
        return "\n".join(html_parts)
    
    def send_alert(self, transformer_data: pd.DataFrame, date: datetime, hour: int, recipient: str) -> bool:
        """
        Send an alert email for transformer loading conditions
        
        Args:
            transformer_data: DataFrame with transformer readings
            date: Date of the readings
            hour: Hour of the readings
            recipient: Email recipient
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            if not self.gmail_creds:
                logger.error("Gmail credentials not configured")
                return False
            
            # Create email message
            message = MIMEMultipart()
            message["to"] = recipient
            
            # Get status of first transformer for subject
            first_row = transformer_data.iloc[0]
            status, _ = get_alert_status(first_row['loading_percentage'])
            message["subject"] = f"Transformer Alert: {first_row['transformer_id']} - {status}"
            
            # Create and attach HTML content
            html_content = self.create_email_content(transformer_data, date, hour)
            message.attach(MIMEText(html_content, "html"))
            
            # Send email using Gmail API
            service = build('gmail', 'v1', credentials=self.gmail_creds)
            service.users().messages().send(
                userId="me",
                body={"raw": message.as_string()}
            ).execute()
            
            logger.info(f"Alert email sent for {len(transformer_data)} transformers")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
            return False
    
    def check_and_send_alerts(self, results_df: pd.DataFrame, date: datetime, hour: int, threshold: float = 80.0) -> bool:
        """
        Check transformer data and send alerts if needed
        
        Args:
            results_df: DataFrame with transformer readings
            date: Date of the readings
            hour: Hour of the readings
            threshold: Loading percentage threshold for alerts (default: 80.0)
            
        Returns:
            bool: True if alerts processed successfully
        """
        try:
            # Filter transformers above threshold
            alerts_df = results_df[results_df['loading_percentage'] >= threshold].copy()
            
            if alerts_df.empty:
                logger.info("No alerts needed")
                return True
            
            # Get recipient from secrets
            recipient = st.secrets.get("ALERT_RECIPIENT", "default@example.com")
            
            # Send alert email
            return self.send_alert(alerts_df, date, hour, recipient)
            
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
            return False
