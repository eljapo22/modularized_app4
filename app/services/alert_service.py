"""
Alert and email services for the Transformer Loading Analysis Application
"""

import os
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from config.constants import SCOPES
import pandas as pd
from datetime import datetime

# Gmail API configuration
if os.getenv("STREAMLIT_CLOUD"):
    from config.cloud_config import GMAIL_CREDENTIALS, GMAIL_TOKEN, DEFAULT_RECIPIENT
    CREDENTIALS_PATH = None
    TOKEN_PATH = None
else:
    CREDENTIALS_PATH = 'C:\\Users\\JohnApostolo\\CascadeProjects\\credentials.json'
    TOKEN_PATH = 'C:\\Users\\JohnApostolo\\CascadeProjects\\token.json'
    DEFAULT_RECIPIENT = "jhnapo2213@gmail.com"  # Updated email address

def get_gmail_service():
    """Initialize Gmail API service"""
    try:
        creds = None
        if os.getenv("STREAMLIT_CLOUD"):
            if GMAIL_CREDENTIALS and GMAIL_TOKEN:
                creds = Credentials.from_authorized_user_info(eval(GMAIL_TOKEN), SCOPES)
        else:
            # Check if we have valid token
            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if os.getenv("STREAMLIT_CLOUD"):
                if not GMAIL_CREDENTIALS:
                    st.error("Gmail credentials not found in environment variables")
                    return None
                creds_info = eval(GMAIL_CREDENTIALS)
                flow = InstalledAppFlow.from_client_config(creds_info, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                if not os.path.exists(CREDENTIALS_PATH):
                    st.error(f"Credentials file not found at {CREDENTIALS_PATH}")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for future use
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
                    
        service = build('gmail', 'v1', credentials=creds)
        return service
        
    except Exception as e:
        st.error(f"Error initializing Gmail service: {str(e)}")
        return None

def get_status_color(status):
    """Get color for status"""
    colors = {
        'Critical': '#ff0000',
        'Overloaded': '#ffa500',
        'Warning': '#ffff00',
        'Pre-Warning': '#90EE90',
        'Normal': '#00ff00'
    }
    return colors.get(status, '#000000')

def create_alert_email_content(alert_data, date, hour, dashboard_link):
    """Create HTML content for alert email"""
    html_content = f"""
    <html>
    <head>
        <style>
            .status {{
                padding: 5px;
                border-radius: 3px;
                color: white;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .view-analysis {{
                display: inline-block;
                margin-top: 15px;
                padding: 10px 20px;
                background-color: #0d6efd;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }}
            .view-analysis:hover {{
                background-color: #0b5ed7;
            }}
            .timestamp {{
                font-family: monospace;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h2>Transformer Loading Alert</h2>
        <p>Date: {date}</p>
        <p>Hour: {hour:02d}:00</p>
        <p class="timestamp">Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table>
            <tr>
                <th>Transformer ID</th>
                <th>Loading Status</th>
                <th>Loading Percentage</th>
                <th>Power (kW)</th>
                <th>Size (kVA)</th>
            </tr>
    """
    
    for _, row in alert_data.iterrows():
        status_color = get_status_color(row['load_range'])
        html_content += f"""
            <tr>
                <td>{row['transformer_id']}</td>
                <td><span class="status" style="background-color: {status_color}">{row['load_range']}</span></td>
                <td>{row['loading_percentage']:.1f}%</td>
                <td>{row['power_kw']:.1f}</td>
                <td>{row['size_kva']:.1f}</td>
            </tr>
        """
    
    html_content += f"""
        </table>
        <p>Click the button below to view the latest analysis:</p>
        <a href="{dashboard_link}" class="view-analysis">View Detailed Analysis</a>
        <p style="color: #666; margin-top: 20px; font-size: 0.9em;">Note: This link will show the most current data for the selected transformer.</p>
    </body>
    </html>
    """
    
    return html_content

def send_alert_email(alert_data, date, hour, recipients=None):
    """Send alert email with dashboard link"""
    try:
        if recipients is None:
            recipients = [DEFAULT_RECIPIENT]
        
        service = get_gmail_service()
        if not service:
            raise Exception("Could not initialize Gmail service")
            
        # Generate dashboard link
        transformer_id = alert_data['transformer_id'].iloc[0]
        feeder = extract_feeder(transformer_id)
        dashboard_link = generate_dashboard_link(
            transformer_id,
            feeder,
            date,
            hour
        )
        
        # Create email content
        html_content = create_alert_email_content(alert_data, date, hour, dashboard_link)
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = f'Transformer Loading Alert - {date} {hour:02d}:00'
        message['From'] = DEFAULT_RECIPIENT
        message['To'] = ', '.join(recipients)
        message.attach(MIMEText(html_content, 'html'))
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def process_alerts(results_df, selected_date, selected_hour, recipients=None):
    """Process alerts and send emails if conditions are met"""
    try:
        # Check for alert conditions
        alert_data = check_alert_condition(results_df, selected_hour)
        
        # Get transformer ID from results
        transformer_id = results_df['transformer_id'].iloc[0]
        feeder = extract_feeder(transformer_id)
        
        if alert_data is not None and not alert_data.empty:
            # Send alert email with dashboard link
            if send_alert_email(alert_data, selected_date, selected_hour, recipients):
                return True
            else:
                raise Exception("Failed to send alert email")
        else:
            # Create a sample alert for testing
            sample_data = pd.DataFrame({
                'transformer_id': [transformer_id],
                'load_range': ['Warning'],
                'loading_percentage': [80.4],
                'power_kw': [55.0],
                'size_kva': [75.0]
            })
            if send_alert_email(sample_data, selected_date, selected_hour, recipients):
                return True
            else:
                raise Exception("Failed to send sample alert email")
                
    except Exception as e:
        raise Exception(f"Error processing alerts: {str(e)}")

def test_alert_system(transformer_id: str, date, hour: int, recipients=None):
    """Test the alert system by sending a test alert"""
    try:
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'transformer_id': [transformer_id],
            'load_range': ['Warning'],
            'loading_percentage': [80.4],
            'power_kw': [55.0],
            'size_kva': [75.0]
        })
        
        # Send test alert
        if send_alert_email(sample_data, date, hour, recipients):
            return True
        else:
            raise Exception("Failed to send test alert email")
            
    except Exception as e:
        raise Exception(f"Error testing alert system: {str(e)}")

