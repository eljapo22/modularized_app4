"""
Data retrieval and processing services for the Transformer Loading Analysis Application
"""

import warnings
import os
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import logging
import re
from typing import List, Tuple, Union, Optional
from app.core.database import SuppressOutput
from app.utils.logging_utils import log_performance, Timer, logger
from pathlib import Path
import streamlit as st
from app.config.cloud_config import use_motherduck

def get_project_root() -> Path:
    """Get the root directory of the project"""
    root = Path(__file__).parent.parent.parent
    logger.info(f"Project root: {root}")
    if not root.exists():
        logger.error(f"Project root does not exist: {root}")
    return root

def get_data_path() -> Path:
    """Get the base path for data files"""
    # Always use repository structure since data is in Git
    path = get_project_root() / "processed_data" / "transformer_analysis" / "hourly"
    logger.info(f"Data path: {path}")
    if not path.exists():
        logger.error(f"Data path does not exist: {path}")
    return path

def get_customer_data_path() -> Path:
    """Get the base path for customer data files"""
    # Always use repository structure since data is in Git
    path = get_project_root() / "processed_data" / "customer_analysis" / "hourly"
    logger.info(f"Customer data path: {path}")
    if not path.exists():
        logger.error(f"Customer data path does not exist: {path}")
    return path

@st.cache_data
def get_available_dates() -> Tuple[date, date]:
    """Get available date range from the data"""
    try:
        if use_motherduck():
            # Use MotherDuck database
            logger.info("Using MotherDuck database")
            con = get_database_connection()
            if not con:
                logger.error("Failed to get database connection")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
            
            # Query date range from MotherDuck
            query = """
            SELECT 
                MIN(DATE(timestamp)) as min_date,
                MAX(DATE(timestamp)) as max_date
            FROM transformer_data
            """
            result = con.execute(query).fetchone()
            if not result or not result[0] or not result[1]:
                logger.error("No dates found in MotherDuck")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            min_date = result[0].date()
            max_date = result[1].date()
            logger.info(f"Date range from MotherDuck: {min_date} to {max_date}")
            return min_date, max_date
        else:
            # Use local files
            base_path = get_data_path() / "feeder1"
            
            if not base_path.exists():
                logger.error(f"Data directory not found: {base_path}")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            # List all parquet files
            files = list(base_path.glob("*.parquet"))
            if not files:
                logger.error("No parquet files found")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            # Extract dates from filenames
            dates = []
            for file in files:
                try:
                    # Only accept daily file format (YYYY-MM-DD.parquet)
                    date_str = file.stem
                    if len(date_str) == 10:  # YYYY-MM-DD format
                        dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
                except ValueError:
                    continue
                    
            if not dates:
                logger.error("No valid dates found in filenames")
                default_date = datetime(2024, 2, 14).date()
                return default_date, default_date
                
            min_date = min(dates)
            max_date = max(dates)
            
            logger.info(f"Date range from files: {min_date} to {max_date}")
            return min_date, max_date
            
    except Exception as e:
        logger.error(f"Error getting available dates: {str(e)}")
        default_date = datetime(2024, 2, 14).date()
        return default_date, default_date

@st.cache_data
@log_performance
def get_transformer_options(feeder: str = None) -> List[str]:
    """Get list of available transformers"""
    try:
        base_path = get_data_path()
        logger.info(f"Looking for transformers in {base_path}")
        
        # If feeder is specified, only look in that feeder's directory
        if feeder:
            feeder_dirs = [feeder]
        else:
            # Otherwise, look in all feeder directories
            feeder_dirs = [d.name for d in base_path.iterdir() if d.is_dir() and d.name.startswith('feeder')]
            logger.info(f"Found feeder directories: {feeder_dirs}")

        transformers = []
        for feeder_dir in feeder_dirs:
            # Get monthly summary file for current month
            feeder_path = base_path / feeder_dir
            if not feeder_path.exists():
                logger.warning(f"Feeder directory not found: {feeder_path}")
                continue
                
            # Get all daily files for the current month
            current_month = datetime.now().strftime('%Y-%m')
            daily_files = list(feeder_path.glob(f"{current_month}-*.parquet"))
            
            if not daily_files:
                logger.warning(f"No daily files found for {current_month} in {feeder_path}")
                continue
            
            # Read each file and collect transformer IDs
            for file in daily_files:
                logger.info(f"Reading transformers from {file}")
                try:
                    df = pd.read_parquet(file)
                    transformers.extend(df['transformer_id'].unique().tolist())
                except Exception as e:
                    logger.error(f"Error reading {file}: {str(e)}")
                    continue
            
        # Remove duplicates and sort
        transformers = sorted(list(set(transformers)))
        logger.info(f"Found {len(transformers)} transformers")
        return transformers
        
    except Exception as e:
        logger.error(f"Error getting transformer options: {str(e)}")
        return []

