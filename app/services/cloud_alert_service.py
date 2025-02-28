"""
Cloud-specific alert service for the Transformer Loading Analysis Application
Updated 2025-02-28: Enhanced email template with recommendations
"""
import logging
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, time
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
            
            # Using the correct thresholds from MEMORY:
            # - Critical: >= 120%
            # - Overloaded: >= 100%
            # - Warning: >= 80%
            # - Pre-Warning: >= 50%
            # - Normal: < 50%
            
            if max_loading['loading_percentage'] >= 50:  # Pre-Warning threshold
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

    def _create_email_content(self, max_data, end_data=None, max_status=None, max_color='#dc3545', deep_link=None):
        """Create HTML email content for alert"""
        # Extract data safely using dictionary-style access
        try:
            transformer_id = max_data['transformer_id'] if 'transformer_id' in max_data else 'Unknown'
            max_loading_pct = max_data['loading_percentage'] if 'loading_percentage' in max_data else 0.0
            
            # Get the timestamp (which is the Series name/index)
            max_timestamp = max_data.name if hasattr(max_data, 'name') else datetime.now()
            
            # Set default status if not provided
            if max_status is None:
                max_status, max_color = get_alert_status(max_loading_pct)
            
            # Get end date status if available
            end_status = None
            end_color = '#6c757d'  # Default gray
            end_loading_pct = 0
            end_timestamp = None
            
            if end_data is not None:
                end_loading_pct = end_data['loading_percentage'] if 'loading_percentage' in end_data else 0.0
                end_status, end_color = get_alert_status(end_loading_pct)
                end_timestamp = end_data.name if hasattr(end_data, 'name') else datetime.now()
        
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; line-height: 1.6; color: #333;">
                <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px; margin-bottom: 25px; text-align: center; border-bottom: 3px solid #0d6efd;">
                    <h2 style="margin: 0; color: #2c3e50; font-size: 26px;">⚡ Transformer Loading Alert ⚡</h2>
                </div>
                
                <p style="margin-top: 20px; font-size: 16px;">Dear Recipient,</p>
                
                <p style="margin-bottom: 25px; font-size: 16px;">This is an automated alert from the Transformer Loading Analysis System regarding abnormal loading conditions detected for Transformer <strong>{transformer_id}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid {max_color};">
                    <h3 style="color: {max_color}; margin-top: 0; font-size: 20px;">{get_status_emoji(max_status)} {max_status} Peak Load Alert</h3>
                    <ul style="list-style-type: none; padding-left: 10px; margin: 20px 0;">
                        <li style="padding: 5px 0;"><strong>Peak Loading:</strong> {max_loading_pct:.1f}% {'' if max_loading_pct < 100 else '<span style="color: #dc3545;">(Exceeds safe threshold)</span>'}</li>
                        <li style="padding: 5px 0;"><strong>Peak Occurrence:</strong> {max_timestamp.strftime('%B %d, %Y, at %H:%M')}</li>
                    </ul>
                </div>
                
                <div style="background-color: #ffffff; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
                    <h4 style="margin-top: 0; color: #495057; font-size: 18px;">📊 Peak Load Readings:</h4>
                    <ul style="list-style-type: none; padding-left: 10px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <li style="padding: 5px 0;"><strong>Power:</strong> {max_data['power_kw']:.1f} kW</li>
                        <li style="padding: 5px 0;"><strong>Current:</strong> {max_data['current_a']:.1f} A</li>
                        <li style="padding: 5px 0;"><strong>Voltage:</strong> {max_data['voltage_v']:.1f} V</li>
                        <li style="padding: 5px 0;"><strong>Power Factor:</strong> {max_data['power_factor']:.2f}</li>
                    </ul>
                </div>
            """
        
            # Add end date information if available
            if end_data is not None:
                html += f"""
                <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid {end_color};">
                    <h3 style="color: {end_color}; margin-top: 0; font-size: 20px;">{get_status_emoji(end_status)} {end_status}: End-Date Loading</h3>
                    <ul style="list-style-type: none; padding-left: 10px; margin: 20px 0;">
                        <li style="padding: 5px 0;"><strong>End-Date Loading:</strong> {end_loading_pct:.1f}%</li>
                        <li style="padding: 5px 0;"><strong>Recorded On:</strong> {end_timestamp.strftime('%B %d, %Y, at %H:%M')}</li>
                    </ul>
                </div>
                
                <div style="background-color: #ffffff; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #e9ecef;">
                    <h4 style="margin-top: 0; color: #495057; font-size: 18px;">📊 End-Date Load Readings:</h4>
                    <ul style="list-style-type: none; padding-left: 10px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <li style="padding: 5px 0;"><strong>Power:</strong> {end_data['power_kw']:.1f} kW</li>
                        <li style="padding: 5px 0;"><strong>Current:</strong> {end_data['current_a']:.1f} A</li>
                        <li style="padding: 5px 0;"><strong>Voltage:</strong> {end_data['voltage_v']:.1f} V</li>
                        <li style="padding: 5px 0;"><strong>Power Factor:</strong> {end_data['power_factor']:.2f}</li>
                    </ul>
                </div>
                """
            
            html += f"""
                <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #0d6efd;">
                    <h4 style="margin-top: 0; color: #495057; font-size: 18px;">Recommended Actions:</h4>
                    <ul>
                        <li style="margin-bottom: 10px;"><strong>Immediate Inspection:</strong> Check transformer health and cooling systems.</li>
                        <li style="margin-bottom: 10px;"><strong>Load Redistribution:</strong> Consider redistributing the load to avoid overloading.</li>
                        <li style="margin-bottom: 10px;"><strong>Monitor Trends:</strong> Review past loading history for potential risk mitigation.</li>
                    </ul>
                </div>
                
                <p style="margin: 25px 0; font-size: 16px;">For a detailed loading history and further analysis, click the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{deep_link}" style="background-color: #0d6efd; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        🔍 View Loading History
                    </a>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                    <p style="margin-bottom: 5px; font-size: 16px;">If you have any questions or require further assistance, please contact the maintenance team.</p>
                    
                    <p style="margin-top: 25px; font-size: 16px;">
                        Best regards,<br>
                        <strong>Transformer Monitoring Team</strong>
                    </p>
                    
                    <p style="color: #6c757d; font-size: 12px; text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                        This is an automated alert from your Transformer Loading Analysis System.
                    </p>
                </div>
            </div>
            """
            return html
        
        except Exception as e:
            logger.error(f"Error creating email content: {str(e)}")
            return ""

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
                # Add the alert time to match the end date if not already specified
                if not isinstance(alert_time, datetime) or alert_time.date() != search_end_date:
                    end_hour = 23  # Default to end of day
                    end_alert_time = datetime.combine(search_end_date, time(hour=end_hour))
                    params['alert_time'] = end_alert_time.strftime('%Y-%m-%dT%H:%M:%S')
                    logger.info(f"Setting alert_time to end date: {params['alert_time']}")
            
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
            
        # Check if the DataFrame is empty
        if results_df is None or results_df.empty:
            logger.warning("Empty results dataframe provided to check_and_send_alerts")
            st.warning("📊 No data available for alert analysis")
            return False

        try:
            # Add verbose debug logging
            logger.info(f"DataFrame shape: {results_df.shape}")
            if not results_df.empty:
                logger.info(f"DataFrame columns: {results_df.columns.tolist()}")
                logger.info(f"DataFrame index type: {type(results_df.index)}")
                logger.info(f"DataFrame date range: {results_df.index.min()} to {results_df.index.max()}")
                
                # Check if loading_percentage is in the dataframe
                if 'loading_percentage' in results_df.columns:
                    logger.info(f"Loading percentage stats: min={results_df['loading_percentage'].min():.1f}%, max={results_df['loading_percentage'].max():.1f}%, mean={results_df['loading_percentage'].mean():.1f}%")
                
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
                emoji_indicator = get_status_emoji(max_status)
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"{emoji_indicator} {max_status} Transformer Loading Alert - Peak: {max_point['loading_percentage']:.1f}%" + (
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
                    max_status=max_status, 
                    max_color=max_color, 
                    deep_link=deep_link
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
