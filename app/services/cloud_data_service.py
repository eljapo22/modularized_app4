"""
Cloud-specific data service implementation
"""

import pandas as pd
from datetime import datetime, date, time, timedelta
import logging
from typing import List, Optional, Dict

from app.config.database_config import (
    TRANSFORMER_DATA_QUERY,
    TRANSFORMER_DATA_RANGE_QUERY,
    CUSTOMER_DATA_QUERY,
    TRANSFORMER_LIST_QUERY,
    CUSTOMER_AGGREGATION_QUERY
)
from app.config.table_config import (
    TRANSFORMER_TABLE_TEMPLATE,
    CUSTOMER_TABLE_TEMPLATE,
    FEEDER_NUMBERS,
    DECIMAL_PLACES
)
from app.utils.db_utils import (
    init_db_pool,
    execute_query
)
from app.models.data_models import (
    TransformerData,
    CustomerData,
    AggregatedCustomerData
)
from app.utils.data_validation import validate_transformer_data, analyze_trends

# Initialize logger
logger = logging.getLogger(__name__)

class CloudDataService:
    """Service class for handling data operations in the cloud environment"""
    
    def __init__(self):
        """Initialize the data service"""
        try:
            logger.info("Initializing CloudDataService...")
            # Initialize database connection pool
            init_db_pool()
            logger.info("Database pool initialized successfully")
            
            # Cache for transformer IDs
            self._transformer_ids: Optional[List[str]] = None
            
            # Cache for available feeders
            self._available_feeders: Optional[List[str]] = None
            
            # Dataset date range
            self.min_date = date(2024, 1, 1)
            self.max_date = date(2024, 6, 28)
            
            logger.info(f"CloudDataService initialized with date range: {self.min_date} to {self.max_date}")
        except Exception as e:
            logger.error(f"Error initializing CloudDataService: {str(e)}")
            raise

    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        if self._available_feeders is None:
            logger.info("Getting feeder options...")
            self._available_feeders = [f"Feeder {num}" for num in FEEDER_NUMBERS]
            logger.info(f"Found {len(self._available_feeders)} feeders: {self._available_feeders}")
        return self._available_feeders

    def get_transformer_ids(self, feeder_num: int) -> List[str]:
        """Get list of transformer IDs for a specific feeder"""
        try:
            logger.info(f"Retrieving transformer IDs for feeder {feeder_num}...")
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                return []
            
            # Use the correct table name format
            table = f'"Transformer Feeder {feeder_num}"'
            logger.debug(f"Querying transformer IDs from table: {table}")
            
            try:
                query = TRANSFORMER_LIST_QUERY.format(table_name=table)
                results = execute_query(query)
                
                if results:
                    transformer_ids = [r['transformer_id'] for r in results]
                    logger.info(f"Found {len(transformer_ids)} transformers")
                    logger.debug(f"Transformer IDs: {transformer_ids}")
                    return sorted(transformer_ids)
                else:
                    logger.warning(f"No transformers found for feeder {feeder_num}")
                    return []
            except Exception as e:
                logger.error(f"Database error getting transformer IDs: {str(e)}")
                # Return a default list of transformers for this feeder
                default_ids = [f"S1F{feeder_num}ATF{i:03d}" for i in range(1, 11)]
                logger.info(f"Using default transformer IDs: {default_ids}")
                return default_ids
                
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_load_options(self, feeder: str) -> List[str]:
        """Get list of available transformer IDs"""
        try:
            logger.info(f"Retrieving transformer IDs for {feeder}...")
            # Extract feeder number from string like "Feeder 1"
            feeder_num = int(feeder.split()[-1])
            return self.get_transformer_ids(feeder_num)
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_available_dates(self) -> tuple[date, date]:
        """Get the available date range for data queries"""
        logger.info(f"Returning date range: {self.min_date} to {self.max_date}")
        return self.min_date, self.max_date

    def _format_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format numeric columns with proper decimal places"""
        if df is None or df.empty:
            return df
            
        # Apply formatting to each numeric column based on configuration
        for col, decimals in DECIMAL_PLACES.items():
            if col in df.columns:
                df[col] = df[col].round(decimals)
        
        return df

    def get_transformer_data(self, date: datetime, hour: int, feeder: str, transformer_id: str) -> Optional[pd.DataFrame]:
        """
        Get transformer data for a specific date and hour.
        
        Args:
            date (datetime): The datetime object for the query
            hour (int): Hour of the day (0-23)
            feeder (str): Feeder identifier
            transformer_id (str): Transformer identifier
        
        Returns:
            Optional[pd.DataFrame]: DataFrame containing transformer data or None if no data found
        """
        try:
            # Extract just the date part for the query
            query_date = date.date()
            
            # Extract feeder number from string like "Feeder 1"
            feeder_num = int(feeder.split()[-1])
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                raise ValueError(f"Invalid feeder number: {feeder_num}")
                
            # Table name already includes quotes
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            logger.debug(f"Querying table: {table}")
            query = TRANSFORMER_DATA_QUERY.format(table_name=table)
            results = execute_query(query, (transformer_id, query_date, hour))
            
            if results and len(results) > 0:
                df = pd.DataFrame(results)
                df = self._format_numeric_columns(df)
                return df
            return None
            
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            raise

    def get_transformer_data_range(
        self,
        start_date: date, 
        end_date: date, 
        feeder: str, 
        transformer_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Get transformer data for a date range.
        """
        try:
            logger.info(f"Fetching transformer data for {transformer_id}")
            
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Convert dates to timestamps for the query
            start_ts = datetime.combine(start_date, time.min)
            end_ts = datetime.combine(end_date, time.max)
            
            # Execute query
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            params = (transformer_id, start_ts, end_ts)
            
            results = execute_query(query, params)
            if not results:
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Print first few rows of raw data for debugging
            logger.info("First 5 rows of raw data:")
            logger.info(df.head().to_string())
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Print some sequential rows to check for cumulative values
            logger.info("\nSample of sequential power readings:")
            sample_size = min(10, len(df))
            logger.info(df[['timestamp', 'power_kw']].head(sample_size).to_string())
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting transformer data range: {str(e)}")
            return None

    def get_transformer_data_to_point(
        self,
        start_date: date,
        end_time: datetime,
        feeder: str,
        transformer_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Get transformer data from start date up to a specific point in time
        
        Args:
            start_date: Start date for the query
            end_time: End datetime for the query
            feeder: Feeder identifier
            transformer_id: Transformer identifier
            
        Returns:
            DataFrame with transformer data or None if error
        """
        try:
            # Get feeder number from feeder string
            feeder_num = int(feeder.split()[-1])  # Fixed: use space split instead of underscore
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Use the range query but with a specific end time
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            start_ts = datetime.combine(start_date, time.min)
            params = (transformer_id, start_ts, end_time)  # Fixed: correct parameter order
            
            results = execute_query(query, params)
            if not results:
                logger.warning(f"No data found for transformer {transformer_id} in range")
                return None
                
            # Convert to DataFrame and process
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Apply numeric formatting
            df = self._format_numeric_columns(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting transformer data to point: {str(e)}")
            return None

    def get_transformer_data_by_range(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date,
        hour: int,
        feeder: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """Get transformer data for a specific date range and hour"""
        try:
            logger.info(f"Fetching data for transformer {transformer_id} from {start_date} to {end_date} at hour {hour}")
            
            # Get feeder number from transformer ID if not provided
            if feeder is None and transformer_id:
                feeder = int(transformer_id[2]) if len(transformer_id) >= 3 else 1
                
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder)
            
            # Create timestamps for the query
            start_ts = datetime.combine(start_date, time.min.replace(hour=hour))
            end_ts = datetime.combine(end_date, time.min.replace(hour=hour))
            
            # Execute query with hour filter
            query = f"""
                SELECT *
                FROM "{table}"
                WHERE transformer_id = %s
                AND timestamp >= %s
                AND timestamp <= %s
                AND EXTRACT(hour FROM timestamp) = %s
                ORDER BY timestamp
            """
            params = (transformer_id, start_ts, end_ts, hour)
            
            results = execute_query(query, params)
            
            if not results:
                logger.warning(f"No data found for transformer {transformer_id} in date range")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df.set_index('timestamp', inplace=True)
            
            # Validate and analyze data
            df = validate_transformer_data(df)
            df = analyze_trends(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching transformer data range: {str(e)}")
            return None

    def get_customer_data(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Get customer data for a specific transformer and date range.
        """
        try:
            logger.info(f"Fetching customer data for transformer {transformer_id}")
            logger.info(f"Date range: {start_date} to {end_date}")
            
            # Extract feeder number from transformer ID (format: S1F2ATF001)
            feeder_num = int(transformer_id[3])  # Position 3 is the feeder number
            
            # Get table name
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder_num)
            logger.info(f"Using table: {table}")
            
            # Convert dates to timestamps for the query
            start_ts = datetime.combine(start_date, time.min)
            end_ts = datetime.combine(end_date, time.max)
            
            # Execute query with all required parameters
            query = CUSTOMER_DATA_QUERY.format(table_name=table)
            results = execute_query(
                query,
                params=(start_ts, end_ts, transformer_id, start_date, end_date)  # All 5 parameters for the query
            )
            
            if not results:
                logger.warning(f"No customer data found for transformer {transformer_id}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Apply numeric formatting
            df = self._format_numeric_columns(df)
            
            logger.info(f"Data timestamp range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            logger.info(f"Retrieved {len(df)} records")
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return None
            
    def get_customer_aggregation(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[Dict]:
        """Get aggregated customer metrics for a transformer"""
        try:
            logger.info(f"Getting customer aggregation for {transformer_id}")
            
            # Extract feeder number from transformer ID (format: S1F1ATF001)
            feeder_num = int(transformer_id.split('F')[0].replace('S', ''))
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Execute query
            query = CUSTOMER_AGGREGATION_QUERY.format(table_name=table)
            results = execute_query(
                query,
                params=(transformer_id, start_date, end_date)
            )
            
            if not results:
                logger.warning(f"No customer aggregation data found")
                return None
                
            # Process results into an object with attributes
            class AggregationData:
                def __init__(self, data_dict):
                    self.__dict__.update(data_dict)
            
            agg_data = {
                'dates': [r['date'] for r in results],
                'customer_ids': [r['customer_id'] for r in results],
                'avg_power': [r['avg_power_kw'] for r in results],
                'max_power': [r['max_power_kw'] for r in results],
                'min_power': [r['min_power_kw'] for r in results],
                'avg_pf': [r['avg_power_factor'] for r in results],
                'customer_count': len(set(r['customer_id'] for r in results))
            }
            
            logger.info(f"Retrieved aggregation data for {agg_data['customer_count']} customers")
            return AggregationData(agg_data)
            
        except Exception as e:
            logger.error(f"Error getting customer aggregation: {str(e)}")
            return None
