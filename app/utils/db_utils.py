"""
Database utility functions for MotherDuck connections
"""
import os
import logging
import duckdb
from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd
import re

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool = None

def init_db_pool():
    """Initialize the MotherDuck connection pool"""
    global _connection_pool
    try:
        if _connection_pool is None:
            # Get MotherDuck token from Streamlit secrets
            try:
                motherduck_token = st.secrets["MOTHERDUCK_TOKEN"]
            except Exception as e:
                logger.error(f"Error accessing MOTHERDUCK_TOKEN from Streamlit secrets: {str(e)}")
                raise ValueError("MOTHERDUCK_TOKEN not found in Streamlit secrets")

            # Create connection to MotherDuck
            _connection_pool = duckdb.connect(f'md:?motherduck_token={motherduck_token}')
            logger.info("Successfully initialized MotherDuck connection pool")
    except duckdb.Error as e:
        logger.error(f"DuckDB error initializing database pool: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database pool: {str(e)}")
        raise

def execute_query(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute a query and return results as a pandas DataFrame"""
    try:
        # Get database connection
        from app.core.database import get_database_connection
        connection = get_database_connection()
        
        if connection is None:
            logger.error("Database connection is None")
            return pd.DataFrame()
        
        # Debug log the query and params
        logger.debug(f"Executing query: {query}")
        logger.debug(f"With parameters: {params}")
            
        # Execute query with parameters
        try:
            if params:
                result = connection.execute(query, params).fetchdf()
            else:
                result = connection.execute(query).fetchdf()

            # Log the result size
            row_count = 0 if result.empty else len(result)
            logger.debug(f"Query returned {row_count} rows")
            
            return result if not result.empty else pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {params}")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return pd.DataFrame()

# Adding back the original query function that returns a list of dictionaries
def query_data(query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
    """Execute a query and return results as a list of dictionaries"""
    global _connection_pool
    try:
        if _connection_pool is None:
            init_db_pool()

        # Debug log
        logger.debug(f"query_data - Executing query: {query}")
        logger.debug(f"query_data - With parameters: {params}")

        # Execute query with parameters
        try:
            if params:
                result = _connection_pool.execute(query, params).fetchdf()
            else:
                result = _connection_pool.execute(query).fetchdf()

            # Convert to list of dictionaries
            if result is not None and not result.empty:
                # Log success
                logger.debug(f"query_data - Query returned {len(result)} rows")
                records = result.to_dict(orient='records')
                return records
            else:
                logger.debug("query_data - Query returned no results")
                return []

        except Exception as e:
            logger.error(f"query_data - Query execution error: {str(e)}")
            logger.error(f"query_data - Query: {query}")
            logger.error(f"query_data - Parameters: {params}")
            return []

    except Exception as e:
        logger.error(f"query_data - Connection pool error: {str(e)}")
        return []

def extract_feeder_number(feeder_str: str) -> int:
    """
    Extract feeder number from feeder string with robust error handling.
    Handles various formats including 'Feeder 1', 'Feeder  1', etc.
    
    Args:
        feeder_str: String containing feeder information
        
    Returns:
        int: Feeder number (defaults to 1 if extraction fails)
    """
    try:
        if not isinstance(feeder_str, str):
            return 1  # Default to feeder 1
            
        # Strip all whitespace and normalize
        feeder_str = feeder_str.strip()
        
        # Try regex pattern to extract digits after "Feeder"
        matches = re.search(r'Feeder\s+(\d+)', feeder_str)
        if matches:
            return int(matches.group(1))
            
        # Fallback: try to find any digit in the string
        digits = [c for c in feeder_str if c.isdigit()]
        if digits:
            return int(digits[0])
            
        # If all else fails, use default
        return 1
    except Exception as e:
        logger.warning(f"Failed to extract feeder number from '{feeder_str}': {str(e)}")
        return 1  # Default to feeder 1

def close_pool():
    """Close the database connection pool"""
    global _connection_pool
    try:
        if _connection_pool is not None:
            _connection_pool.close()
            _connection_pool = None
            logger.info("Successfully closed database pool")
    except duckdb.Error as e:
        logger.error(f"DuckDB error closing database pool: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error closing database pool: {str(e)}")
        raise
