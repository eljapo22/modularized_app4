"""
Cloud-specific data service implementation
"""

import pandas as pd
from datetime import datetime, date
import logging
from typing import List, Optional, Tuple, Dict

from app.config.database_config import (
    TRANSFORMER_DATA_QUERY,
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
    execute_query,
    get_all_transformer_tables,
    get_all_customer_tables
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
            # Initialize database connection pool
            init_db_pool()
            
            # Cache for transformer IDs
            self._transformer_ids: Optional[List[str]] = None
            
            # Dataset date range
            self.min_date = date(2024, 1, 1)
            self.max_date = date(2024, 6, 28)
            
            logger.info("CloudDataService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing CloudDataService: {str(e)}")
            raise
    
    def get_feeder_options(self) -> List[str]:
        """Get list of available feeders"""
        return ["Transformer Feeder 1"]  # Currently fixed as per UI requirement
    
    def get_load_options(self, feeder: str) -> List[str]:
        """Get list of available transformer IDs"""
        if self._transformer_ids is None:
            try:
                transformer_ids = set()
                for table in get_all_transformer_tables():
                    query = TRANSFORMER_LIST_QUERY.format(table_name=table)
                    results = execute_query(query)
                    if results:
                        transformer_ids.update(row['transformer_id'] for row in results)
                self._transformer_ids = sorted(list(transformer_ids))
                logger.info(f"Found {len(self._transformer_ids)} unique transformer IDs")
            except Exception as e:
                logger.error(f"Error getting transformer IDs: {str(e)}")
                return []
        return self._transformer_ids
    
    def get_available_dates(self) -> Tuple[date, date]:
        """Get the available date range for data queries"""
        try:
            logger.info(f"Available date range: {self.min_date} to {self.max_date}")
            return self.min_date, self.max_date
        except Exception as e:
            logger.error(f"Error getting available dates: {str(e)}")
            return self.min_date, self.max_date
    
    def get_transformer_data(
        self,
        date: datetime,
        hour: int,
        feeder: str,
        transformer_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Get transformer data for the specified parameters
        
        Args:
            date: Date to get data for
            hour: Hour of the day (0-23)
            feeder: Feeder name (currently fixed)
            transformer_id: Transformer ID (e.g., SP1MT7501)
            
        Returns:
            DataFrame with transformer data or None if no data available
        """
        try:
            # Check if date is within range
            if not (self.min_date <= date.date() <= self.max_date):
                logger.warning(f"Date {date} is outside available range")
                return None
            
            # Get data from all transformer tables
            all_data = []
            for table in get_all_transformer_tables():
                query = TRANSFORMER_DATA_QUERY.format(table_name=table)
                results = execute_query(query, (transformer_id, date.date(), hour))
                if results:
                    all_data.extend(results)
            
            if not all_data:
                logger.warning(f"No transformer data found for {transformer_id} on {date} hour {hour}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            return df
            
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            return None
    
    def get_customer_data(
        self,
        transformer_id: str,
        date: datetime,
        hour: int
    ) -> Optional[pd.DataFrame]:
        """Get customer data for a specific transformer"""
        try:
            all_data = []
            for table in get_all_customer_tables():
                query = CUSTOMER_DATA_QUERY.format(table_name=table)
                results = execute_query(query, (transformer_id, date.date(), hour))
                if results:
                    all_data.extend(results)
            
            if not all_data:
                logger.warning(f"No customer data found for transformer {transformer_id}")
                return None
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            logger.error(f"Error getting customer data: {str(e)}")
            return None
    
    def get_customer_aggregation(
        self,
        transformer_id: str,
        date: datetime,
        hour: int
    ) -> Optional[AggregatedCustomerData]:
        """Get aggregated customer metrics for a transformer"""
        try:
            all_data = []
            for table in get_all_customer_tables():
                query = CUSTOMER_AGGREGATION_QUERY.format(table_name=table)
                results = execute_query(query, (transformer_id, date.date(), hour))
                if results:
                    all_data.extend(results)
            
            if not all_data:
                logger.warning(f"No customer aggregation data found for transformer {transformer_id}")
                return None
            
            # Combine results from all tables
            agg_data = {
                'transformer_id': transformer_id,
                'customer_count': sum(row['customer_count'] for row in all_data),
                'total_power_kw': sum(row['total_power_kw'] for row in all_data),
                'avg_power_factor': sum(row['avg_power_factor'] * row['customer_count'] for row in all_data) / sum(row['customer_count'] for row in all_data),
                'total_power_kva': sum(row['total_power_kva'] for row in all_data),
                'avg_voltage_v': sum(row['avg_voltage_v'] * row['customer_count'] for row in all_data) / sum(row['customer_count'] for row in all_data),
                'total_current_a': sum(row['total_current_a'] for row in all_data)
            }
            
            return AggregatedCustomerData(**agg_data)
            
        except Exception as e:
            logger.error(f"Error getting customer aggregation: {str(e)}")
            return None

# Initialize the service as a singleton
logger.info("Initializing CloudDataService singleton")
data_service = CloudDataService()
logger.info("CloudDataService initialization complete")
