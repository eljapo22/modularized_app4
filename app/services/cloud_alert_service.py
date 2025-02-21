"""
Cloud-specific alert service for the Transformer Loading Analysis Application
"""
import logging
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import pandas as pd
import numpy as np
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

    def _select_alert_point(self, results_df: pd.DataFrame) -> Optional[pd.Series]:
        """Select the point to alert on"""
        try:
            logger.info("=== Starting Alert Point Selection ===")
            logger.info(f"Analyzing {len(results_df)} data points")
            
            # Find the highest loading percentage
            max_loading_idx = results_df['loading_percentage'].idxmax()
            max_loading = results_df.loc[max_loading_idx]
            
            # Log detailed loading information
            logger.info(f"Maximum loading found: {max_loading['loading_percentage']:.1f}%")
            logger.info(f"At timestamp: {max_loading.name}")
            logger.info(f"Transformer ID: {max_loading.get('transformer_id', 'N/A')}")
            
            # Only alert if loading is high enough
            if max_loading['loading_percentage'] >= 80:
                logger.info(f"Alert threshold met: {max_loading['loading_percentage']:.1f}% >= 80%")
                return max_loading
            else:
                logger.info(f"Below alert threshold: {max_loading['loading_percentage']:.1f}% < 80%")
                st.info(f"🔍 Maximum loading ({max_loading['loading_percentage']:.1f}%) is below alert threshold (80%)")
                return None
                
        except Exception as e:
            logger.error(f"Error in alert point selection: {str(e)}", exc_info=True)
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
        """Create HTML content for email"""
        # Convert timestamp if it's a numpy int
        alert_time = data.name
        if isinstance(alert_time, (np.int64, np.integer)):
            alert_time = pd.Timestamp(alert_time)
            
        # Get power value from correct column name
        power_value = data.get('power_kw', data.get('power', 0))
            
        return f"""
        <html>
        <body>
        <h2>Transformer Loading Alert</h2>
        <p>A transformer has exceeded normal loading conditions:</p>
        
        <div style="margin: 20px 0; padding: 10px; border: 1px solid {color}; border-radius: 5px;">
            <p><strong>Status:</strong> <span style="color: {color}">{status}</span></p>
            <p><strong>Transformer:</strong> {data['transformer_id']}</p>
            <p><strong>Loading:</strong> {data['loading_percentage']:.1f}%</p>
            <p><strong>Power:</strong> {power_value:.2f} kW</p>
            <p><strong>Alert Time:</strong> {alert_time.strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <p>View details in the application: <a href="{deep_link}">Click here</a></p>
        
        <p style="color: #666; font-size: 0.9em;">
            This is an automated alert from the Transformer Monitoring System.
        </p>
        </body>
        </html>
        """
    
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
        recipient: str = None
    ) -> bool:
        """Check loading conditions and send alert if needed"""
        logger.info("=== Starting Alert Check Process ===")
        logger.info(f"Data points to analyze: {len(results_df)}")
        logger.info(f"Time range: {results_df.index[0]} to {results_df.index[-1]}")
        
        if not self.email_enabled:
            msg = "Email alerts disabled - Gmail app password not found in secrets.toml"
            logger.warning(msg)
            st.warning(f"📧 {msg}")
            return False

        try:
            # Create an expander for detailed alert info
            with st.expander("📋 Alert Check Details", expanded=True):
                st.write("**Checking Alert Conditions**")
                
                # Select the alert point
                alert_point = self._select_alert_point(results_df)
                
                if alert_point is None:
                    logger.info("No alert point selected - conditions not met")
                    return False
                
                # Get alert status and color
                status, color = get_alert_status(alert_point['loading_percentage'])
                logger.info(f"Alert status determined: {status} at {alert_point['loading_percentage']:.1f}%")
                
                # Create deep link
                deep_link = self._create_deep_link(
                    start_date,
                    alert_time or alert_point.name,
                    alert_point['transformer_id']
                )
                logger.info(f"Deep link created: {deep_link}")
                
                # Prepare email
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"Transformer Loading Alert - {alert_point['loading_percentage']:.1f}% Loading"
                msg['From'] = self.email
                msg['To'] = recipient or self.email
                
                logger.info(f"Preparing email: Subject={msg['Subject']}, To={msg['To']}")
                
                # Create and send email
                html_content = self._create_email_content(
                    alert_point, status, color, deep_link
                )
                msg.attach(MIMEText(html_content, 'html'))
                
                # Send and log result
                if self._send_email(msg):
                    logger.info("=== Alert Process Completed Successfully ===")
                    return True
                else:
                    logger.error("=== Alert Process Failed - Email Send Error ===")
                    return False
                
        except Exception as e:
            logger.error(f"=== Alert Process Failed - Error: {str(e)} ===", exc_info=True)
            st.error(f"❌ Error in alert process: {str(e)}")
            return False
