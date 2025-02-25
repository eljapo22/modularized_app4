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
            logger.info(f"Getting transformer data for {transformer_id} on {date_str}")
            
            # Better feeder number extraction with fallback
            feeder_num = 1  # Default to feeder 1
            try:
                if isinstance(transformer_id, str) and len(transformer_id) > 3:
                    # Try to get feeder number from 4th character in ID (e.g., S1F1ATF001)
                    feeder_chars = [c for c in transformer_id if c.isdigit()]
                    if feeder_chars:
                        feeder_num = int(feeder_chars[0])
                    else:
                        logger.warning(f"Could not extract feeder number from transformer ID: {transformer_id}")
            except Exception as e:
                logger.warning(f"Feeder number extraction failed: {str(e)}")
            
            # Use correct table name with quotes
            table_name = f'"Transformer Feeder {feeder_num}"'
            
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
            FROM {table_name}
            WHERE transformer_id = ?
            AND timestamp::DATE = ?::DATE
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
            logger.info(f"Getting customer data for {customer_id} on {date_str}")
            
            # Better feeder number extraction with fallback
            feeder_num = 1  # Default to feeder 1
            try:
                # Extract feeder from customer ID 
                if isinstance(customer_id, str):
                    # Try to get the transformer part (if customer ID format contains transformer ID)
                    transformer_id = customer_id.split('C')[0] if 'C' in customer_id else customer_id
                    # Try to get feeder number from digits in ID
                    feeder_chars = [c for c in transformer_id if c.isdigit()]
                    if feeder_chars:
                        feeder_num = int(feeder_chars[0])
                    else:
                        logger.warning(f"Could not extract feeder number from ID: {customer_id}")
            except Exception as e:
                logger.warning(f"Feeder number extraction failed: {str(e)}")
            
            # Use correct table name with quotes
            table_name = f'"Customer Feeder {feeder_num}"'
            
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
            FROM {table_name}
            WHERE customer_id = ?
            AND timestamp::DATE = ?::DATE
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
