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
    
    def _create_email_content(self, data: pd.DataFrame, date: datetime, hour: int) -> str:
        """Create HTML content for alert email"""
        transformer_id = data['transformer_id'].iloc[0]
        loading_pct = data['loading_percentage'].iloc[-1]
        status, color, emoji = self._get_status_color(loading_pct)
        
        # Create deep link back to app
        deep_link = f"{self.app_url}?view=alert&id={transformer_id}"
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2f4f4f;">Transformer Loading Alert {emoji}</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: {color};">Status: {status}</h3>
                <p><strong>Transformer:</strong> {transformer_id}</p>
                <p><strong>Loading:</strong> {loading_pct:.1f}%</p>
                <p><strong>Time:</strong> {date.strftime('%Y-%m-%d')} {hour:02d}:00</p>
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h4>Detailed Readings:</h4>
                <ul>
                    <li>Power: {data['power_kw'].iloc[-1]:.1f} kW</li>
                    <li>Current: {data['current_a'].iloc[-1]:.1f} A</li>
                    <li>Voltage: {data['voltage_v'].iloc[-1]:.1f} V</li>
                    <li>Power Factor: {data['power_factor'].iloc[-1]:.2f}</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{deep_link}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View in Dashboard
                </a>
            </div>
            
            <p style="color: #6c757d; font-size: 12px; text-align: center;">
                This is an automated alert from your Transformer Loading Analysis System.
            </p>
        </div>
        """
        return html
    
    def create_email_content(self, transformer_data: pd.DataFrame, date: datetime, hour: int) -> str:
        """Create HTML email content with transformer data"""
        
        html_parts = []
        for _, row in transformer_data.iterrows():
            transformer_id = row['transformer_id']
            loading_pct = row['loading_percentage']
            status, color = get_alert_status(loading_pct)
            emoji = get_status_emoji(status)
            
            # Create deep link back to app
            alert_link = f"{self.app_url}?view=alert&id={transformer_id}"
            
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
    
    def check_and_send_alerts(self, results_df: pd.DataFrame, date: datetime, hour: int, recipient: str) -> bool:
        """
        Check transformer data and send alerts if needed
        
        Args:
            results_df: DataFrame with transformer readings
            date: Date of the readings
            hour: Hour of the readings
            recipient: Email recipient
            
        Returns:
            bool: True if alerts processed successfully
        """
        try:
            # Filter transformers above threshold
            alerts_df = results_df[results_df['loading_percentage'] >= 80.0].copy()
            
            if alerts_df.empty:
                logger.info("No alerts needed")
                return True
            
            # Send alert email
            return self.send_alert(alerts_df, date, hour, recipient)
            
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
            return False
    
    def check_and_send_alerts_smtp(self, results_df: pd.DataFrame, date: datetime, hour: int, recipient: str) -> bool:
        """
        Check loading conditions and send alert if needed
        
        Args:
            results_df: DataFrame with transformer data
            date: Date of the data
            hour: Hour of the data
            recipient: Email recipient
            
        Returns:
            bool: True if alert was sent or would have been sent, False otherwise
        """
        try:
            loading_pct = results_df['loading_percentage'].iloc[-1]
            
            # Check if loading is above warning threshold
            if loading_pct >= 80:
                logger.info(f"High loading detected ({loading_pct:.1f}%)")
                
                # If email is not enabled, just log the alert
                if not self.email_enabled:
                    logger.warning("Alert would have been sent, but email is not enabled")
                    st.warning("⚠️ High loading detected. Email alerts are currently disabled.")
                    return True
                
                # Create and send email
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"Transformer Loading Alert - {loading_pct:.1f}% Loading"
                msg['From'] = self.gmail_user
                msg['To'] = recipient
                
                # Create HTML content
                html_content = self._create_email_content(results_df, date, hour)
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(self.gmail_user, self.gmail_password)
                    smtp.send_message(msg)
                
                logger.info("Alert email sent successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in alert system: {str(e)}")
            if self.email_enabled:
                st.error("Failed to send alert email. Check the logs for details.")
            return False
