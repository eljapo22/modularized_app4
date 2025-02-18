"""
Database adapter layer to support both local DuckDB and MotherDuck connections
"""

import os
import streamlit as st
import duckdb
from abc import ABC, abstractmethod
from typing import Optional, Union, List
import pandas as pd

class DatabaseAdapter(ABC):
    """Abstract base class for database operations"""
    
    @abstractmethod
    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish database connection"""
        pass
        
    @abstractmethod
    def query_data(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute query and return results"""
        pass
        
    @abstractmethod
    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        """Get transformer data using implementation-specific method"""
        pass

class LocalDuckDBAdapter(DatabaseAdapter):
    """Adapter for local DuckDB with parquet files"""
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect(database=':memory:', read_only=False)
        con.execute("SET enable_progress_bar=false")
        con.execute("SET errors_as_json=true")
        return con
        
    def query_data(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        con = self.connect()
        if params:
            return con.execute(query, params).fetchdf()
        return con.execute(query).fetchdf()
        
    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        base_path = os.path.join("C:", "Users", "JohnApostolo", "CascadeProjects", 
                                "processed_data", "transformer_analysis", "hourly")
        query = """
        SELECT *
        FROM read_parquet(?)
        WHERE transformer_id = ?
        AND DATE(timestamp) = DATE(?)
        """
        return self.query_data(query, [f"{base_path}/{date_str}.parquet", transformer_id, date_str])

class MotherDuckAdapter(DatabaseAdapter):
    """Adapter for MotherDuck cloud database"""
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        token = st.secrets.get("motherduck_token", "")
        con = duckdb.connect(f'md:transformer_analysis?motherduck_token={token}')
        con.execute("SET enable_progress_bar=false")
        con.execute("SET errors_as_json=true")
        return con
        
    def query_data(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        con = self.connect()
        if params:
            return con.execute(query, params).fetchdf()
        return con.execute(query).fetchdf()
        
    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        query = """
        SELECT *
        FROM transformer_readings
        WHERE transformer_id = ?
        AND DATE(timestamp) = DATE(?)
        """
        return self.query_data(query, [transformer_id, date_str])

def get_db_adapter() -> DatabaseAdapter:
    """Factory function to get the appropriate database adapter"""
    use_motherduck = st.session_state.get('use_motherduck', False)
    return MotherDuckAdapter() if use_motherduck else LocalDuckDBAdapter()
