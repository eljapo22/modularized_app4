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
from pathlib import Path
import json
from google.auth.transport.requests import Request

def debug_print_secrets():
    """Debug function to print available secrets"""
    st.write("Available secrets:", list(st.secrets.keys()))
    if "GMAIL_TOKEN" in st.secrets:
        token_info = st.secrets["GMAIL_TOKEN"]
        st.write("Token type:", type(token_info))
        if isinstance(token_info, str):
            try:
                parsed = json.loads(token_info)
                st.write("Token parsed successfully")
            except Exception as e:
                st.write("Token parse error:", str(e))
    else:
        st.write("GMAIL_TOKEN not found in secrets")

def debug_token_info(token_info):
    """Debug helper to safely print token info"""
    if isinstance(token_info, str):
        st.write("Token is a string, length:", len(token_info))
        try:
            parsed = json.loads(token_info)
            st.write("Token parsed successfully")
            # Show token structure without sensitive values
            safe_info = {
                k: "..." if k in ["token", "refresh_token", "client_secret"] 
                else v for k, v in parsed.items()
            }
            st.write("Token structure:", safe_info)
        except json.JSONDecodeError as e:
            st.write("Token parse error:", str(e))
    elif isinstance(token_info, dict):
        st.write("Token is already a dictionary")
        # Show token structure without sensitive values
        safe_info = {
            k: "..." if k in ["token", "refresh_token", "client_secret"] 
            else v for k, v in token_info.items()
        }
        st.write("Token structure:", safe_info)
    else:
        st.write("Token is unexpected type:", type(token_info))

# Gmail API configuration
def is_running_in_cloud():
    """Check if we're running in Streamlit Cloud"""
    in_cloud = st.secrets.get("GMAIL_TOKEN") is not None
    st.write("Running in cloud:", in_cloud)
    return in_cloud

if is_running_in_cloud():
    try:
        debug_print_secrets()
        from config.cloud_config import DEFAULT_RECIPIENT
        CREDENTIALS_PATH = None
        TOKEN_PATH = None
        st.write("Cloud config loaded successfully")
    except Exception as e:
        st.warning(f"Email alerts are disabled: {str(e)}")
        DEFAULT_RECIPIENT = None
        CREDENTIALS_PATH = None
        TOKEN_PATH = None
else:
    # Use repository-relative paths for local development
    CREDENTIALS_PATH = Path(__file__).parent.parent / 'config' / 'credentials.json'
    TOKEN_PATH = Path(__file__).parent.parent / 'config' / 'token.json'
    DEFAULT_RECIPIENT = "jhnapo2213@gmail.com"
    st.write("Running in local mode")

def get_gmail_service():
    """Initialize Gmail API service"""
    try:
        # First check if we have token in Streamlit secrets
        st.write("Checking for GMAIL_TOKEN in secrets...")
        if "GMAIL_TOKEN" in st.secrets:
            st.write("Found GMAIL_TOKEN in secrets")
            try:
                # Get and parse token from secrets
                token_info = st.secrets["GMAIL_TOKEN"]
                debug_token_info(token_info)
                
                if isinstance(token_info, str):
                    st.write("Parsing token string...")
                    try:
                        token_info = json.loads(token_info)
                        st.write("Token parsed successfully")
                    except json.JSONDecodeError as e:
                        st.error(f"Failed to parse token: {str(e)}")
                        return None
                
                st.write("Creating credentials object...")
                try:
                    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                    st.write("Credentials created successfully")
                except Exception as e:
                    st.error(f"Failed to create credentials: {str(e)}")
                    return None
                
                if not creds:
                    st.error("Credentials object is None")
                    return None
                    
                if not creds.valid:
                    st.write("Credentials are invalid, attempting refresh...")
                    if creds.expired and creds.refresh_token:
                        try:
                            creds.refresh(Request())
                            st.write("Credentials refreshed successfully")
                        except Exception as e:
                            st.error(f"Failed to refresh credentials: {str(e)}")
                            return None
                    else:
                        st.error("Credentials are invalid and cannot be refreshed")
                        return None
                
                # Build and return Gmail service
                st.write("Building Gmail service...")
                try:
                    service = build('gmail', 'v1', credentials=creds)
                    st.write("Gmail service built successfully")
                    return service
                except Exception as e:
                    st.error(f"Failed to build Gmail service: {str(e)}")
                    return None
                    
            except Exception as e:
                st.error(f"Error with Gmail token: {str(e)}")
                return None
        else:
            st.write("GMAIL_TOKEN not found in secrets, falling back to local mode")
            # Local development mode
            token_path = Path(__file__).parent.parent / 'config' / 'token.json'
            creds_path = Path(__file__).parent.parent / 'config' / 'credentials.json'
            
            if os.path.exists(token_path):
                try:
                    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                except Exception as e:
                    st.error(f"Error loading token file: {str(e)}")
                    return None

            if not creds or not creds.valid:
                if not os.path.exists(creds_path):
                    st.error(f"Credentials file not found at {creds_path}")
                    return None
                    
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            # Build and return Gmail service
            try:
                service = build('gmail', 'v1', credentials=creds)
                return service
            except Exception as e:
                st.error(f"Error building Gmail service: {str(e)}")
                return None

    except Exception as e:
        st.error(f"Error in get_gmail_service: {str(e)}")
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
