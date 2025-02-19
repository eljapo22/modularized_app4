"""
Cloud-specific alert service implementation using Streamlit secrets and Gmail API
"""

import os
import json
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

from app.services.alert_service import (
    AlertService, 
    extract_feeder,
    generate_dashboard_link,
    check_alert_condition
)
from app.config.cloud_config import GmailConfig, SCOPES

class CloudAlertService(AlertService):
    """Cloud implementation of alert service using Streamlit secrets"""
    
    def __init__(self):
        """Initialize cloud alert service with Streamlit secrets"""
        try:
            self.token_info = GmailConfig.get_token()
            self.default_recipient = GmailConfig.get_recipient()
            if not self.token_info or not self.default_recipient:
                raise ValueError("Failed to initialize Gmail configuration")
        except Exception as e:
            st.error(f"Failed to initialize cloud alert service: {str(e)}")
            self.token_info = None
            self.default_recipient = None
        
    def _get_gmail_service(self):
        """Initialize Gmail API service using cloud token"""
        try:
            creds = Credentials.from_authorized_user_info(self.token_info, SCOPES)
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            st.error(f"Failed to initialize Gmail service: {str(e)}")
            return None
            
    def _get_status_color(self, status: str) -> str:
        """Get color for status."""
        colors = {
            'Critical': '#dc3545',
            'Overloaded': '#fd7e14',
            'Warning': '#ffc107',
            'Pre-Warning': '#6f42c1',
            'Normal': '#198754'
        }
        return colors.get(status, '#6c757d')

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        emojis = {
            'Critical': '🔴',
            'Overloaded': '🟠',
            'Warning': '🟡',
            'Pre-Warning': '🟣',
            'Normal': '🟢'
        }
        return emojis.get(status, '⚪')

    def _create_email_content(self, alert_data: pd.DataFrame, date: datetime, hour: int) -> str:
        """Create HTML content for alert email"""
        html = ""
        
        for _, row in alert_data.iterrows():
            transformer_id = row['transformer_id']
            feeder = extract_feeder(transformer_id)
            status = row['load_range']
            loading = row['loading_percentage']
            color = self._get_status_color(status)
            emoji = self._get_status_emoji(status)
            dashboard_url = generate_dashboard_link(transformer_id, feeder, date, hour)
            
            html += f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2f4f4f;">Transformer Loading Alert</h2>
                <p>Alert detected for transformer <strong>{transformer_id}</strong></p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
                    <p style="color: {color};">
                        {emoji} Status: {status}<br>
                        Loading: {loading:.1f}%
                    </p>
                    
                    <h3>Readings:</h3>
                    <ul>
                        <li>Power: {row.get('power_kw', 'N/A'):.1f} kW</li>
                        <li>Current: {row.get('current_a', 'N/A'):.1f} A</li>
                        <li>Voltage: {row.get('voltage_v', 'N/A'):.1f} V</li>
                        <li>Power Factor: {row.get('power_factor', 'N/A'):.2f}</li>
                    </ul>
                    
                    <p>Time: {date.strftime('%Y-%m-%d')} {hour:02d}:00</p>
                </div>
                
                <p>
                    <a href="{dashboard_url}" 
                       style="background-color: #0d6efd; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        View in Dashboard
                    </a>
                </p>
            </body>
            </html>
            """
        
        return html
        
    def send_alert(self, alert_data: pd.DataFrame, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send alert email using Gmail API"""
        try:
            service = self._get_gmail_service()
            if not service:
                return False
                
            if recipients is None:
                recipients = [self.default_recipient]
                
            message = MIMEMultipart('alternative')
            message['to'] = ', '.join(recipients)
            
            # Get the first transformer's status for the subject line
            first_alert = alert_data.iloc[0]
            message['subject'] = f"Transformer Alert: {first_alert['transformer_id']} - {first_alert['load_range']}"
            
            html_content = self._create_email_content(alert_data, date, hour)
            message.attach(MIMEText(html_content, 'html'))
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            service.users().messages().send(userId='me', body={'raw': raw}).execute()
            
            return True
        except Exception as e:
            st.error(f"Failed to send alert email: {str(e)}")
            return False
            
    def test_alert(self, transformer_id: str, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send test alert email"""
        test_data = pd.DataFrame({
            'transformer_id': [transformer_id],
            'load_range': ['Warning'],
            'loading_percentage': [99.9],
            'power_kw': [75.5],
            'current_a': [150.2],
            'voltage_v': [240.1],
            'power_factor': [0.95]
        })
        return self.send_alert(test_data, date, hour, recipients)
        
    def process_alerts(self, results_df: pd.DataFrame, selected_date: datetime, selected_hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Process alerts and send if conditions are met"""
        alerts = check_alert_condition(results_df, selected_hour)
        if alerts is not None:
            return self.send_alert(alerts, selected_date, selected_hour, recipients)
        return True  # No alerts needed to be sent
