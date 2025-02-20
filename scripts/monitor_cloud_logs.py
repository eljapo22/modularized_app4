"""
Monitor Streamlit Cloud logs in real-time and analyze for issues
"""
import requests
import time
import json
import sys
import logging
from datetime import datetime
import streamlit as st
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cloud_monitor.log')
    ]
)
logger = logging.getLogger(__name__)

def analyze_error(error_msg: str) -> dict:
    """Analyze error message and suggest potential fixes"""
    analysis = {
        "error_type": None,
        "likely_cause": None,
        "suggested_fix": None,
        "severity": "unknown"
    }
    
    # Common error patterns
    if "AttributeError" in error_msg:
        if "no attribute" in error_msg:
            analysis.update({
                "error_type": "AttributeError",
                "likely_cause": "Method or attribute not found, possibly due to caching issues",
                "suggested_fix": "Clear Streamlit cache or check method implementation",
                "severity": "high"
            })
    elif "MotherDuck" in error_msg and "connection" in error_msg.lower():
        analysis.update({
            "error_type": "ConnectionError",
            "likely_cause": "MotherDuck connection failed",
            "suggested_fix": "Check MotherDuck token and network connectivity",
            "severity": "high"
        })
    elif "ModApp4DB" in error_msg:
        analysis.update({
            "error_type": "DatabaseError",
            "likely_cause": "Database schema or query issue",
            "suggested_fix": "Verify table names and schema structure",
            "severity": "high"
        })
    
    return analysis

def monitor_logs():
    """Monitor logs in real-time and analyze issues"""
    logger.info("Starting cloud log monitor...")
    
    # Keep track of seen errors to avoid duplicates
    seen_errors = set()
    
    while True:
        try:
            # Read the latest logs
            with open('cloud_monitor.log', 'r') as f:
                logs = f.readlines()
            
            # Process new logs
            for log in logs[-100:]:  # Look at last 100 lines
                if 'ERROR' in log or 'CRITICAL' in log:
                    error_hash = hash(log)
                    if error_hash not in seen_errors:
                        seen_errors.add(error_hash)
                        
                        # Analyze the error
                        analysis = analyze_error(log)
                        
                        logger.info(f"New error detected!")
                        logger.info(f"Error: {log.strip()}")
                        logger.info(f"Analysis: {json.dumps(analysis, indent=2)}")
                        
                        # If it's a high severity issue, take action
                        if analysis['severity'] == 'high':
                            logger.warning(f"High severity issue detected: {analysis['error_type']}")
                            logger.warning(f"Suggested fix: {analysis['suggested_fix']}")
            
            # Sleep briefly before next check
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Monitor error: {str(e)}")
            time.sleep(10)  # Wait longer if there's an error

if __name__ == "__main__":
    monitor_logs()