@log_performance
def get_relevant_files_query(base_path, feeder, start_date, end_date):
    """Get the query string for relevant parquet files based on date range"""
    try:
        feeder_path = base_path / f'feeder{feeder}'
        
        if not feeder_path.exists():
            st.error(f"Feeder directory not found: {feeder_path}")
            return None
            
        parquet_files = [f for f in os.listdir(feeder_path) if f.endswith('.parquet')]
        if not parquet_files:
            st.error(f"No parquet files found in {feeder_path}")
            return None
            
        st.info(f"Found {len(parquet_files)} parquet files to analyze")
        return f"read_parquet('{str(feeder_path)}/*.parquet', union_by_name=True)"  # Convert to string
        
    except Exception as e:
        st.error(f"Error constructing file query: {str(e)}")
        logger.error(f"Error in get_relevant_files_query: {str(e)}", exc_info=True)
        return None

@log_performance
def get_transformer_ids_for_feeder(feeder: str) -> List[str]:
    """Get list of transformer IDs for a feeder using the latest monthly summary file"""
    try:
        # Get base path for data
        base_path = get_data_path() / feeder  # get_data_path() already includes 'hourly'
        logger.info(f"Looking for transformers in {base_path}")
        
        if not base_path.exists():
            logger.error(f"Feeder directory not found: {base_path}")
            return ['no_transformers_found']
            
        # Get all parquet files
        try:
            parquet_files = [f for f in os.listdir(base_path) if f.endswith('.parquet')]
            logger.info(f"Found {len(parquet_files)} parquet files: {parquet_files[:5]}")
        except Exception as e:
            logger.error(f"Error listing directory {base_path}: {str(e)}")
            return ['no_transformers_found']
        
        if not parquet_files:
            logger.error(f"No parquet files found in {base_path}")
            return ['no_transformers_found']
            
        # Get latest file
        latest_file = sorted(parquet_files)[-1]
        file_path = base_path / latest_file
        logger.info(f"Using file: {file_path}")
        
        # Read parquet file
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"Read parquet file with columns: {df.columns.tolist()}")
            logger.info(f"Sample data:\n{df.head()}")
        except Exception as e:
            logger.error(f"Error reading parquet file {file_path}: {str(e)}")
            return ['no_transformers_found']
        
        # Get unique transformer IDs
        transformer_ids = sorted(df['transformer_id'].unique().tolist())
        logger.info(f"Found {len(transformer_ids)} transformers: {transformer_ids[:5]}")
        
        if not transformer_ids:
            logger.warning(f"No transformer IDs found in {file_path}")
            return ['no_transformers_found']
            
        return transformer_ids
        
    except Exception as e:
        logger.error(f"Error in get_transformer_ids_for_feeder: {str(e)}")
        return ['no_transformers_found']

