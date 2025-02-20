"""
Database utility functions for MotherDuck connections
"""
import os
import logging
import duckdb
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool = None

def init_db_pool():
    """Initialize the MotherDuck connection pool"""
    global _connection_pool
    try:
        if _connection_pool is None:
            # Get MotherDuck token from environment
            motherduck_token = os.getenv('MOTHERDUCK_TOKEN')
            if not motherduck_token:
                raise ValueError("MOTHERDUCK_TOKEN environment variable not set")

            # Create connection to MotherDuck
            _connection_pool = duckdb.connect(f'md:?motherduck_token={motherduck_token}')
            logger.info("Successfully initialized MotherDuck connection pool")
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
        if params:
            result = _connection_pool.execute(query, params).fetchdf()
        else:
            result = _connection_pool.execute(query).fetchdf()

        return result.to_dict('records')
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
            logger.info("Successfully closed database connection pool")
    except Exception as e:
        logger.error(f"Error closing database pool: {str(e)}")
        raise
