"""
Database utility functions
"""
import logging
from contextlib import contextmanager
from typing import Generator, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from app.config.database_config import DB_CONFIG
from app.config.table_config import (
    TRANSFORMER_TABLE_TEMPLATE,
    CUSTOMER_TABLE_TEMPLATE,
    FEEDER_NUMBERS
)

logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None

def init_db_pool(minconn=1, maxconn=10) -> None:
    """Initialize the database connection pool"""
    global connection_pool
    try:
        connection_pool = SimpleConnectionPool(
            minconn,
            maxconn,
            **DB_CONFIG,
            cursor_factory=RealDictCursor
        )
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Error initializing database pool: {str(e)}")
        raise

@contextmanager
def get_db_connection() -> Generator:
    """Get a database connection from the pool"""
    global connection_pool
    connection = None
    try:
        connection = connection_pool.getconn()
        yield connection
    finally:
        if connection:
            connection_pool.putconn(connection)

@contextmanager
def get_db_cursor(commit=False) -> Generator:
    """Get a database cursor"""
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()

def execute_query(query: str, params: tuple = None, commit: bool = False) -> Optional[List[dict]]:
    """Execute a database query and return results"""
    try:
        with get_db_cursor(commit=commit) as cursor:
            cursor.execute(query, params)
            if cursor.description:  # If the query returns data
                return cursor.fetchall()
            return None
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise

def get_all_transformer_tables() -> List[str]:
    """Get list of all transformer feeder table names"""
    return [TRANSFORMER_TABLE_TEMPLATE.format(i) for i in FEEDER_NUMBERS]

def get_all_customer_tables() -> List[str]:
    """Get list of all customer feeder table names"""
    return [CUSTOMER_TABLE_TEMPLATE.format(i) for i in FEEDER_NUMBERS]