def get_loading_status(loading_percentage: float) -> str:
    """Get the loading status based on percentage."""
    if loading_percentage >= 120:
        return 'Critical'
    elif loading_percentage >= 100:
        return 'Overloaded'
    elif loading_percentage >= 80:
        return 'Warning'
    elif loading_percentage >= 50:
        return 'Pre-Warning'
    else:
        return 'Normal'

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_analysis_results(transformer_id: str, selected_date: Union[date, datetime, str, int, np.integer], time_range: tuple = (0, 24), loading_range: tuple = (0, 200)) -> pd.DataFrame:
    """Get analysis results for a transformer and date"""
    try:
        logger.debug(f"Starting get_analysis_results for transformer {transformer_id} on date {selected_date}")
        
        # Extract feeder from transformer ID
        feeder = extract_feeder(transformer_id)
        if not feeder:
            logger.error(f"Could not extract feeder from transformer ID: {transformer_id}")
            return pd.DataFrame()
            
        logger.info(f"Getting data for transformer {transformer_id} in {feeder}")
        
        # Convert date to string format
        try:
            if isinstance(selected_date, (datetime, date)):
                date_str = selected_date.strftime('%Y-%m-%d')
            elif isinstance(selected_date, str):
                # Validate the date string format
                datetime.strptime(selected_date, '%Y-%m-%d')
                date_str = selected_date
            else:
                # For other types (int, np.integer), convert through Timestamp
                date_str = pd.Timestamp(selected_date).strftime('%Y-%m-%d')
                
            logger.debug(f"Converted date {selected_date} to format: {date_str}")
            
        except Exception as e:
            logger.error(f"Invalid date format: {selected_date} - {str(e)}")
            return pd.DataFrame()
            
        try:
            if use_motherduck():
                # Use MotherDuck database
                logger.info("Using MotherDuck database")
                con = get_database_connection()
                if not con:
                    logger.error("Failed to get database connection")
                    return pd.DataFrame()
                
                # Query data from MotherDuck
                query = f"""
                SELECT *
                FROM transformer_data
                WHERE transformer_id = '{transformer_id}'
                AND DATE(timestamp) = '{date_str}'
                """
                df = pd.DataFrame(con.execute(query).fetchdf())
                logger.info(f"Retrieved {len(df)} rows from MotherDuck")
            else:
                # Use local parquet files
                base_path = get_data_path() / feeder
                logger.debug(f"Looking for data in: {base_path}")
                
                if not base_path.exists():
                    logger.error(f"Feeder directory not found: {base_path}")
                    return pd.DataFrame()
                
                # Try daily file only
                daily_file = base_path / f"{date_str}.parquet"
                logger.debug(f"Checking daily file: {daily_file}")
                
                if daily_file.exists():
                    file_path = daily_file
                    logger.info(f"Found and using daily file: {file_path}")
                else:
                    logger.error(f"No daily data file found for {date_str} at {daily_file}")
                    st.error(f"No data file found for date: {date_str}")
                    return pd.DataFrame()
                
                # Read parquet file
                logger.info(f"Reading file: {file_path}")
                df = pd.read_parquet(file_path)
                logger.info(f"Read {len(df)} rows with columns: {df.columns.tolist()}")
            
            # Filter for transformer
            df = df[df['transformer_id'] == transformer_id].copy()
            logger.info(f"Found {len(df)} rows for transformer {transformer_id}")
            
            if df.empty:
                logger.warning(f"No data found for transformer {transformer_id} on {date_str}")
                st.error("""No data found for this transformer. Please check:
                1. The selected date is within the available range
                2. The transformer has data for this date
                3. The data files are properly formatted""")
                return pd.DataFrame()
            
            # Log transformer capacity
            if 'size_kva' in df.columns:
                size_kva = df['size_kva'].iloc[0]
                logger.info(f"Transformer capacity (size_kva): {size_kva} kVA")
            else:
                logger.warning("size_kva column not found in data")
            
            # Log power values before processing
            if 'power_kw' in df.columns:
                logger.info(f"Power values: min={df['power_kw'].min()}, max={df['power_kw'].max()}")
                
                # Calculate loading percentage using power and size_kva
                if 'size_kva' in df.columns and 'power_factor' in df.columns:
                    size_kva = df['size_kva'].iloc[0]
                    power_factor = df['power_factor'].fillna(0.95)  # Use 0.95 as default power factor if missing
                    df['loading_percentage'] = (df['power_kw'] / (size_kva * power_factor)) * 100
                    logger.info(f"Calculated loading percentage using size_kva={size_kva}, power_factor={power_factor.iloc[0]}")
                elif 'size_kva' in df.columns:
                    size_kva = df['size_kva'].iloc[0]
                    df['loading_percentage'] = (df['power_kw'] / size_kva) * 100  # Assume unity power factor
                    logger.warning("Power factor not found, assuming unity power factor for loading calculation")
                else:
                    logger.error("Cannot calculate loading percentage - missing size_kva")
            
            # Filter by time range
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df = df[(df['hour'] >= time_range[0]) & (df['hour'] <= time_range[1])]
            logger.info(f"Found {len(df)} rows in time range {time_range}")
            
            # Filter by loading range
            df = df[(df['loading_percentage'] >= loading_range[0]) & 
                   (df['loading_percentage'] <= loading_range[1])]
            logger.info(f"Found {len(df)} rows in loading range {loading_range}")
            
            if df.empty:
                logger.warning("No data found after applying time and loading range filters")
                st.warning("No data found within the selected time and loading ranges")
                return pd.DataFrame()
                
            # Add load range based on loading percentage
            df['load_range'] = df['loading_percentage'].apply(get_loading_status)
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            logger.info(f"Returning {len(df)} rows of data")
            return df
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            st.error(f"Error processing data: {str(e)}")
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_customer_data(transformer_id: str, selected_date: Union[date, datetime, str]) -> pd.DataFrame:
    """Get customer data for a transformer and date"""
    try:
        logger.debug(f"Starting get_customer_data for transformer {transformer_id} on date {selected_date}")
        
        # Extract feeder from transformer ID
        feeder = extract_feeder(transformer_id)
        if not feeder:
            logger.error(f"Could not extract feeder from transformer ID: {transformer_id}")
            return pd.DataFrame()

        # Convert date to string format for month
        try:
            if isinstance(selected_date, (datetime, date)):
                date_obj = selected_date if isinstance(selected_date, date) else selected_date.date()
            elif isinstance(selected_date, str):
                # Validate the date string format
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
            else:
                logger.error(f"Invalid date type: {type(selected_date)}")
                return pd.DataFrame()
            
            # Format for monthly file
            month_str = date_obj.strftime('%Y-%m')
            target_date = date_obj.strftime('%Y-%m-%d')
            logger.debug(f"Converted date {selected_date} to month format: {month_str}")
            
        except Exception as e:
            logger.error(f"Invalid date format: {selected_date}")
            return pd.DataFrame()

        # Construct file path for monthly customer data
        file_path = get_customer_data_path() / feeder / f"{transformer_id}_{month_str}.parquet"
        logger.debug(f"Looking for customer data at: {file_path}")
        
        if not file_path.exists():
            logger.error(f"Customer data file not found: {file_path}")
            return pd.DataFrame()

        # Read parquet file
        logger.debug(f"Reading customer data file: {file_path}")
        df = pd.read_parquet(file_path)
        logger.debug(f"Read {len(df)} rows from customer data file")
        
        # Convert timestamp to date for filtering
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        df = df[df['date'] == date_obj].copy()
        logger.debug(f"Filtered to {len(df)} rows for date {target_date}")
        
        # Drop temporary date column
        df = df.drop('date', axis=1)
        
        if df.empty:
            logger.warning(f"No customer data found for date {target_date}")
            return pd.DataFrame()

        logger.info(f"Found {len(df)} customer data records for {transformer_id} on {target_date}")
        return df

    except Exception as e:
        logger.error(f"Error getting customer data: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_transformer_attributes(transformer_id: str) -> pd.DataFrame:
    """
    Get attributes for a specific transformer
    
    Args:
        transformer_id: ID of the transformer to get attributes for
        
    Returns:
        DataFrame containing transformer attributes
    """
    try:
        # Get customer data for current month
        current_date = datetime.now().date()
        month_start = current_date.replace(day=1)
        customer_data = get_customer_data(transformer_id, month_start)
        
        if customer_data.empty:
            logger.warning(f"No customer data found for transformer {transformer_id}")
            return pd.DataFrame({
                'transformer_id': [transformer_id],
                'number_of_customers': [0],
                'x_coordinate': [None],
                'y_coordinate': [None]
            })
            
        # Count unique customers per transformer
        customer_count = customer_data['customer_id'].nunique()
        logger.info(f"Found {customer_count} customers for transformer {transformer_id}")
        
        attributes = pd.DataFrame({
            'transformer_id': [transformer_id],
            'number_of_customers': [customer_count],
            'x_coordinate': [None],  # Placeholder for now
            'y_coordinate': [None]   # Placeholder for now
        })
        
        return attributes
        
    except Exception as e:
        logger.error(f"Error getting transformer attributes: {str(e)}")
        return pd.DataFrame({
            'transformer_id': [transformer_id],
            'number_of_customers': [0],
            'x_coordinate': [None],
            'y_coordinate': [None]
        })

def get_database_connection():
    # TO DO: implement logic to get a database connection
    pass

def extract_feeder(transformer_id: str) -> str:
    """
    Extract feeder ID from transformer ID.
    
    Format: S[sector]F[feeder]ATF[number]
    Example: S1F1ATF001 -> feeder1
    
    Args:
        transformer_id: ID of the transformer
        
    Returns:
        Feeder ID (e.g. 'feeder1')
    """
    try:
        # Extract feeder number using regex
        match = re.search(r'F(\d+)', transformer_id)
        if not match:
            logger.error(f"Could not extract feeder from transformer ID: {transformer_id}")
            return None
            
        feeder_num = match.group(1)
        feeder = f"feeder{feeder_num}"
        logger.info(f"Extracted feeder {feeder} from {transformer_id}")
        return feeder
        
    except Exception as e:
        logger.error(f"Error extracting feeder: {str(e)}")
        return None

@st.cache_data
@log_performance
def get_available_feeders() -> List[str]:
    """Get list of available feeders"""
    try:
        base_path = get_data_path()
        logger.info(f"Looking for feeders in {base_path}")
        
        # Get all feeder directories
        feeder_dirs = [d.name for d in base_path.iterdir() if d.is_dir() and d.name.startswith('feeder')]
        feeder_dirs = sorted(feeder_dirs)
        
        logger.info(f"Found feeders: {feeder_dirs}")
        return feeder_dirs
    except Exception as e:
        logger.error(f"Error getting available feeders: {str(e)}")
        return ['feeder1']  # Return default if error occurs
