"""
Cloud data service that exclusively uses MotherDuck for data access
"""
import os
import pandas as pd
import duckdb
from datetime import datetime, date
from typing import Optional, List, Dict, Union
import logging
import streamlit as st

logger = logging.getLogger(__name__)

class CloudDataService:
    def __init__(self):
        """Initialize cloud data service with MotherDuck connection"""
        self.conn = None
        self.setup_motherduck()
    
    def setup_motherduck(self):
        """Setup MotherDuck connection"""
        try:
            # Get token from Streamlit secrets only
            if not hasattr(st, 'secrets') or 'MOTHERDUCK_TOKEN' not in st.secrets:
                raise ValueError("MotherDuck token not found in Streamlit secrets")
                
            token = st.secrets["MOTHERDUCK_TOKEN"]
            
            # Set the token in environment variable as recommended by MotherDuck
            os.environ["motherduck_token"] = token
            
            # Connect using the simpler connection string
            self.conn = duckdb.connect('md:ModApp4DB')
            logger.info("Successfully connected to MotherDuck")
        except Exception as e:
            logger.error(f"MotherDuck connection failed: {str(e)}")
            st.error("Failed to connect to MotherDuck database. Please check your configuration.")
            raise RuntimeError(f"Failed to connect to MotherDuck: {str(e)}")
    
    def query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        try:
            if params:
                return self.conn.execute(query, params).df()
            return self.conn.execute(query).df()
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return None
    
    @st.cache_data(ttl="1h")
    def get_feeder_data(self, feeder: int) -> pd.DataFrame:
        """Get data for a specific feeder"""
        query = """
            SELECT *
            FROM transformer_readings
            WHERE feeder_id = ?
            AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """
        return self.query(query, [feeder])
    
    @st.cache_data(ttl="24h")
    def get_transformer_ids(self, feeder: int) -> List[str]:
        """Get transformer IDs for a feeder"""
        query = """
            SELECT DISTINCT transformer_id
            FROM transformer_readings
            WHERE feeder_id = ?
            ORDER BY transformer_id
        """
        result = self.query(query, [feeder])
        return result['transformer_id'].tolist() if result is not None else []
    
    @st.cache_data(ttl="1h")
    def get_transformer_data(self, transformer_id: str, start_date: date, end_date: Optional[date] = None) -> pd.DataFrame:
        """Get data for a specific transformer within a date range"""
        if end_date is None:
            end_date = datetime.now().date()
            
        query = """
            SELECT *
            FROM transformer_readings
            WHERE transformer_id = ?
            AND DATE(timestamp) BETWEEN ? AND ?
            ORDER BY timestamp
        """
        return self.query(query, [transformer_id, start_date, end_date])
    
    @st.cache_data(ttl="24h")
    def get_feeder_list(self) -> List[int]:
        """Get list of all feeder IDs"""
        query = """
            SELECT DISTINCT feeder_id
            FROM transformer_readings
            ORDER BY feeder_id
        """
        result = self.query(query)
        return result['feeder_id'].tolist() if result is not None else []
    
    @property
    @st.cache_data(ttl="1h")
    def available_dates(self) -> tuple[date, date]:
        """Get available date range from the data"""
        try:
            # Query date range from MotherDuck
            query = """
            SELECT 
                MIN(DATE(timestamp)) as min_date,
                MAX(DATE(timestamp)) as max_date
            FROM transformer_data
            """
            result = self.conn.execute(query).fetchone()
            if not result or not result[0] or not result[1]:
                logger.error("No dates found in MotherDuck")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            min_date = result[0].date()
            max_date = result[1].date()
            logger.info(f"Date range from MotherDuck: {min_date} to {max_date}")
            return min_date, max_date
        except Exception as e:
            logger.error(f"Error getting available dates: {str(e)}")
            default_date = datetime(2024, 2, 14).date()
            return default_date, default_date

# Initialize the service
data_service = CloudDataService()
