"""
Base interface for alert services in the Transformer Loading Analysis Application
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

class AlertService(ABC):
    """Abstract base class for alert services"""
    
    @abstractmethod
    def send_alert(self, alert_data: pd.DataFrame, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """
        Send alert email with transformer loading data
        
        Args:
            alert_data: DataFrame containing transformer loading data
            date: Date of the data
            hour: Hour of the data
            recipients: Optional list of email recipients
            
        Returns:
            bool: True if alert was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def test_alert(self, transformer_id: str, date: datetime, hour: int, recipients: Optional[List[str]] = None) -> bool:
        """
        Send a test alert email
        
        Args:
            transformer_id: ID of transformer to test
            date: Test date
            hour: Test hour
            recipients: Optional list of email recipients
            
        Returns:
            bool: True if test alert was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def process_alerts(self, results_df: pd.DataFrame, selected_date: datetime, selected_hour: int, recipients: Optional[List[str]] = None) -> bool:
        """
        Process transformer data and send alerts if conditions are met
        
        Args:
            results_df: DataFrame with transformer loading results
            selected_date: Date to check
            selected_hour: Hour to check
            recipients: Optional list of email recipients
            
        Returns:
            bool: True if alerts were processed successfully, False otherwise
        """
        pass

def get_status_color(status: str) -> str:
    """Get color code for loading status"""
    colors = {
        'Critical': '#FF0000',
        'Overloaded': '#FFA500',
        'Warning': '#FFFF00',
        'Pre-Warning': '#90EE90',
        'Normal': '#008000'
    }
    return colors.get(status, '#000000')

def extract_feeder(transformer_id: str) -> str:
    """Extract feeder ID from transformer ID"""
    return transformer_id.split('_')[0] if '_' in transformer_id else ''

def generate_dashboard_link(transformer_id: str, feeder: str, date: datetime, hour: int) -> str:
    """Generate link to dashboard with pre-filled parameters"""
    base_url = "https://transformerapp.streamlit.app"
    date_str = date.strftime('%Y-%m-%d')
    return f"{base_url}?transformer={transformer_id}&feeder={feeder}&date={date_str}&hour={hour}"

def check_alert_condition(results_df: pd.DataFrame, selected_hour: int, transformer_id: str = None) -> Optional[pd.DataFrame]:
    """
    Check for alert conditions at the selected hour
    
    Returns DataFrame with rows that meet alert conditions, or None if no alerts
    """
    if results_df is None or results_df.empty:
        return None
        
    # Filter for selected hour and transformer
    hour_data = results_df[results_df['hour'] == selected_hour].copy()
    if transformer_id:
        hour_data = hour_data[hour_data['transformer_id'] == transformer_id]
        
    if hour_data.empty:
        return None
        
    # Check loading conditions
    alert_conditions = (
        (hour_data['load_range'].isin(['Critical', 'Overloaded', 'Warning']))
    )
    
    alerts = hour_data[alert_conditions]
    return alerts if not alerts.empty else None
