"""
Data service implementation for MotherDuck
"""

import pandas as pd
from datetime import datetime, date, timedelta
import logging
from typing import List, Optional, Dict
from app.core.database_adapter import DatabaseAdapter

logger = logging.getLogger(__name__)

class CloudDataService:
    """Service class for handling data operations"""
    
    def __init__(self):
        """Initialize the data service with database adapter"""
        self.db = DatabaseAdapter()
        logger.info("CloudDataService initialized")
        
    def get_transformer_data(self, transformer_id: str, date_str: str) -> pd.DataFrame:
        """Get transformer data for a specific date"""
        try:
            data = self.db.get_transformer_data(transformer_id, date_str)
            if data.empty:
                logger.warning(f"No data found for transformer {transformer_id} on {date_str}")
            return data
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            return pd.DataFrame()
            
    def get_customer_data(self, customer_id: str, date_str: str) -> pd.DataFrame:
        """Get customer data for a specific date"""
        try:
            data = self.db.get_customer_data(customer_id, date_str)
            if data.empty:
                logger.warning(f"No data found for customer {customer_id} on {date_str}")
            return data
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return pd.DataFrame()
            
    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        try:
            query = """
            SELECT DISTINCT 
                SUBSTRING(transformer_id, 1, 4) as feeder_id 
            FROM transformer_feeder_1
            UNION
            SELECT DISTINCT 
                SUBSTRING(transformer_id, 1, 4) as feeder_id 
            FROM transformer_feeder_2
            UNION
            SELECT DISTINCT 
                SUBSTRING(transformer_id, 1, 4) as feeder_id 
            FROM transformer_feeder_3
            UNION
            SELECT DISTINCT 
                SUBSTRING(transformer_id, 1, 4) as feeder_id 
            FROM transformer_feeder_4
            ORDER BY feeder_id
            """
            result = self.db.query_data(query)
            return result['feeder_id'].tolist()
        except Exception as e:
            logger.error(f"Error getting feeder options: {str(e)}")
            return []
            
    def get_transformer_options(self, feeder_id: str) -> List[str]:
        """Get list of transformers for a specific feeder"""
        try:
            feeder_num = int(feeder_id[3])  # Extract feeder number from ID
            query = f"""
            SELECT DISTINCT transformer_id
            FROM transformer_feeder_{feeder_num}
            WHERE transformer_id LIKE ?
            ORDER BY transformer_id
            """
            result = self.db.query_data(query, [f"{feeder_id}%"])
            return result['transformer_id'].tolist()
        except Exception as e:
            logger.error(f"Error getting transformer options: {str(e)}")
            return []
            
    def get_customer_options(self, transformer_id: str) -> List[str]:
        """Get list of customers for a specific transformer"""
        try:
            feeder_num = int(transformer_id[3])  # Extract feeder number from ID
            query = f"""
            SELECT DISTINCT customer_id
            FROM customer_feeder_{feeder_num}
            WHERE transformer_id = ?
            ORDER BY customer_id
            """
            result = self.db.query_data(query, [transformer_id])
            return result['customer_id'].tolist()
        except Exception as e:
            logger.error(f"Error getting customer options: {str(e)}")
            return []
