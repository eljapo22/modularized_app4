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
    
    def __init__(self):
        self.db_name = "ModApp4DB"
        self.feeders = range(1, 5)

    def connect(self) -> duckdb.DuckDBPyConnection:
        token = st.secrets["motherduck_token"]
        con = duckdb.connect(f'md:{self.db_name}?motherduck_token={token}')
        con.execute("SET enable_progress_bar=false")
        con.execute("SET errors_as_json=true")
        return con
        
    def query_data(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        con = self.connect()
        if params:
            return con.execute(query, params).fetchdf()
        return con.execute(query).fetchdf()
        
    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        """Get transformer data from all feeders"""
        results = []
        for feeder in self.feeders:
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
            df = self.query_data(query, [transformer_id, date_str])
            if not df.empty:
                results.append(df)
        
        return pd.concat(results) if results else pd.DataFrame()

    def get_customer_data(self, customer_id: str, date_str: str) -> pd.DataFrame:
        """Get customer data from all feeders"""
        results = []
        for feeder in self.feeders:
            query = f"""
            SELECT 
                timestamp,
                hour,
                customer_id,
                transformer_id,
                power_kw,
                power_factor,
                power_kva,
                current_a,
                size_kva,
                voltage_v
            FROM customer_feeder_{feeder}
            WHERE customer_id = ?
            AND DATE(timestamp) = DATE(?)
            """
            df = self.query_data(query, [customer_id, date_str])
            if not df.empty:
                results.append(df)
        
        return pd.concat(results) if results else pd.DataFrame()

    def get_transformer_customers(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        """Get all customers for a specific transformer"""
        results = []
        for feeder in self.feeders:
            query = f"""
            SELECT DISTINCT
                c.customer_id,
                c.transformer_id,
                t.size_kva as transformer_size_kva,
                t.loading_percentage
            FROM customer_feeder_{feeder} c
            JOIN transformer_feeder_{feeder} t 
                ON c.transformer_id = t.transformer_id
                AND DATE(c.timestamp) = DATE(t.timestamp)
            WHERE c.transformer_id = ?
            AND DATE(c.timestamp) = DATE(?)
            """
            df = self.query_data(query, [transformer_id, date_str])
            if not df.empty:
                results.append(df)
        
        return pd.concat(results) if results else pd.DataFrame()

    def get_feeder_stats(self, date_str: str) -> pd.DataFrame:
        """Get statistics for all feeders"""
        results = []
        for feeder in self.feeders:
            query = f"""
            SELECT 
                'Feeder {feeder}' as feeder_name,
                COUNT(DISTINCT transformer_id) as transformer_count,
                AVG(loading_percentage) as avg_loading,
                MAX(loading_percentage) as max_loading,
                COUNT(CASE WHEN loading_percentage >= 120 THEN 1 END) as critical_count,
                COUNT(CASE WHEN loading_percentage >= 100 AND loading_percentage < 120 THEN 1 END) as overloaded_count,
                COUNT(CASE WHEN loading_percentage >= 80 AND loading_percentage < 100 THEN 1 END) as warning_count
            FROM transformer_feeder_{feeder}
            WHERE DATE(timestamp) = DATE(?)
            GROUP BY DATE(timestamp)
            """
            df = self.query_data(query, [date_str])
            if not df.empty:
                results.append(df)
        
        return pd.concat(results) if results else pd.DataFrame()

def get_db_adapter() -> DatabaseAdapter:
    """Factory function to get the appropriate database adapter"""
    use_motherduck = st.session_state.get('use_motherduck', False)
    return MotherDuckAdapter() if use_motherduck else LocalDuckDBAdapter()
