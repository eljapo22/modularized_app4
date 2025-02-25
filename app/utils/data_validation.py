"""
Utilities for data validation and pattern detection
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def validate_transformer_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean transformer data.
    
    Args:
        df: DataFrame containing transformer data
        
    Returns:
        DataFrame with validated and cleaned data
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Ensure timestamp column exists and is datetime
    if 'timestamp' in df.columns and not pd.api.types.is_datetime64_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
    # Drop rows with null timestamps
    if 'timestamp' in df.columns:
        df = df.dropna(subset=['timestamp'])
        
    # Ensure required columns exist
    required_columns = ['transformer_id', 'loading_percentage', 'power_kw']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Missing required columns: {missing_columns}")
        # Add missing columns with default values
        for col in missing_columns:
            df[col] = None
            
    # Convert numeric columns to appropriate types
    numeric_columns = {
        'loading_percentage': float,
        'power_kw': float,
        'size_kva': float,
        'current_a': float,
        'voltage_v': float,
        'power_factor': float
    }
    
    for col, dtype in numeric_columns.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Remove duplicates
    if 'timestamp' in df.columns and 'transformer_id' in df.columns:
        df = df.drop_duplicates(subset=['timestamp', 'transformer_id'], keep='first')
        
    return df

def analyze_trends(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze trends in the data to detect patterns.
    Returns a dictionary of trend metrics.
    """
    if df is None or df.empty:
        return {}
        
    trends = {}
    
    try:
        # Calculate rate of change over time
        time_diff = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600  # hours
        power_diff = df['power_kw'].max() - df['power_kw'].min()
        loading_diff = df['loading_percentage'].max() - df['loading_percentage'].min()
        
        trends['power_change_rate'] = power_diff / time_diff if time_diff > 0 else 0  # kW per hour
        trends['loading_change_rate'] = loading_diff / time_diff if time_diff > 0 else 0  # % per hour
        
        logger.info(f"Power change rate: {trends['power_change_rate']:.2f} kW/hour")
        logger.info(f"Loading change rate: {trends['loading_change_rate']:.2f} %/hour")
        
        # Calculate correlation between time and values
        trends['power_time_correlation'] = df['power_kw'].corr(pd.to_numeric(df['timestamp']))
        trends['loading_time_correlation'] = df['loading_percentage'].corr(pd.to_numeric(df['timestamp']))
        
        logger.info(f"Power-time correlation: {trends['power_time_correlation']:.2f}")
        logger.info(f"Loading-time correlation: {trends['loading_time_correlation']:.2f}")
        
    except Exception as e:
        logger.error(f"Error during trend analysis: {str(e)}")
        return {}
        
    return trends
