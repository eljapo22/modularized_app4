"""
Database connection management for MotherDuck
"""

import os
import streamlit as st
import duckdb
import logging

logger = logging.getLogger(__name__)

class SuppressOutput:
    """Context manager to suppress DuckDB output"""
    def __enter__(self):
        self._original_stdout = os.dup(1)
        self._devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._devnull, 1)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self._original_stdout, 1)
        os.close(self._devnull)

@st.cache_resource
def get_database_connection():
    """Get a cached MotherDuck database connection"""
    try:
        # Get MotherDuck token from secrets
        token = st.secrets.get('MOTHERDUCK_TOKEN')
        if not token:
            st.error("MotherDuck token not found in secrets")
            return None
            
        # Set token in environment as recommended by MotherDuck
        os.environ["motherduck_token"] = token
        
        # Create connection and load extension
        con = duckdb.connect(':memory:')
        con.execute("INSTALL motherduck")
        con.execute("LOAD motherduck")
        
        # Attach MotherDuck database
        con.execute("ATTACH 'md:ModApp4DB' as motherduck")
        con.execute("USE motherduck")
        
        # Configure connection
        con.execute("SET enable_progress_bar=false")
        con.execute("SET errors_as_json=true")
        
        logger.info("Successfully connected to MotherDuck database")
        return con
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return None
