"""
Data service implementation for MotherDuck
"""

import pandas as pd
from datetime import datetime, date, timedelta
import logging
from typing import List, Optional, Dict, Tuple
from app.core.database_adapter import DatabaseAdapter
from app.utils.db_utils import execute_query

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
            logger.info("Retrieving feeder options...")
            
            # Hardcoded feeders as fallback
            feeders = ["Feeder 1", "Feeder 2", "Feeder 3", "Feeder 4"]
            
            try:
                # Try to query database
                query = """
                SELECT DISTINCT 
                    'Feeder ' || SUBSTRING(table_name, 19, 1) as feeder
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                AND table_name LIKE 'transformer_feeder_%'
                ORDER BY feeder
                """
                
                result = execute_query(query)
                if result is not None and not result.empty:
                    feeders = result['feeder'].tolist()
            except Exception as e:
                logger.warning(f"Using fallback feeders due to error: {str(e)}")
                
            logger.info(f"Found feeders: {feeders}")
            return feeders
            
        except Exception as e:
            logger.error(f"Error getting feeder options: {str(e)}")
            return ["Feeder 1"]  # Return at least one default feeder
            
    def get_transformer_options(self, feeder_id: str) -> List[str]:
        """Get list of transformers for a specific feeder"""
        try:
            feeder_num = feeder_id.split()[-1] if isinstance(feeder_id, str) and 'Feeder' in feeder_id else 1
            # Convert to int
            try:
                feeder_num = int(feeder_num)
            except:
                feeder_num = 1
                
            query = f"""
            SELECT DISTINCT transformer_id
            FROM transformer_feeder_{feeder_num}
            ORDER BY transformer_id
            """
            
            # First try using execute_query
            try:
                result = execute_query(query)
                if result is not None and not result.empty:
                    return result['transformer_id'].tolist()
            except Exception as e:
                logger.warning(f"Primary query method failed: {str(e)}. Trying backup.")
                
            # If that failed, try using the database adapter directly
            try:
                result = self.db.query_data(query)
                if result is not None and not result.empty:
                    return result['transformer_id'].tolist()
            except Exception as e:
                logger.warning(f"Backup query method failed: {str(e)}. Using fallback values.")
                
            # Return fallback values if all else fails
            return [f"TF{feeder_num}00{i}" for i in range(1, 6)]
            
        except Exception as e:
            logger.error(f"Error getting transformer options: {str(e)}")
            return [f"TF100{i}" for i in range(1, 6)]  # Return some sample transformers
            
    def get_customer_options(self, transformer_id: str) -> List[str]:
        """Get list of customers for a specific transformer"""
        try:
            # First try to extract feeder number from transformer_id
            try:
                if transformer_id and len(transformer_id) >= 4:
                    feeder_num = int(transformer_id[3])  # Extract feeder number from ID like S1F1ATF001
                else:
                    feeder_num = 1
            except:
                feeder_num = 1
                
            query = f"""
            SELECT DISTINCT customer_id
            FROM customer_feeder_{feeder_num}
            WHERE transformer_id = ?
            ORDER BY customer_id
            """
            
            # Try with execute_query first
            try:
                result = execute_query(query, (transformer_id,))
                if result is not None and not result.empty:
                    return result['customer_id'].tolist()
            except Exception as e:
                logger.warning(f"Primary customer query method failed: {str(e)}. Trying backup.")
            
            # Then try with database adapter
            try:
                result = self.db.query_data(query, [transformer_id])
                if result is not None and not result.empty:
                    return result['customer_id'].tolist()
            except Exception as e:
                logger.warning(f"Backup customer query method failed: {str(e)}. Using fallback values.")
            
            # Return fallback values
            return [f"CUST_{transformer_id}_{i}" for i in range(1, 4)]
        except Exception as e:
            logger.error(f"Error getting customer options: {str(e)}")
            return [f"CUST_{i}" for i in range(1, 4)]  # Return sample customer IDs

    def get_available_dates(self) -> Tuple[date, date]:
        """Get the available date range for data queries"""
        try:
            # You could query this from the database, but using constants for simplicity
            return date(2024, 1, 1), date(2024, 6, 30)
        except Exception as e:
            logger.error(f"Error getting available dates: {str(e)}")
            return date(2024, 1, 1), date(2024, 6, 30)
            
    def get_transformer_data_range(
        self, 
        start_date: date,
        end_date: date,
        feeder: str,
        transformer_id: str = None
    ) -> Optional[pd.DataFrame]:
        """Get transformer data for a date range."""
        try:
            logger.info(f"Fetching transformer data from {start_date} to {end_date}")
            
            # Extract feeder number
            feeder_num = int(feeder.split()[-1]) if isinstance(feeder, str) and 'Feeder' in feeder else 1
            
            # Build query
            query = f"""
            SELECT 
                timestamp,
                transformer_id,
                CAST(size_kva AS DECIMAL(5,1)) as size_kva,
                load_range,
                CAST(loading_percentage AS DECIMAL(5,2)) as loading_percentage,
                CAST(current_a AS DECIMAL(6,2)) as current_a,
                CAST(voltage_v AS INTEGER) as voltage_v,
                CAST(power_kw AS DECIMAL(5,2)) as power_kw,
                CAST(power_kva AS DECIMAL(5,2)) as power_kva,
                CAST(power_factor AS DECIMAL(4,3)) as power_factor
            FROM transformer_feeder_{feeder_num}
            WHERE DATE(timestamp) BETWEEN ? AND ?
            """
            
            params = [start_date, end_date]
            
            # Add transformer filter if provided
            if transformer_id:
                query += " AND transformer_id = ?"
                params.append(transformer_id)
                
            query += " ORDER BY timestamp"
            
            # Execute query
            results = execute_query(query, tuple(params))
            
            if results is None or results.empty:
                logger.warning("No transformer data found")
                return None
                
            # Process data
            results['timestamp'] = pd.to_datetime(results['timestamp'])
            results.set_index('timestamp', inplace=True)
            
            logger.info(f"Retrieved {len(results)} records")
            return results
                
        except Exception as e:
            logger.error(f"Error in get_transformer_data_range: {str(e)}")
            return None
