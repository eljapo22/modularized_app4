"""
Cloud-specific alert service for the Transformer Loading Analysis Application
"""
import logging
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, date
import pandas as pd
from typing import Optional, List, Dict, Tuple
import smtplib
import json
import base64

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
        self.app_url = st.secrets.get("APP_URL", "https://modularized-app4.streamlit.app")
        
        # Try to get Gmail credentials, but don't fail if they're not available
        try:
            # Parse the GMAIL_TOKEN from secrets
            gmail_token = json.loads(st.secrets["GMAIL_TOKEN"])
            self.gmail_creds = Credentials.from_authorized_user_info(gmail_token)
            self.default_recipient = st.secrets["DEFAULT_RECIPIENT"]
            self.email_enabled = True
            logger.info("Email alerts enabled")
        except Exception as e:
            logger.warning(f"Email alerts disabled: Gmail credentials not found in secrets - {str(e)}")
            self.email_enabled = False
    
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

    def _select_alert_point(self, results: pd.DataFrame) -> Optional[pd.Series]:
        """
        Find the latest point that exceeds the threshold in the date range.
        
        Args:
            results: DataFrame with transformer data
            
        Returns:
            tuple: (DataFrame row of the alert point) or (None) if no alert needed
        """
        try:
            # Filter points exceeding threshold (80%)
            exceeding_points = results[results['loading_percentage'] >= 80]
            
            if not exceeding_points.empty:
                # Get the latest exceeding point
                alert_point = exceeding_points.iloc[-1]
                logger.info(f"Found alert point at {alert_point.name} with loading {alert_point['loading_percentage']:.1f}%")
                return alert_point
                
            logger.info("No points exceed the alert threshold")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting alert point: {str(e)}")
            return None
    
    def _create_deep_link(self, start_date: date, alert_time: datetime, transformer_id: str) -> str:
        """Create deep link back to app with context"""
        params = {
            'view': 'alert',
            'id': transformer_id,
            'start': start_date.isoformat() if start_date else None,
            'alert_time': alert_time.isoformat() if alert_time else None
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
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
    
    def check_and_send_alerts(
        self,
        results_df: pd.DataFrame,
        start_date: Optional[date] = None,
        alert_time: Optional[datetime] = None,
        recipient: str = None
    ) -> bool:
        """
        Check loading conditions and send alert if needed
        """
        if not self.email_enabled:
            logger.warning("Email alerts disabled - skipping alert check")
            return False

        try:
            # Select the alert point
            alert_point = self._select_alert_point(results_df)
            
            if alert_point is None:
                logger.info("No alert conditions met")
                return False
            
            logger.info(f"Alert condition met: {alert_point['loading_percentage']:.1f}% loading")
            
            # Get alert status and color
            status, color = get_alert_status(alert_point['loading_percentage'])
            
            # Create deep link
            deep_link = self._create_deep_link(
                start_date,
                alert_time or alert_point.name,
                alert_point['transformer_id']
            )
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Transformer Loading Alert - {alert_point['loading_percentage']:.1f}% Loading"
            msg['From'] = self.default_recipient  # Use default_recipient as From address
            msg['To'] = recipient or self.default_recipient
            
            # Create HTML content
            html_content = self._create_email_content(
                alert_point, status, color, deep_link
            )
            msg.attach(MIMEText(html_content, 'html'))
            
            try:
                # Send email using Gmail API
                service = build('gmail', 'v1', credentials=self.gmail_creds)
                message = {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}
                service.users().messages().send(userId='me', body=message).execute()
                logger.info("Alert email sent successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error in check_and_send_alerts: {str(e)}")
            return False
