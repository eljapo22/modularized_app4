"""
Data service implementation for MotherDuck
"""

import pandas as pd
from datetime import datetime, date, timedelta
import logging
from typing import List, Optional, Dict, Tuple
from app.core.database_adapter import DatabaseAdapter
from app.utils.db_utils import execute_query, extract_feeder_number

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
            
    def get_customer_data(
        self, 
        transformer_id: str, 
        start_date: Union[date, datetime], 
        end_date: Union[date, datetime] = None
    ) -> pd.DataFrame:
        """Get customer data for a specific transformer"""
        try:
            # If no end date provided, use start date
            if end_date is None:
                end_date = start_date
            
            # Ensure dates are datetime
            if isinstance(start_date, date):
                start_date = datetime.combine(start_date, datetime.min.time())
            if isinstance(end_date, date):
                end_date = datetime.combine(end_date, datetime.max.time())
            
            logger.info(f"Retrieving customer data for transformer {transformer_id}")
            logger.info(f"Date range: {start_date} to {end_date}")
            
            # Extract feeder number from transformer ID
            try:
                import re
                match = re.search(r'F(\d+)', transformer_id)
                feeder_num = int(match.group(1)) if match else 1
            except Exception as e:
                logger.warning(f"Feeder extraction failed: {str(e)}")
                feeder_num = 1
            
            # Use correct table name with quotes
            table_name = f'"Customer Feeder {feeder_num}"'
            
            # Comprehensive query
            query = f"""
            SELECT 
                timestamp,
                customer_id,
                transformer_id,
                CAST(power_kw AS DECIMAL(5,2)) as power_kw,
                CAST(current_a AS DECIMAL(5,2)) as current_a,
                CAST(voltage_v AS DECIMAL(5,1)) as voltage_v,
                CAST(power_kva AS DECIMAL(5,2)) as power_kva
            FROM {table_name}
            WHERE transformer_id = ? 
            AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
            """
            
            # Execute query
            results = execute_query(query, (transformer_id, start_date, end_date))
            
            if results is None or len(results) == 0:
                logger.warning(f"No customer data found for transformer {transformer_id}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Retrieved {len(df)} customer records")
            return df
            
        except Exception as e:
            logger.error(f"Comprehensive error in get_customer_data: {str(e)}")
            return pd.DataFrame()
            
    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        try:
            logger.info("Retrieving feeder options...")
            
            # Hardcoded feeders as fallback
            feeders = ["Feeder 1", "Feeder 2", "Feeder 3", "Feeder 4"]
            
            try:
                # Try to query database using correct table names
                query = """
                SELECT DISTINCT 
                    'Feeder ' || SUBSTRING(table_name, 19, 1) as feeder
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                AND table_name LIKE 'Transformer Feeder %'
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
            logger.info(f"Retrieving transformer options for feeder '{feeder_id}'")
            
            # Extract feeder number using the robust function
            feeder_num = extract_feeder_number(feeder_id)
             
            # Use correct table name with quotes   
            table_name = f'"Transformer Feeder {feeder_num}"'
            
            query = f"""
            SELECT DISTINCT transformer_id
            FROM {table_name}
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
            logger.info(f"Retrieving customer options for transformer '{transformer_id}'")
            
            # Extract feeder number from transformer ID
            feeder_num = 1  # Default
            
            try:
                if isinstance(transformer_id, str):
                    # Try to extract from S1F1ATF format
                    import re
                    match = re.search(r'F(\d+)', transformer_id)
                    if match:
                        feeder_num = int(match.group(1))
                    else:
                        # Fallback to extracting any digit
                        digits = [c for c in transformer_id if c.isdigit()]
                        if digits:
                            feeder_num = int(digits[0])
            except Exception as e:
                logger.warning(f"Feeder number extraction failed: {str(e)}")
            
            # Use correct table name with quotes
            table_name = f'"Customer Feeder {feeder_num}"'
                
            query = f"""
            SELECT DISTINCT customer_id
            FROM {table_name}
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
            logger.info(f"Fetching transformer data from {start_date} to {end_date} for feeder '{feeder}'")
            
            # Extract feeder number using the robust function
            feeder_num = extract_feeder_number(feeder)
            
            # Use correct table name with quotes
            table_name = f'"Transformer Feeder {feeder_num}"'
            
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
            FROM {table_name}
            WHERE timestamp::DATE BETWEEN ?::DATE AND ?::DATE
            """
            
            params = [start_date, end_date]
            
            # Add transformer filter if provided
            if transformer_id:
                query += " AND transformer_id = ?"
                params.append(transformer_id)
                
            query += " ORDER BY timestamp"
            
            # Execute query
            results = execute_query(query, tuple(params))
            
            # Handle empty results
            if results is None or results.empty:
                logger.warning(f"No data found for query against {table_name}")
                logger.debug(f"Query: {query}")
                logger.debug(f"Parameters: {params}")
                return None
                
            # Validate and clean the data
            from app.utils.data_validation import validate_transformer_data
            results = validate_transformer_data(results)
            
            # Process data if not empty after validation
            if not results.empty:
                if 'timestamp' in results.columns:
                    results['timestamp'] = pd.to_datetime(results['timestamp'])
                    results.set_index('timestamp', inplace=True)
                
                logger.info(f"Retrieved {len(results)} records")
                return results
            else:
                logger.warning("No valid data after validation")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_transformer_data_range: {str(e)}")
            return None

    def _select_alert_point(self, results_df: pd.DataFrame) -> Optional[pd.Series]:
        """Select the point to alert on"""
        try:
            # Find the row with maximum loading
            if 'loading_percentage' not in results_df.columns:
                logger.error("'loading_percentage' column not found in results")
                return None
                
            # Find max loading safely
            max_loading_idx = results_df['loading_percentage'].idxmax()
            max_loading_row = results_df.loc[max_loading_idx]
            
            # Get the loading value (safely convert to float first)
            max_loading_value = float(max_loading_row['loading_percentage'])
            
            # Log the max loading found (avoid using f-string with Series directly)
            logger.info(f"Found max loading: {max_loading_value:.1f}% at {max_loading_idx}")
            
            # Only alert if loading is high enough
            if max_loading_value >= 80:
                return max_loading_row
            else:
                logger.info(f"Max loading {max_loading_value:.1f}% below alert threshold (80%)")
                return None
                
        except Exception as e:
            logger.error(f"Error selecting alert point: {str(e)}")
            return None
