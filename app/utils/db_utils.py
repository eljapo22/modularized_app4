"""
Database utility functions for MotherDuck connections
"""
import os
import logging
import duckdb
from typing import List, Dict, Any, Optional
import streamlit as st

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

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Execute a query and return results as a list of dictionaries"""
    global _connection_pool
    try:
        if _connection_pool is None:
            init_db_pool()

        # Execute query with parameters
        try:
            if params:
                result = _connection_pool.execute(query, params).fetchdf()
            else:
                result = _connection_pool.execute(query).fetchdf()

            # Convert to list of dictionaries
            return result.to_dict('records')
        except duckdb.Error as e:
            logger.error(f"DuckDB error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {params}")
            raise
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Parameters: {params}")
        raise

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
