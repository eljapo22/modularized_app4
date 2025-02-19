"""
Cloud-specific alert service implementation using Amazon SES via SMTP
"""

import os
import json
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

from app.services.alert_service import (
    AlertService, 
    extract_feeder,
    generate_dashboard_link,
    check_alert_condition,
    get_loading_status
)
from app.config.cloud_config import EmailConfig

class CloudAlertService(AlertService):
    """Cloud-specific implementation of alert service using Amazon SES"""
    
    def __init__(self):
        """Initialize the cloud alert service"""
        self.smtp_settings = EmailConfig.get_smtp_settings()
        self.sender_email = EmailConfig.get_sender()
        self.default_recipient = EmailConfig.get_recipient()
        
        if not EmailConfig.is_configured():
            st.warning("Email service is not fully configured. Alerts will not be sent.")
            
    def _get_smtp_connection(self):
        """Create an SMTP connection with TLS"""
        try:
            if not self.smtp_settings:
                st.error("Cannot create SMTP connection: missing settings")
                return None
                
            # Create secure SSL/TLS context
            context = ssl.create_default_context()
            
            # Connect to SMTP server
            server = smtplib.SMTP(
                self.smtp_settings['host'],
                self.smtp_settings['port']
            )
            server.starttls(context=context)
            server.login(
                self.smtp_settings['username'],
                self.smtp_settings['password']
            )
            
            return server
            
        except Exception as e:
            st.error(f"Failed to create SMTP connection: {str(e)}")
            return None
            
    def _get_status_color(self, status: str) -> str:
        """Get HTML color for status."""
        return {
            'Critical': '#FF0000',      # Red
            'Overloaded': '#FFA500',    # Orange
            'Warning': '#FFD700',       # Gold
            'Pre-Warning': '#FFFF00',   # Yellow
            'Normal': '#90EE90'         # Light Green
        }.get(status, '#FFFFFF')        # White as default
            
    def process_alerts(self, results_df: pd.DataFrame, selected_date: datetime, selected_hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Process transformer data and send alerts if conditions are met"""
        try:
            alert_data = check_alert_condition(results_df, selected_hour)
            if alert_data is not None and not alert_data.empty:
                return self.send_alert(alert_data, selected_date, selected_hour, recipients)
            return True
        except Exception as e:
            st.error(f"Failed to process alerts: {str(e)}")
            return False

    def test_alert(self, transformer_id: str, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send a test alert email"""
        try:
            test_data = pd.DataFrame({
                'transformer_id': [transformer_id],
                'loading_percentage': [120.0],  # Critical level for testing
                'voltage': [230.0],
                'current': [100.0]
            })
            return self.send_alert(test_data, date, hour, recipients)
        except Exception as e:
            st.error(f"Failed to send test alert: {str(e)}")
            return False

    def send_alert(self, alert_data: pd.DataFrame, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send alert email with transformer loading data"""
        if not self.smtp_settings or not self.sender_email:
            st.error("Email configuration is incomplete. Cannot send alerts.")
            return False

        try:
            server = self._get_smtp_connection()
            if not server:
                return False

            recipient_list = recipients if recipients else [self.default_recipient]
            
            for _, row in alert_data.iterrows():
                transformer_id = row['transformer_id']
                loading = row['loading_percentage']
                status = get_loading_status(loading)
                color = self._get_status_color(status)
                feeder = extract_feeder(transformer_id)
                
                subject = f"Transformer Alert: {transformer_id} - {status}"
                html_content = f"""
                <h2>Transformer Loading Alert</h2>
                <p><strong>Transformer:</strong> {transformer_id}</p>
                <p><strong>Feeder:</strong> {feeder}</p>
                <p><strong>Date:</strong> {date.strftime('%Y-%m-%d')}</p>
                <p><strong>Time:</strong> {hour}:00</p>
                <p><strong>Loading:</strong> <span style="color: {color}">{loading:.1f}%</span></p>
                <p><strong>Status:</strong> <span style="color: {color}">{status}</span></p>
                <p><a href="{generate_dashboard_link(transformer_id, feeder, date, hour)}">View in Dashboard</a></p>
                """

                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.sender_email
                msg['To'] = ', '.join(recipient_list)
                msg.attach(MIMEText(html_content, 'html'))

                server.send_message(msg)

            server.quit()
            st.success("Alert emails sent successfully!")
            return True

        except Exception as e:
            st.error(f"Failed to send alert email: {str(e)}")
            return False
