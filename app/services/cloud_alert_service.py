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
            self.gmail_user = st.secrets["gmail"]["username"]
            self.gmail_password = st.secrets["gmail"]["password"]
            self.gmail_creds = Credentials.from_authorized_user_info(st.secrets["gmail"])
            self.email_enabled = True
            logger.info("Email alerts enabled")
        except Exception as e:
            self.gmail_creds = None
            self.email_enabled = False
            logger.warning("Email alerts disabled: Gmail credentials not found in secrets")
    
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

    def select_alert_point(self, results: pd.DataFrame) -> Tuple[Optional[pd.Series], Optional[datetime]]:
        """
        Find the latest point that exceeds the threshold in the date range.
        
        Args:
            results: DataFrame with transformer data
            
        Returns:
            tuple: (DataFrame row of the alert point, timestamp of the alert) or (None, None) if no alert needed
        """
        try:
            # Filter points exceeding threshold (80%)
            exceeding_points = results[results['loading_percentage'] >= 80]
            
            if not exceeding_points.empty:
                # Get the latest exceeding point
                alert_point = exceeding_points.iloc[-1]
                alert_time = alert_point.name  # Get timestamp from index
                logger.info(f"Found alert point at {alert_time} with loading {alert_point['loading_percentage']:.1f}%")
                return alert_point, alert_time
                
            logger.info("No points exceed the alert threshold")
            return None, None
            
        except Exception as e:
            logger.error(f"Error selecting alert point: {str(e)}")
            return None, None
    
    def _create_email_content(self, data: pd.Series, alert_time: datetime, start_date: date) -> str:
        """
        Create HTML content for alert email with context
        
        Args:
            data: Series with transformer data at alert point
            alert_time: Timestamp of the alert point
            start_date: Start date of the analysis range
        """
        transformer_id = data['transformer_id']
        loading_pct = data['loading_percentage']
        status, color, emoji = self._get_status_color(loading_pct)
        
        # Create deep link back to app with context
        deep_link = f"{self.app_url}?view=alert&id={transformer_id}&start={start_date}&alert_time={alert_time.isoformat()}"
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2f4f4f;">Transformer Loading Alert {emoji}</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: {color};">Status: {status}</h3>
                <p><strong>Transformer:</strong> {transformer_id}</p>
                <p><strong>Loading:</strong> {loading_pct:.1f}%</p>
                <p><strong>Alert Time:</strong> {alert_time.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Analysis Start:</strong> {start_date.strftime('%Y-%m-%d')}</p>
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
        recipient: str = "jhnapo2213@gmail.com"
    ) -> bool:
        """
        Check loading conditions and send alert if needed
        
        Args:
            results_df: DataFrame with transformer data
            start_date: Start date of the analysis range (optional)
            alert_time: Specific time to check for alert (optional)
            recipient: Email recipient
            
        Returns:
            bool: True if alert was sent or would have been sent, False otherwise
        """
        try:
            # If no alert_time provided, find the latest exceeding point
            if alert_time is None:
                alert_point, alert_time = self.select_alert_point(results_df)
                if alert_point is None:
                    logger.info("No alert conditions found")
                    return False
            else:
                # Use the specific time point
                alert_point = results_df.loc[alert_time]
            
            # If email is not enabled, just log the alert
            if not self.email_enabled:
                logger.warning("Alert would have been sent, but email is not enabled")
                st.warning("⚠️ High loading detected. Email alerts are currently disabled.")
                return True
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Transformer Loading Alert - {alert_point['loading_percentage']:.1f}% Loading"
            msg['From'] = self.gmail_user
            msg['To'] = recipient
            
            # Create HTML content
            html_content = self._create_email_content(
                alert_point,
                alert_time,
                start_date or alert_time.date()
            )
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.gmail_user, self.gmail_password)
                smtp.send_message(msg)
            
            logger.info("Alert email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in alert system: {str(e)}")
            if self.email_enabled:
                st.error("Failed to send alert email. Check the logs for details.")
            return False
