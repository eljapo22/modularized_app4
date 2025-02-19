"""
Local alert service implementation using OAuth flow and local credentials
"""

import os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime
import json

from app.services.alert_service import (
    AlertService, 
    get_status_color, 
    extract_feeder,
    generate_dashboard_link,
    check_alert_condition
)
from app.config.constants import SCOPES

class LocalAlertService(AlertService):
    """Local implementation of alert service using OAuth flow"""
    
    def __init__(self):
        """Initialize local alert service with file paths"""
        self.credentials_path = Path(__file__).parent.parent / 'config' / 'credentials.json'
        self.token_path = Path(__file__).parent.parent / 'config' / 'token.json'
        self.default_recipient = "jhnapo2213@gmail.com"  # Local development recipient
        
        # Verify credentials exist
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Gmail credentials not found at {self.credentials_path}. "
                "Please create this file for local development."
            )
            
    def _get_gmail_service(self):
        """Initialize Gmail API service using local OAuth flow"""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            with open(self.token_path, 'r') as token:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                
        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                
        return build('gmail', 'v1', credentials=creds)
            
    def _create_email_content(self, alert_data: pd.DataFrame, date: datetime, hour: int) -> str:
        """Create HTML content for alert email"""
        html = f"""
        <html>
        <head>
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .critical {{ color: #FF0000; }}
                .overloaded {{ color: #FFA500; }}
                .warning {{ color: #FFFF00; }}
            </style>
        </head>
        <body>
            <h2>Transformer Loading Alert (Local Development)</h2>
            <p>The following transformers require attention:</p>
            <table>
                <tr>
                    <th>Transformer</th>
                    <th>Loading Status</th>
                    <th>Loading %</th>
                    <th>Dashboard Link</th>
                </tr>
        """
        
        for _, row in alert_data.iterrows():
            transformer_id = row['transformer_id']
            feeder = extract_feeder(transformer_id)
            status = row['loading_status']
            loading = row['loading_percentage']
            color = get_status_color(status)
            dashboard_url = generate_dashboard_link(transformer_id, feeder, date, hour)
            
            html += f"""
                <tr>
                    <td>{transformer_id}</td>
                    <td style="color: {color}">{status}</td>
                    <td>{loading:.1f}%</td>
                    <td><a href="{dashboard_url}">View Details</a></td>
                </tr>
            """
            
        html += """
            </table>
            <p><em>This is a local development email.</em></p>
        </body>
        </html>
        """
        return html
        
    def send_alert(self, alert_data: pd.DataFrame, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send alert email using local Gmail API credentials"""
        try:
            service = self._get_gmail_service()
            
            if recipients is None:
                recipients = [self.default_recipient]
                
            message = MIMEMultipart('alternative')
            message['to'] = ', '.join(recipients)
            message['subject'] = f'[LOCAL] Transformer Loading Alert - {date.strftime("%Y-%m-%d")} Hour {hour}'
            
            html_content = self._create_email_content(alert_data, date, hour)
            message.attach(MIMEText(html_content, 'html'))
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            service.users().messages().send(userId='me', body={'raw': raw}).execute()
            
            return True
        except Exception as e:
            print(f"Failed to send local alert email: {str(e)}")
            return False
            
    def test_alert(self, transformer_id: str, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Send test alert email"""
        test_data = pd.DataFrame({
            'transformer_id': [transformer_id],
            'loading_status': ['Test Alert (Local)'],
            'loading_percentage': [99.9]
        })
        return self.send_alert(test_data, date, hour, recipients)
        
    def process_alerts(self, results_df: pd.DataFrame, selected_date: datetime, selected_hour: int, recipients: Optional[List[str]] = None) -> bool:
        """Process alerts and send if conditions are met"""
        alerts = check_alert_condition(results_df, selected_hour)
        if alerts is not None:
            return self.send_alert(alerts, selected_date, selected_hour, recipients)
        return True  # No alerts needed to be sent
