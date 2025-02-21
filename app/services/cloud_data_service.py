"""
Cloud-specific data service implementation
"""

import pandas as pd
from datetime import datetime, date, timedelta
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
    FEEDER_NUMBERS
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
            
            # Dataset date range
            self.min_date = date(2024, 1, 1)
            self.max_date = date(2024, 6, 28)
            
            logger.info(f"CloudDataService initialized with date range: {self.min_date} to {self.max_date}")
        except Exception as e:
            logger.error(f"Error initializing CloudDataService: {str(e)}")
            raise

    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        logger.info("Retrieving feeder options...")
        feeders = [f"Feeder {num}" for num in FEEDER_NUMBERS]
        logger.info(f"Found {len(feeders)} feeders: {feeders}")
        return feeders

    def get_load_options(self, feeder: str) -> List[str]:
        """Get list of available transformer IDs"""
        try:
            logger.info(f"Retrieving transformer IDs for {feeder}...")
            # Extract feeder number from string like "Feeder 1"
            feeder_num = int(feeder.split()[-1])
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                raise ValueError(f"Invalid feeder number: {feeder_num}")
                
            if self._transformer_ids is None:
                # Table name already includes quotes
                table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
                logger.debug(f"Querying transformer IDs from table: {table}")
                query = TRANSFORMER_LIST_QUERY.format(table_name=table)
                results = execute_query(query)
                self._transformer_ids = [r['transformer_id'] for r in results]
                logger.info(f"Found {len(self._transformer_ids)} transformers")
                logger.debug(f"Transformer IDs: {self._transformer_ids}")
            return sorted(self._transformer_ids)
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_available_dates(self) -> tuple[date, date]:
        """Get the available date range for data queries"""
        logger.info(f"Returning date range: {self.min_date} to {self.max_date}")
        return self.min_date, self.max_date

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
                return pd.DataFrame(results)
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
        
        Args:
            start_date (date): Start date for the query
            end_date (date): End date for the query
            feeder (str): Feeder identifier
            transformer_id (str): Transformer identifier
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with transformer data or None if error
        """
        try:
            logger.info(f"Fetching transformer data for {transformer_id} from {start_date} to {end_date}")
            
            # Extract feeder number
            feeder_num = int(feeder.split()[-1])
            if feeder_num not in FEEDER_NUMBERS:
                logger.error(f"Invalid feeder number: {feeder_num}")
                return None
            
            # Get table name
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Execute query
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            results = execute_query(
                query, 
                params=(transformer_id, start_date, end_date)
            )
            
            if not results:
                logger.warning(f"No data found for transformer {transformer_id} in date range")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Sort by timestamp
            df.sort_index(inplace=True)
            
            logger.info(f"Retrieved {len(df)} records for transformer {transformer_id}")
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
            feeder_num = feeder.split('_')[-1]
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Use the range query but with a specific end time
            query = TRANSFORMER_DATA_RANGE_QUERY.format(table_name=table)
            params = (transformer_id, start_date, end_time)
            
            results = execute_query(query, params)
            if not results:
                logger.warning(f"No data found for transformer {transformer_id} in range")
                return None
                
            # Convert to DataFrame and process
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting transformer data to point: {str(e)}")
            return None

    def get_customer_data(
        self,
        transformer_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """Get customer data for a specific transformer and date range"""
        try:
            logger.info(f"Fetching customer data for {transformer_id} from {start_date} to {end_date}")
            
            # Get table name from transformer ID
            feeder_num = int(transformer_id.split('_')[0])
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder_num)
            
            # Execute query
            query = CUSTOMER_DATA_QUERY.format(table_name=table)
            results = execute_query(
                query,
                params=(transformer_id, start_date, end_date)
            )
            
            if not results:
                logger.warning(f"No customer data found for transformer {transformer_id}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Retrieved {len(df)} customer records")
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
            
            # Get table name from transformer ID
            feeder_num = int(transformer_id.split('_')[0])
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
                
            # Process results into a dictionary
            agg_data = {
                'dates': [],
                'customer_ids': [],
                'avg_power': [],
                'max_power': [],
                'min_power': [],
                'avg_pf': []
            }
            
            for row in results:
                agg_data['dates'].append(row['date'])
                agg_data['customer_ids'].append(row['customer_id'])
                agg_data['avg_power'].append(row['avg_power_kw'])
                agg_data['max_power'].append(row['max_power_kw'])
                agg_data['min_power'].append(row['min_power_kw'])
                agg_data['avg_pf'].append(row['avg_power_factor'])
            
            logger.info(f"Retrieved aggregation data for {len(agg_data['customer_ids'])} customers")
            return agg_data
            
        except Exception as e:
            logger.error(f"Error getting customer aggregation: {str(e)}")
            return None

# Initialize the service as a singleton
logger.info("Initializing CloudDataService singleton")
data_service = CloudDataService()
logger.info("CloudDataService initialization complete")
