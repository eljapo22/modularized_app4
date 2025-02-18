"""
Database connection and management for the Transformer Loading Analysis Application
"""

import os
import streamlit as st
import duckdb

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
    """Get a cached DuckDB connection"""
    con = duckdb.connect(database=':memory:', read_only=False)
    con.execute("SET enable_progress_bar=false")
    con.execute("SET errors_as_json=true")
    return con