def extract_feeder(transformer_id: str) -> str:
    """Extract feeder ID from transformer ID"""
    return transformer_id.split('_')[0] if '_' in transformer_id else 'feeder1'

def generate_dashboard_link(transformer_id: str, feeder: str, date, hour: int) -> str:
    """Generate link to dashboard with pre-filled parameters"""
    # Use the same port as the running app
    base_url = "http://localhost:8501"
    
    # Format parameters - ensure feeder has correct format (e.g., "Feeder 1" not "feeder1")
    feeder_formatted = f"Feeder {feeder.split('feeder')[-1]}" if feeder.lower().startswith('feeder') else feeder
    
    params = {
        "transformer": transformer_id,
        "feeder": feeder_formatted,
        "date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else date,
        "hour": hour,
        "view": "full"  # This triggers full view mode in the same app
    }
    
    # Build query string
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    
    return f"{base_url}/?{param_str}"

def check_alert_condition(results_df, selected_hour):
    """
    Check for alert conditions at the selected hour
    
    Returns DataFrame with rows that meet alert conditions, or None if no alerts
    """
    if results_df is None or results_df.empty:
        return None
        
    try:
        # Convert selected_hour to integer if it's a datetime.time
        if hasattr(selected_hour, 'hour'):
            selected_hour = selected_hour.hour
            
        # Filter data for the selected hour
        hour_data = results_df[results_df['timestamp'].dt.hour == selected_hour].copy()
        
        if hour_data.empty:
            return None
            
        # Check for any loading percentages that meet alert conditions
        alert_data = hour_data[hour_data['loading_percentage'] >= 50]  # Pre-Warning threshold
        
        if alert_data.empty:
            return None
            
        # Add load range based on loading percentage
        alert_data['load_range'] = alert_data['loading_percentage'].apply(lambda x: 
            'Critical' if x >= 120 else
            'Overloaded' if x >= 100 else
            'Warning' if x >= 80 else
            'Pre-Warning' if x >= 50 else
            'Normal'
        )
        
        return alert_data.sort_values('loading_percentage', ascending=False)
        
    except Exception as e:
        st.error(f"Error checking alert conditions: {str(e)}")
        return None
