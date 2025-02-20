"""
Cloud-specific data service implementation
"""

import pandas as pd
from datetime import datetime, date
import logging
from typing import List, Optional, Dict

from app.config.database_config import (
    TRANSFORMER_DATA_QUERY,
    CUSTOMER_DATA_QUERY,
    TRANSFORMER_LIST_QUERY,
    CUSTOMER_AGGREGATION_QUERY
)
from app.config.table_config import (
    TRANSFORMER_TABLE_TEMPLATE,
    CUSTOMER_TABLE_TEMPLATE
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
        return ["Feeder 1"]  # For now, we'll just use a single feeder

    def get_load_options(self, feeder: str) -> List[str]:
        """Get list of available transformer IDs"""
        try:
            if self._transformer_ids is None:
                table = TRANSFORMER_TABLE_TEMPLATE.format(feeder)
                query = TRANSFORMER_LIST_QUERY.format(table_name=table)
                results = execute_query(query)
                self._transformer_ids = [r['transformer_id'] for r in results]
            return sorted(self._transformer_ids)
        except Exception as e:
            logger.error(f"Error getting transformer IDs: {str(e)}")
            return []

    def get_available_dates(self) -> tuple[date, date]:
        """Get the available date range for data queries"""
        return self.min_date, self.max_date

    def get_transformer_data(
            self,
            date: datetime,
            hour: int,
            feeder: str,
            transformer_id: str
        ) -> Optional[TransformerData]:
        """
        Get transformer data for the specified parameters
        """
        try:
            table = TRANSFORMER_TABLE_TEMPLATE.format(feeder)
            query = TRANSFORMER_DATA_QUERY.format(table_name=table)
            results = execute_query(
                query,
                (transformer_id, date.date(), hour)
            )
            
            if not results:
                return None
                
            return TransformerData(
                transformer_id=transformer_id,
                timestamp=[r['timestamp'] for r in results],
                power_kw=[r['power_kw'] for r in results],
                power_kva=[r['power_kva'] for r in results],
                power_factor=[r['power_factor'] for r in results],
                voltage_v=[r['voltage_v'] for r in results],
                current_a=[r['current_a'] for r in results],
                loading_percentage=[r['loading_percentage'] for r in results]
            )
        except Exception as e:
            logger.error(f"Error getting transformer data: {str(e)}")
            return None

    def get_customer_data(
            self,
            transformer_id: str,
            date: datetime,
            hour: int
        ) -> Optional[CustomerData]:
        """Get customer data for a specific transformer"""
        try:
            # Extract feeder number from transformer ID (format: S{feeder}F...)
            try:
                feeder = int(transformer_id[1])
            except (IndexError, ValueError):
                raise ValueError(f"Invalid transformer ID format: {transformer_id}")
                
            table = CUSTOMER_TABLE_TEMPLATE.format(feeder)
            query = CUSTOMER_DATA_QUERY.format(table_name=table)
            results = execute_query(
                query,
                (transformer_id, date.date(), hour)
            )
            
            if not results:
                return None
                
            return CustomerData(
                customer_ids=[r['customer_id'] for r in results],
                transformer_id=transformer_id,
                timestamp=[r['timestamp'] for r in results],
                power_kw=[r['power_kw'] for r in results],
                power_factor=[r['power_factor'] for r in results],
                voltage_v=[r['voltage_v'] for r in results],
                current_a=[r['current_a'] for r in results]
            )
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
            customer_data = self.get_customer_data(transformer_id, date, hour)
            
            if customer_data is None:
                return None
            
            return AggregatedCustomerData(
                customer_count=len(customer_data.customer_ids),
                total_power_kw=sum(customer_data.power_kw),
                avg_power_factor=sum(customer_data.power_factor) / len(customer_data.power_factor),
                total_current_a=sum(customer_data.current_a)
            )
        except Exception as e:
            logger.error(f"Error getting customer aggregation: {str(e)}")
            return None

# Initialize the service as a singleton
logger.info("Initializing CloudDataService singleton")
data_service = CloudDataService()
logger.info("CloudDataService initialization complete")
