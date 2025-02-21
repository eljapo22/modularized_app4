"""
Cloud-specific alert service for the Transformer Loading Analysis Application
"""
import logging
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Tuple
import smtplib

logger = logging.getLogger(__name__)

def get_alert_status(loading_pct: float) -> tuple[str, str]:
    """
    Get alert status and color based on loading percentage.
    Returns tuple of (status, color).
    
    Thresholds:
    - Critical: >= 120%
    - Overloaded: >= 100%
    - Warning: >= 80%
    - Pre-Warning: >= 50%
    - Normal: < 50%
    """
    if loading_pct >= 120:
        return 'Critical', '#dc3545'  # Red
    elif loading_pct >= 100:
        return 'Overloaded', '#fd7e14'  # Orange
    elif loading_pct >= 80:
        return 'Warning', '#ffc107'  # Yellow
    elif loading_pct >= 50:
        return 'Pre-Warning', '#6f42c1'  # Purple
    else:
        return 'Normal', '#198754'  # Green

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    return {
        'Critical': '🔴',
        'Overloaded': '🟠',
        'Warning': '🟡',
        'Pre-Warning': '🟣',
        'Normal': '🟢'
    }.get(status, '⚪')

def analyze_loading_conditions(df: pd.DataFrame) -> dict:
    """
    Analyze loading conditions and return statistics.
    """
    if 'loading_percentage' not in df.columns:
        return {}
        
    loading = df['loading_percentage']
    
    # Calculate time spent in each condition
    total_records = len(df)
    conditions = {
        'Critical': (loading >= 120).sum(),
        'Overloaded': ((loading >= 100) & (loading < 120)).sum(),
        'Warning': ((loading >= 80) & (loading < 100)).sum(),
        'Pre-Warning': ((loading >= 50) & (loading < 80)).sum(),
        'Normal': (loading < 50).sum()
    }
    
    # Convert to percentages
    percentages = {k: (v/total_records)*100 for k, v in conditions.items()}
    
    # Get peak loading and when it occurred
    peak_loading = loading.max()
    peak_idx = loading.idxmax()
    peak_time = df.loc[peak_idx, 'timestamp'] if peak_idx in df.index else pd.Timestamp.now()
    
    # Calculate average loading
    avg_loading = loading.mean()
    
    # Identify sustained overloads (more than 1 hour above 100%)
    sustained_overloads = []
    if (loading >= 100).any():
        overload_periods = []
        current_period = None
        
        for idx, row in df.iterrows():
            if row['loading_percentage'] >= 100:
                if current_period is None:
                    current_period = {'start': pd.to_datetime(row['timestamp']), 'peak': row['loading_percentage']}
                else:
                    current_period['peak'] = max(current_period['peak'], row['loading_percentage'])
            elif current_period is not None:
                current_period['end'] = pd.to_datetime(df.loc[idx-1, 'timestamp'])
                duration = (current_period['end'] - current_period['start']).total_seconds() / 3600
                if duration >= 1:
                    sustained_overloads.append({
                        'start': current_period['start'],
                        'end': current_period['end'],
                        'duration_hours': duration,
                        'peak_loading': current_period['peak']
                    })
                current_period = None
    
    return {
        'condition_percentages': percentages,
        'peak_loading': peak_loading,
        'peak_time': peak_time,
        'average_loading': avg_loading,
        'sustained_overloads': sustained_overloads
    }

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
                # Convert index to datetime if it's an integer
                if isinstance(max_loading.name, (int, np.integer)):
                    max_loading.name = results_df.index[max_loading.name]
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
        # Calculate end_date as 7 days after start_date
        end_date = start_date + timedelta(days=7)
        
        params = {
            'view': 'alert',
            'id': transformer_id,
            'feeder': 'Feeder 1',
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'alert_time': alert_time.isoformat(),
            'loading': 'true',  # Flag to auto-trigger loading
            'auto_search': 'true'  # Flag to auto-trigger search
        }
        
        # Remove None values and create query string
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
