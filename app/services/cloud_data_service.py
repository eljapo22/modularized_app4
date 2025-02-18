"""
Cloud-compatible data service that works with both MotherDuck and Parquet
"""
import os
import pandas as pd
import duckdb
from pathlib import Path
import streamlit as st
from datetime import datetime, date
import json
from typing import Optional, List, Dict, Union
import logging

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        self.use_motherduck = bool(os.getenv("USE_MOTHERDUCK", ""))
        self.data_path = Path(__file__).parent.parent.parent / "data"
        
        if self.use_motherduck:
            self.setup_motherduck()
    
    def setup_motherduck(self):
        """Setup MotherDuck connection if enabled"""
        try:
            token = os.getenv("MOTHERDUCK_TOKEN") or st.secrets["MOTHERDUCK_TOKEN"]
            self.conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        except Exception as e:
            logger.error(f"MotherDuck connection failed: {str(e)}")
            self.use_motherduck = False
    
    @st.cache_data(ttl="1h")
    def get_feeder_data(self, feeder: int) -> pd.DataFrame:
        """Get data for a specific feeder"""
        try:
            if self.use_motherduck:
                return self._get_feeder_data_motherduck(feeder)
            else:
                return self._get_feeder_data_parquet(feeder)
        except Exception as e:
            logger.error(f"Error getting feeder {feeder} data: {str(e)}")
            return pd.DataFrame()
    
    def _get_feeder_data_motherduck(self, feeder: int) -> pd.DataFrame:
        """Get feeder data from MotherDuck"""
        query = f"""
            SELECT *
            FROM transformer_readings
            WHERE feeder_id = {feeder}
            AND timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """
        return self.conn.execute(query).df()
    
    def _get_feeder_data_parquet(self, feeder: int) -> pd.DataFrame:
        """Get feeder data from Parquet files"""
        feeder_path = self.data_path / f"feeder{feeder}" / "data.parquet"
        if feeder_path.exists():
            return pd.read_parquet(feeder_path)
        return pd.DataFrame()
    
    @st.cache_data(ttl="24h")
    def get_transformer_ids(self, feeder: int) -> List[str]:
        """Get transformer IDs for a feeder"""
        try:
            if self.use_motherduck:
                return self._get_transformer_ids_motherduck(feeder)
            else:
                return self._get_transformer_ids_parquet(feeder)
        except Exception as e:
            logger.error(f"Error getting transformer IDs for feeder {feeder}: {str(e)}")
            return []
    
    def _get_transformer_ids_motherduck(self, feeder: int) -> List[str]:
        """Get transformer IDs from MotherDuck"""
        query = f"""
            SELECT DISTINCT transformer_id
            FROM transformer_readings
            WHERE feeder_id = {feeder}
            ORDER BY transformer_id
        """
        return self.conn.execute(query).df()['transformer_id'].tolist()
    
    def _get_transformer_ids_parquet(self, feeder: int) -> List[str]:
        """Get transformer IDs from Parquet metadata"""
        metadata_path = self.data_path / f"feeder{feeder}" / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                return json.load(f)['transformer_ids']
        return []
    
    @st.cache_data(ttl="1h")
    def get_transformer_data(self, transformer_id: str, selected_date: date) -> pd.DataFrame:
        """Get data for a specific transformer on a specific date"""
        try:
            if self.use_motherduck:
                return self._get_transformer_data_motherduck(transformer_id, selected_date)
            else:
                return self._get_transformer_data_parquet(transformer_id, selected_date)
        except Exception as e:
            logger.error(f"Error getting transformer {transformer_id} data: {str(e)}")
            return pd.DataFrame()
    
    def _get_transformer_data_motherduck(self, transformer_id: str, selected_date: date) -> pd.DataFrame:
        """Get transformer data from MotherDuck"""
        query = f"""
            SELECT *
            FROM transformer_readings
            WHERE transformer_id = '{transformer_id}'
            AND DATE(timestamp) = DATE '{selected_date}'
        """
        return self.conn.execute(query).df()
    
    def _get_transformer_data_parquet(self, transformer_id: str, selected_date: date) -> pd.DataFrame:
        """Get transformer data from Parquet files"""
        # Find the feeder file containing this transformer
        for feeder in range(1, 5):
            df = self._get_feeder_data_parquet(feeder)
            if transformer_id in df['transformer_id'].unique():
                mask = (df['transformer_id'] == transformer_id) & (pd.to_datetime(df['timestamp']).dt.date == selected_date)
                return df[mask]
        return pd.DataFrame()

# Initialize the service
data_service = DataService()
