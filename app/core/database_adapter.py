"""
Database adapter layer for MotherDuck connections
"""

import streamlit as st
import duckdb
from typing import Optional, List
import pandas as pd
import logging
from app.utils.db_utils import query_data as utils_query_data

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """Adapter for MotherDuck cloud database"""
    
    def __init__(self):
        """Initialize the database adapter with MotherDuck connection"""
        self.db_name = "ModApp4DB"
        self.feeders = range(1, 5)
        # Use the cached connection from database.py
        from app.core.database import get_database_connection
        self.conn = get_database_connection()
        logger.info("DatabaseAdapter initialized with MotherDuck connection")

    def query_data(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute query and return results"""
        try:
            if self.conn is None:
                # Fallback to the connection pool if direct connection fails
                return pd.DataFrame(utils_query_data(query, params))
                
            if params:
                result = self.conn.execute(query, params).fetchdf()
            else:
                result = self.conn.execute(query).fetchdf()
            
            # Convert timestamp columns to datetime
            for col in result.columns:
                if 'timestamp' in col.lower():
                    result[col] = pd.to_datetime(result[col])
                    
            return result
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {params}")
            # Try using the connection pool as fallback
            try:
                return pd.DataFrame(utils_query_data(query, params))
            except:
                return pd.DataFrame()

    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        """Get transformer data from specific feeder"""
        try:
            # Extract feeder number from transformer ID (e.g., S1F1ATF001 -> 1)
            feeder = int(transformer_id[3])  # Position 3 is the feeder number
            
            query = f"""
            SELECT 
                timestamp,
                transformer_id,
                loading_percentage,
                power_kw,
                size_kva,
                power_factor,
                voltage_v,
                current_a,
                power_kva,
                load_range
            FROM transformer_feeder_{feeder}
            WHERE transformer_id = ?
            AND DATE(timestamp) = DATE(?)
            """
            
            result = self.query_data(query, [transformer_id, date_str])
            
            # Remove duplicates if any exist
            if 'timestamp' in result.columns:
                before_count = len(result)
                result = result.drop_duplicates(subset=['timestamp', 'transformer_id'], keep='first')
                after_count = len(result)
                
                if before_count > after_count:
                    logger.info(f"Removed {before_count - after_count} duplicate rows")
            
            return result
        except Exception as e:
            logger.error(f"Error in get_transformer_data: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame on error

    def get_customer_data(self, customer_id: str, date_str: str) -> pd.DataFrame:
        """Get customer data for a specific date"""
        try:
            # Extract feeder from customer ID (format matches transformer ID pattern)
            transformer_id = customer_id.split('C')[0]  # Get transformer part of customer ID
            feeder = int(transformer_id[3])  # Same position as in transformer ID
            
            query = f"""
            SELECT 
                timestamp,
                customer_id,
                transformer_id,
                power_kw,
                power_factor,
                power_kva,
                current_a,
                voltage_v
            FROM customer_feeder_{feeder}
            WHERE customer_id = ?
            AND DATE(timestamp) = DATE(?)
            """
            
            result = self.query_data(query, [customer_id, date_str])
            
            # Remove duplicates
            if 'timestamp' in result.columns:
                result = result.drop_duplicates(subset=['timestamp', 'customer_id'], keep='first')
            
            return result
        except Exception as e:
            logger.error(f"Error in get_customer_data: {str(e)}")
            return pd.DataFrame()

def get_db_adapter() -> DatabaseAdapter:
    """Factory function to get the database adapter"""
    return DatabaseAdapter()
