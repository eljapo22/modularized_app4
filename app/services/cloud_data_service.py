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

class DataService:
    def __init__(self):
        """Initialize cloud data service with MotherDuck connection"""
        self.setup_motherduck()
    
    def setup_motherduck(self):
        """Setup MotherDuck connection"""
        try:
            token = os.getenv("MOTHERDUCK_TOKEN") or st.secrets["MOTHERDUCK_TOKEN"]
            self.conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
            logger.info("Successfully connected to MotherDuck")
        except Exception as e:
            logger.error(f"MotherDuck connection failed: {str(e)}")
            raise RuntimeError("Failed to connect to MotherDuck. Cloud environment requires MotherDuck connection.")
    
    @st.cache_data(ttl="1h")
    def get_feeder_data(self, feeder: int) -> pd.DataFrame:
        """Get data for a specific feeder"""
        query = """
            SELECT *
            FROM transformer_readings
            WHERE feeder_id = ?
            AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """
        return self.conn.execute(query, [feeder]).df()
    
    @st.cache_data(ttl="24h")
    def get_transformer_ids(self, feeder: int) -> List[str]:
        """Get transformer IDs for a feeder"""
        query = """
            SELECT DISTINCT transformer_id
            FROM transformer_readings
            WHERE feeder_id = ?
            ORDER BY transformer_id
        """
        return self.conn.execute(query, [feeder]).df()['transformer_id'].tolist()
    
    @st.cache_data(ttl="1h")
    def get_transformer_data(self, transformer_id: str, selected_date: date) -> pd.DataFrame:
        """Get data for a specific transformer on a specific date"""
        query = """
            SELECT 
                timestamp,
                transformer_id,
                power_kw,
                current_a,
                voltage_v,
                power_factor,
                size_kva,
                loading_percentage,
                feeder_id
            FROM transformer_readings
            WHERE transformer_id = ?
            AND DATE(timestamp) = ?
            ORDER BY timestamp
        """
        return self.conn.execute(query, [transformer_id, selected_date]).df()
    
    @st.cache_data(ttl="24h")
    def get_available_dates(self) -> tuple[date, date]:
        """Get available date range"""
        query = """
            SELECT 
                MIN(DATE(timestamp)) as min_date,
                MAX(DATE(timestamp)) as max_date
            FROM transformer_readings
        """
        result = self.conn.execute(query).df()
        return result['min_date'].iloc[0], result['max_date'].iloc[0]
    
    @st.cache_data(ttl="24h")
    def get_available_feeders(self) -> List[str]:
        """Get list of available feeders"""
        query = """
            SELECT DISTINCT feeder_id
            FROM transformer_readings
            ORDER BY feeder_id
        """
        feeders = self.conn.execute(query).df()['feeder_id'].tolist()
        return [f"Feeder {fid}" for fid in feeders]
    
    @st.cache_data(ttl="1h")
    def get_customer_data(self, transformer_id: str, selected_date: date) -> pd.DataFrame:
        """Get customer data for a transformer"""
        query = """
            SELECT 
                customer_id,
                consumption_kwh,
                peak_demand_kw,
                power_factor,
                connection_type
            FROM customer_readings
            WHERE transformer_id = ?
            AND DATE(timestamp) = ?
        """
        return self.conn.execute(query, [transformer_id, selected_date]).df()

# Initialize the service
data_service = DataService()
