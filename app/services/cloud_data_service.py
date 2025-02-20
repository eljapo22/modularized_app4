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
import traceback

logger = logging.getLogger(__name__)

@st.cache_resource
def get_motherduck_connection():
    """Get a cached MotherDuck connection"""
    logger.info("Attempting to get MotherDuck connection from cache")
    try:
        # Get token from Streamlit secrets only
        if not hasattr(st, 'secrets'):
            logger.error("No Streamlit secrets available")
            raise ValueError("No Streamlit secrets available")
            
        if 'MOTHERDUCK_TOKEN' not in st.secrets:
            logger.error("MotherDuck token not found in Streamlit secrets")
            raise ValueError("MotherDuck token not found in Streamlit secrets")
            
        token = st.secrets["MOTHERDUCK_TOKEN"]
        logger.info("Successfully retrieved MotherDuck token")
        
        # Connect with proper token in connection string
        conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        logger.info("Successfully established MotherDuck connection")
        return conn
    except Exception as e:
        logger.error(f"MotherDuck connection failed: {str(e)}\nTraceback: {traceback.format_exc()}")
        st.error("Failed to connect to MotherDuck database. Please check your configuration.")
        raise RuntimeError(f"Failed to connect to MotherDuck: {str(e)}")

class CloudDataService:
    _instance = None
    
    def __new__(cls):
        logger.info("Creating new CloudDataService instance")
        if cls._instance is None:
            try:
                cls._instance = super().__new__(cls)
                cls._instance.conn = get_motherduck_connection()
                logger.info("Successfully initialized CloudDataService singleton")
            except Exception as e:
                logger.error(f"Failed to initialize CloudDataService: {str(e)}\nTraceback: {traceback.format_exc()}")
                raise
        return cls._instance
    
    def __init__(self):
        """Initialize cloud data service with MotherDuck connection"""
        # Initialization is done in __new__
        pass
    
    @st.cache_data(ttl="1h")
    def query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        try:
            logger.info(f"Executing query: {query} with params: {params}")
            if params:
                result = self.conn.execute(query, params).df()
            else:
                result = self.conn.execute(query).df()
            logger.info(f"Query returned {len(result)} rows")
            return result
        except Exception as e:
            logger.error(f"Query failed: {str(e)}\nQuery: {query}\nParams: {params}\nTraceback: {traceback.format_exc()}")
            return None
    
    @st.cache_data(ttl="1h")
    def get_feeder_data(self, feeder: int) -> pd.DataFrame:
        """Get data for a specific feeder"""
        logger.info(f"Getting data for feeder {feeder}")
        query = """
            SELECT 
                timestamp,
                transformer_id,
                size_kva,
                load_range,
                loading_percentage,
                current_a,
                voltage_v,
                power_kw,
                power_kva,
                power_factor
            FROM ModApp4DB.main."Transformer Feeder {}"
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY timestamp
        """.format(feeder)
        return self.query(query)
    
    @st.cache_data(ttl="24h")
    def get_transformer_ids(self, feeder: int) -> List[str]:
        """Get transformer IDs for a feeder"""
        logger.info(f"Getting transformer IDs for feeder {feeder}")
        query = """
            SELECT DISTINCT transformer_id
            FROM ModApp4DB.main."Transformer Feeder {}"
            ORDER BY transformer_id
        """.format(feeder)
        result = self.query(query)
        ids = result['transformer_id'].tolist() if result is not None else []
        logger.info(f"Found {len(ids)} transformers for feeder {feeder}")
        return ids
    
    @st.cache_data(ttl="1h")
    def get_transformer_data(self, transformer_id: str, start_date: date, end_date: Optional[date] = None) -> pd.DataFrame:
        """Get data for a specific transformer within a date range"""
        logger.info(f"Getting data for transformer {transformer_id} from {start_date} to {end_date}")
        if end_date is None:
            end_date = datetime.now().date()
            
        # Extract feeder number from transformer_id (e.g., S1F1ATF003 -> 1)
        feeder_num = transformer_id[3]
            
        query = """
            SELECT 
                timestamp,
                transformer_id,
                size_kva,
                load_range,
                loading_percentage,
                current_a,
                voltage_v,
                power_kw,
                power_kva,
                power_factor
            FROM ModApp4DB.main."Transformer Feeder {}"
            WHERE transformer_id = ?
            AND CAST(timestamp AS DATE) BETWEEN ? AND ?
            ORDER BY timestamp
        """.format(feeder_num)
        return self.query(query, [transformer_id, start_date, end_date])
    
    @st.cache_data(ttl="24h")
    def get_feeder_list(self) -> List[int]:
        """Get list of all feeder IDs"""
        logger.info("Getting list of all feeders")
        # Since tables are named "Transformer Feeder 1", "Transformer Feeder 2", etc.
        # We'll return [1, 2, 3, 4] as that's what we see in the database
        return [1, 2, 3, 4]
    
    @st.cache_data(ttl="1h")
    def get_available_dates(self) -> tuple[date, date]:
        """Get available date range from the data"""
        logger.info("Getting available date range")
        try:
            # Query date range from first feeder (they should all have same date range)
            query = """
            SELECT 
                MIN(CAST(timestamp AS DATE)) as min_date,
                MAX(CAST(timestamp AS DATE)) as max_date
            FROM ModApp4DB.main."Transformer Feeder 1"
            """
            result = self.conn.execute(query).fetchone()
            if not result or not result[0] or not result[1]:
                logger.error("No dates found in MotherDuck")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            min_date = result[0].date()
            max_date = result[1].date()
            logger.info(f"Available date range: {min_date} to {max_date}")
            return min_date, max_date
        except Exception as e:
            logger.error(f"Error getting available dates: {str(e)}\nTraceback: {traceback.format_exc()}")
            default_date = datetime(2024, 2, 14).date()
            return default_date, default_date
    
    @st.cache_data(ttl="1h")
    def get_customer_data(self, feeder: int) -> pd.DataFrame:
        """Get customer data for a specific feeder"""
        logger.info(f"Getting customer data for feeder {feeder}")
        query = """
            SELECT 
                timestamp,
                customer_id,
                transformer_id,
                power_kw,
                power_factor,
                power_kva,
                voltage_v,
                current_a
            FROM ModApp4DB.main."Customer Feeder {}"
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY timestamp
        """.format(feeder)
        return self.query(query)
    
    @st.cache_data(ttl="24h")
    def get_customer_ids(self, transformer_id: str) -> List[str]:
        """Get customer IDs for a transformer"""
        logger.info(f"Getting customer IDs for transformer {transformer_id}")
        # Extract feeder number from transformer_id (e.g., S1F1ATF003 -> 1)
        feeder_num = transformer_id[3]
        
        query = """
            SELECT DISTINCT customer_id
            FROM ModApp4DB.main."Customer Feeder {}"
            WHERE transformer_id = ?
            ORDER BY customer_id
        """.format(feeder_num)
        result = self.query(query, [transformer_id])
        ids = result['customer_id'].tolist() if result is not None else []
        logger.info(f"Found {len(ids)} customers for transformer {transformer_id}")
        return ids

# Initialize the service as a singleton
logger.info("Initializing CloudDataService singleton")
data_service = CloudDataService()
logger.info("CloudDataService initialization complete")
