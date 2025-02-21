"""
Utilities for data validation and pattern detection
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

def validate_transformer_data(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate transformer data for anomalies and patterns.
    Returns a dictionary of validation flags.
    """
    if df is None or df.empty:
        return {}
        
    validations = {}
    
    try:
        # Check for monotonic increase
        power_increasing = df['power_kw'].is_monotonic_increasing
        loading_increasing = df['loading_percentage'].is_monotonic_increasing
        validations['monotonic_increase'] = power_increasing or loading_increasing
        
        if validations['monotonic_increase']:
            logger.warning("Detected monotonic increase in power or loading values")
            logger.info(f"Power trend: {'increasing' if power_increasing else 'varying'}")
            logger.info(f"Loading trend: {'increasing' if loading_increasing else 'varying'}")
            
        # Check for unusual rate of change
        power_changes = df['power_kw'].diff()
        loading_changes = df['loading_percentage'].diff()
        
        # Calculate statistics
        power_change_stats = {
            'mean': power_changes.mean(),
            'std': power_changes.std(),
            'max': power_changes.max()
        }
        loading_change_stats = {
            'mean': loading_changes.mean(),
            'std': loading_changes.std(),
            'max': loading_changes.max()
        }
        
        # Flag if changes are consistently positive
        validations['consistent_increase'] = (
            power_changes.mean() > 0 and 
            power_changes.std() < abs(power_changes.mean())
        )
        
        if validations['consistent_increase']:
            logger.warning("Detected consistent increase pattern")
            logger.info(f"Power change stats: {power_change_stats}")
            logger.info(f"Loading change stats: {loading_change_stats}")
            
        # Check for missing timestamps
        time_diffs = df['timestamp'].diff()
        expected_diff = pd.Timedelta(minutes=15)  # Assuming 15-minute intervals
        has_gaps = (time_diffs > expected_diff * 1.5).any()
        validations['has_time_gaps'] = has_gaps
        
        if has_gaps:
            gaps = time_diffs[time_diffs > expected_diff * 1.5]
            logger.warning(f"Found {len(gaps)} time gaps in data")
            logger.info(f"Largest gap: {gaps.max()}")
            
        # Check for value ranges
        validations['unusual_power_range'] = (
            df['power_kw'].max() > df['power_kw'].mean() * 2 or
            df['power_kw'].min() < 0
        )
        validations['unusual_loading_range'] = (
            df['loading_percentage'].max() > 100 or
            df['loading_percentage'].min() < 0
        )
        
        if validations['unusual_power_range'] or validations['unusual_loading_range']:
            logger.warning("Detected unusual value ranges")
            logger.info(f"Power range: {df['power_kw'].min():.2f} to {df['power_kw'].max():.2f} kW")
            logger.info(f"Loading range: {df['loading_percentage'].min():.2f}% to {df['loading_percentage'].max():.2f}%")
            
    except Exception as e:
        logger.error(f"Error during data validation: {str(e)}")
        return {}
        
    return validations

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
