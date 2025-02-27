"""
Cloud-specific alert service for the Transformer Loading Analysis Application
"""
import logging
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Optional, Dict, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
        self.app_url = st.secrets.get("APP_URL", "https://transformer-dashboard.streamlit.app")
        self.email = st.secrets.get("DEFAULT_EMAIL", "jhnapo2213@gmail.com")
        self.app_password = st.secrets.get("GMAIL_APP_PASSWORD")
        self.email_enabled = self.app_password is not None
        
        if not self.email_enabled:
            logger.warning("Email alerts disabled: Gmail app password not found in secrets")
        else:
            logger.info("Email alerts enabled")

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

    def _select_alert_point(self, results_df: pd.DataFrame, end_date=None, selected_hour=None) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """Select the points to alert on - returns (max_loading_point, end_point)"""
        try:
            # Find the highest loading percentage
            max_loading_idx = results_df['loading_percentage'].idxmax()
            max_loading = results_df.loc[max_loading_idx]
            
            # Log the max loading found
            logger.info(f"Found max loading: {max_loading['loading_percentage']:.1f}% at {max_loading.name}")
            
            # Find the end-date loading percentage if end_date is provided
            end_point = None
            if end_date is not None:
                # Convert end_date to the correct format if it's a string
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date).date()
                
                # Set the target time to the end date with the selected hour
                target_time = pd.Timestamp(
                    year=end_date.year, 
                    month=end_date.month,
                    day=end_date.day,
                    hour=selected_hour or 12  # Default to noon if hour not specified
                )
                
                # Convert index to datetime if it's not already
                if not isinstance(results_df.index, pd.DatetimeIndex):
                    results_df.index = pd.to_datetime(results_df.index)
                
                # Find closest time point
                results_df['time_diff'] = abs(results_df.index - target_time)
                end_idx = results_df['time_diff'].idxmin()
                end_point = results_df.loc[end_idx]
                
                logger.info(f"Found end-date loading: {end_point['loading_percentage']:.1f}% at {end_point.name}")
            
            # Only alert if either max loading or end-date loading is high enough
            alert_criteria_met = False
            
            if max_loading['loading_percentage'] >= 80:
                alert_criteria_met = True
                logger.info(f"Alert criteria met: Max loading {max_loading['loading_percentage']:.1f}% >= 80%")
            elif end_point is not None and end_point['loading_percentage'] >= 80:
                alert_criteria_met = True
                logger.info(f"Alert criteria met: End-date loading {end_point['loading_percentage']:.1f}% >= 80%")
            
            if alert_criteria_met:
                return max_loading, end_point
            else:
                logger.info(f"Max loading {max_loading['loading_percentage']:.1f}% and end-date loading " + 
                          (f"{end_point['loading_percentage']:.1f}%" if end_point is not None else "N/A") + 
                          " below alert threshold (80%)")
                st.info(f"🔍 Maximum ({max_loading['loading_percentage']:.1f}%) and end-date loading " + 
                       (f"({end_point['loading_percentage']:.1f}%)" if end_point is not None else "(N/A)") + 
                       " are below alert threshold (80%)")
                return None, None
                
        except Exception as e:
            logger.error(f"Error selecting alert points: {str(e)}")
            return None, None

    def _create_email_content(self, max_data: pd.Series, end_data: Optional[pd.Series], 
                            max_status: str, max_color: str, deep_link: str) -> str:
        """
        Create HTML content for alert email with context
        
        Args:
            max_data: Series with transformer data at max loading point
            end_data: Series with transformer data at end date point (may be None)
            max_status: Status of the max loading alert
            max_color: Color of the max loading alert
            deep_link: Deep link back to app
            
        Returns:
            str: HTML content of the email
        """
        transformer_id = max_data['transformer_id']
        max_loading_pct = max_data['loading_percentage']
        
        # Get status for end_data if available
        end_status = None
        end_color = None
        end_loading_pct = None
        
        if end_data is not None:
            end_loading_pct = end_data['loading_percentage']
            end_status, end_color = get_alert_status(end_loading_pct)
        
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2f4f4f;">Transformer Loading Alert {get_status_emoji(max_status)}</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3 style="color: {max_color};">Peak Status: {max_status}</h3>
                <p><strong>Transformer:</strong> {transformer_id}</p>
                <p><strong>Peak Loading:</strong> {max_loading_pct:.1f}%</p>
                <p><strong>Peak Time:</strong> {max_data.name.strftime('%Y-%m-%d %H:%M')}</p>
        """
        
        # Add end date information if available
        if end_data is not None:
            html += f"""
                <h3 style="margin-top: 20px; color: {end_color};">End-Date Status: {end_status}</h3>
                <p><strong>End-Date Loading:</strong> {end_loading_pct:.1f}%</p>
                <p><strong>Time:</strong> {end_data.name.strftime('%Y-%m-%d %H:%M')}</p>
            """
            
        html += f"""
            </div>
            
            <div style="background-color: #ffffff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h4>Peak Loading Readings:</h4>
                <ul>
                    <li>Power: {max_data['power_kw']:.1f} kW</li>
                    <li>Current: {max_data['current_a']:.1f} A</li>
                    <li>Voltage: {max_data['voltage_v']:.1f} V</li>
                    <li>Power Factor: {max_data['power_factor']:.2f}</li>
                </ul>
        """
        
        # Add end date detailed readings if available
        if end_data is not None:
            html += f"""
                <h4 style="margin-top: 20px;">End-Date Readings:</h4>
                <ul>
                    <li>Power: {end_data['power_kw']:.1f} kW</li>
                    <li>Current: {end_data['current_a']:.1f} A</li>
                    <li>Voltage: {end_data['voltage_v']:.1f} V</li>
                    <li>Power Factor: {end_data['power_factor']:.2f}</li>
                </ul>
            """
            
        html += f"""
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

    def _create_deep_link(self, start_date: date, alert_time: datetime, 
                         transformer_id: str, search_end_date: Optional[date] = None) -> str:
        """Create a deep link to the dashboard with alert parameters"""
        try:
            # Make sure start_date is not None
            if start_date is None:
                logger.warning("start_date is None in _create_deep_link")
                start_date = date.today()
            
            # Create parameters with original search dates
            params = {
                'view': 'alert',
                'id': transformer_id,
                'start': start_date.strftime('%Y-%m-%d'),
                'alert_time': alert_time.strftime('%Y-%m-%dT%H:%M:%S') if isinstance(alert_time, datetime) else datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            }
            
            # Add end date if provided
            if search_end_date:
                params['end'] = search_end_date.strftime('%Y-%m-%d')
                
            # Create the query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            
            # Ensure base URL doesn't have trailing slash before adding query parameters
            base_url = self.app_url.rstrip('/')
            deep_link = f"{base_url}/?{query_string}"
            
            logger.info(f"Created deep link with base URL: {base_url}")
            logger.info(f"Full deep link: {deep_link}")
            logger.info(f"Query parameters: {params}")
            
            return deep_link
            
        except Exception as e:
            logger.error(f"Error creating deep link: {str(e)}")
            return "#"  # Return a safe default

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """Send email using Gmail SMTP with app password"""
        try:
            logger.info(f"Attempting to send email to {msg['To']}")
            
            # Connect to Gmail's SMTP server
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.email, self.app_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info("Email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            if "Invalid login" in str(e):
                st.error("❌ Failed to login to Gmail. Please check your app password in secrets.toml")
            return False

    def check_and_send_alerts(
        self,
        results_df: pd.DataFrame,
        start_date: Optional[date] = None,
        alert_time: Optional[datetime] = None,
        recipient: str = None,
        search_end_date: Optional[date] = None,
        selected_hour: Optional[int] = None
    ) -> bool:
        """Check loading conditions and send alert if needed"""
        logger.info("Starting alert check process...")
        
        if not self.email_enabled:
            msg = "Email alerts disabled - Gmail app password not found in secrets.toml"
            logger.warning(msg)
            st.warning(f"📧 {msg}")
            return False

        try:
            # Convert alert_time to datetime if it's a numpy.int64
            if isinstance(alert_time, np.int64):
                alert_time = pd.Timestamp(alert_time).to_pydatetime()
            
            # Log the data we're checking
            logger.info(f"Checking {len(results_df)} data points from {results_df.index[0]} to {results_df.index[-1]}")
            logger.info(f"Current email settings - From: {self.email}, App password configured: {bool(self.app_password)}")
            
            # Create an expander for detailed alert info
            with st.expander("📋 Alert Check Details", expanded=True):
                st.write("**Checking Alert Conditions**")
                st.write(f"Analyzing {len(results_df)} data points...")
                
                # Select the alert points (max and end date)
                max_point, end_point = self._select_alert_point(
                    results_df, 
                    end_date=search_end_date,
                    selected_hour=selected_hour
                )
                
                if max_point is None:
                    logger.info("No alert point selected - conditions not met")
                    return False
                
                # Get max alert status and color
                max_status, max_color = get_alert_status(max_point['loading_percentage'])
                logger.info(f"Max alert status: {max_status} ({max_point['loading_percentage']:.1f}%)")
                st.write(f"**Peak Loading Status:** {max_status}")
                st.write(f"**Peak Loading:** {max_point['loading_percentage']:.1f}%")
                st.write(f"**Peak Time:** {max_point.name}")
                
                # Add end point info to UI if available
                if end_point is not None:
                    end_status, end_color = get_alert_status(end_point['loading_percentage'])
                    st.write(f"**End-Date Loading Status:** {end_status}")
                    st.write(f"**End-Date Loading:** {end_point['loading_percentage']:.1f}%")
                    st.write(f"**End Time:** {end_point.name}")
                    
                    # Store the end point timestamp in session state for chart highlighting
                    st.session_state.highlight_timestamp = end_point.name
                    logger.info(f"Set highlight timestamp to end date: {end_point.name}")
                
                # Create deep link
                deep_link = self._create_deep_link(
                    start_date,
                    alert_time or max_point.name,
                    max_point['transformer_id'],
                    search_end_date
                )
                logger.info(f"Created deep link: {deep_link}")
                
                # Create and send email
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"Transformer Loading Alert - Peak: {max_point['loading_percentage']:.1f}%" + (
                    f", End: {end_point['loading_percentage']:.1f}%" if end_point is not None else ""
                )
                msg['From'] = self.email
                msg['To'] = recipient or self.email
                
                logger.info(f"Preparing email to: {msg['To']}")
                st.write("**Sending Email Alert**")
                st.write(f"To: {msg['To']}")
                
                # Create HTML content
                html_content = self._create_email_content(
                    max_point, 
                    end_point,
                    max_status, 
                    max_color, 
                    deep_link
                )
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send the email
                if self._send_email(msg):
                    st.success(f"✉️ Alert email sent successfully")
                    return True
                else:
                    st.error(f"❌ Failed to send alert email")
                    return False
                
        except Exception as e:
            error_msg = f"Error in check_and_send_alerts: {str(e)}"
            logger.error(error_msg)
            st.error(f"❌ {error_msg}")
            return False

    def process_alerts(self, start_date, selected_hour, selected_feeder, selected_transformer):
        """Process alerts for the given parameters"""
        from app.services.cloud_data_service import CloudDataService
        
        try:
            # Get data service
            data_service = CloudDataService()
            
            # Convert start_date to date if it's a datetime
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            
            # Get transformer data for the specified date range
            transformer_data = data_service.get_transformer_data_range(
                start_date=start_date,
                end_date=start_date,  # For now, we only check one day
                feeder=f"Feeder{selected_feeder}",
                transformer_id=selected_transformer
            )
            
            if transformer_data is None or transformer_data.empty:
                st.warning(f"No data found for transformer {selected_transformer} on {start_date}")
                return False
            
            # Check and send alerts
            return self.check_and_send_alerts(
                transformer_data,
                start_date=start_date,
                alert_time=None,  # Will be determined from the data
                selected_hour=selected_hour
            )
            
        except Exception as e:
            logger.error(f"Error processing alerts: {str(e)}")
            st.error(f"❌ Error processing alerts: {str(e)}")
            return False
