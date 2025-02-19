"""
Data retrieval and processing services for the Transformer Loading Analysis Application
"""

import warnings
import os
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import logging
from typing import List, Tuple, Union
from app.core.database import SuppressOutput
from app.utils.logging_utils import log_performance, Timer, logger
from pathlib import Path
import streamlit as st

def get_data_path() -> Path:
    """Get the base path for data files, works both locally and in cloud"""
    if os.getenv('STREAMLIT_SHARING') or os.getenv('STREAMLIT_CLOUD'):
        # In cloud, use relative path from app directory
        return Path(__file__).parent.parent.parent / "processed_data" / "transformer_analysis" / "hourly"
    else:
        # Locally, use path relative to repository root
        return Path(__file__).parent.parent.parent / "processed_data" / "transformer_analysis" / "hourly"

def get_customer_data_path() -> Path:
    """Get the base path for customer data files, works both locally and in cloud"""
    if os.getenv("STREAMLIT_CLOUD"):
        # In cloud, use relative path from app directory
        return Path(__file__).parent.parent.parent / "processed_data" / "customer_analysis" / "hourly"
    else:
        # Locally, use path relative to repository root
        return Path(__file__).parent.parent.parent / "processed_data" / "customer_analysis" / "hourly"

@st.cache_data
def get_available_dates() -> Tuple[date, date]:
    """Get available date range from the data"""
    try:
        base_path = get_data_path() / "feeder1"
        
        if not base_path.exists():
            logger.error(f"Data directory not found: {base_path}")
            return date.today(), date.today()
            
        # Get all parquet files
        parquet_files = [f for f in os.listdir(base_path) if f.endswith('.parquet')]
        
        # Extract dates from filenames (excluding monthly summaries)
        dates = []
        for file in parquet_files:
            try:
                # Skip monthly summary files
                if file.count('-') != 2:
                    continue
                    
                # Parse date from filename (format: YYYY-MM-DD.parquet)
                date_str = file.replace('.parquet', '')
                dates.append(datetime.strptime(date_str, '%Y-%m-%d').date())
            except ValueError:
                continue
                
        if not dates:
            logger.error("No valid date files found")
            return date.today(), date.today()
            
        dates.sort()  # Sort dates chronologically
        return dates[0], dates[-1]
    except Exception as e:
        logger.error(f"Error getting available dates: {str(e)}")
        return date.today(), date.today()

@st.cache_data
@log_performance
def get_transformer_options(feeder: str = None) -> List[str]:
    """
    Get list of transformers for all feeders or a specific feeder
    
    Args:
        feeder: Optional feeder name to filter transformers. If None, returns all transformers.
    """
    try:
        base_path = get_data_path()
                               
        if not base_path.exists():
            st.warning(f"Data directory not found: {base_path}")
            return []
            
        # Find all feeder directories
        if feeder:
            feeder_dirs = [feeder] if os.path.exists(base_path / feeder) else []
        else:
            feeder_dirs = [d for d in os.listdir(base_path) if d.startswith('feeder')]
        
        if not feeder_dirs:
            st.warning(f"No feeder directories found in {base_path}")
            return []
            
        # Get transformer IDs from first file in each feeder
        transformer_ids = set()
        for feeder_dir in feeder_dirs:
            feeder_path = base_path / feeder_dir
            parquet_files = [f for f in os.listdir(feeder_path) if f.endswith('.parquet')]
            
            if not parquet_files:
                continue
                
            # Get transformer IDs from first file
            first_file = str(feeder_path / parquet_files[0])  # Convert to string
            try:
                df = pd.read_parquet(first_file)
                transformer_ids.update(df['transformer_id'].unique())
            except Exception as e:
                logger.error(f"Error reading transformer IDs from {first_file}: {str(e)}")
                continue
                
        # Convert to sorted list
        return sorted(list(transformer_ids))
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
        feeder_dir = feeder.lower().replace(' ', '')
        base_path = get_data_path() / feeder_dir
        
        if not base_path.exists():
            st.warning(f"Feeder directory not found: {base_path}")
            return []
            
        with Timer("Finding Monthly Files"):
            monthly_files = [f for f in os.listdir(base_path) 
                           if f.endswith('.parquet') 
                           and len(f.split('-')) == 2]
            
            if not monthly_files:
                st.warning(f"No monthly summary files found in {base_path}")
                return []
                
            latest_monthly = sorted(monthly_files)[-1]
            monthly_path = base_path / latest_monthly
            st.info(f"Using monthly summary file: {latest_monthly}")
        
        with Timer("Querying Transformer IDs"):
            with SuppressOutput():
                query = f"""
                SELECT DISTINCT transformer_id 
                FROM read_parquet('{str(monthly_path)}')
                ORDER BY transformer_id
                """
                transformer_ids = st.session_state.db_con.execute(query).df()
                
            return transformer_ids['transformer_id'].tolist()
        
    except Exception as e:
        st.error(f"Error getting transformer IDs: {str(e)}")
        logger.error(f"Error in get_transformer_ids_for_feeder: {str(e)}", exc_info=True)
        return []

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
def get_analysis_results(transformer_id: str, selected_date: Union[date, datetime, str], time_range: tuple = (0, 24), loading_range: tuple = (0, 200)) -> pd.DataFrame:
    """
    Get analysis results for the selected transformer and date
    
    Args:
        transformer_id: ID of the transformer
        selected_date: Date to analyze (can be date object, datetime object, or string in YYYY-MM-DD format)
        time_range: Tuple of (start_hour, end_hour) to filter
        loading_range: Tuple of (min_loading, max_loading) percentage to filter
    """
    try:
        logger.info(f"Getting analysis results for transformer {transformer_id} on {selected_date}")
        
        # Convert selected_date to date object if it's not already
        if isinstance(selected_date, str):
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        elif isinstance(selected_date, datetime):
            selected_date = selected_date.date()
        elif isinstance(selected_date, int):
            # Handle Unix timestamp if that's what we're getting
            selected_date = datetime.fromtimestamp(selected_date).date()
        elif not isinstance(selected_date, date):
            raise ValueError(f"Invalid date type: {type(selected_date)}")
        
        # Find the parquet file for the selected date
        base_path = get_data_path()
                               
        # Find which feeder contains this transformer
        feeder_found = None
        transformer_file = None
        
        for feeder in os.listdir(base_path):
            if not feeder.startswith('feeder'):
                continue
                
            feeder_path = base_path / feeder
            date_file = feeder_path / f"{selected_date.strftime('%Y-%m-%d')}.parquet"
            
            if not date_file.exists():
                continue
                
            # Check if transformer exists in this file
            try:
                df = pd.read_parquet(date_file)
                if transformer_id in df['transformer_id'].unique():
                    feeder_found = feeder
                    transformer_file = date_file
                    logger.info(f"Found transformer in {feeder}")
                    break
            except Exception as e:
                logger.error(f"Error reading {date_file}: {str(e)}")
                continue
                    
        if transformer_file is None:
            logger.error(f"No data found for transformer {transformer_id} on {selected_date}")
            return pd.DataFrame()
            
        # Read and process the data
        try:
            df = pd.read_parquet(transformer_file)
            
            # Filter for the specific transformer
            df = df[df['transformer_id'] == transformer_id]
            
            # Apply time range filter
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df = df[(df['hour'] >= time_range[0]) & (df['hour'] <= time_range[1])]
            
            # Apply loading range filter
            df = df[(df['loading_percentage'] >= loading_range[0]) & 
                   (df['loading_percentage'] <= loading_range[1])]
            
            # Add loading status
            df['load_range'] = df['loading_percentage'].apply(get_loading_status)
            
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error in get_analysis_results: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_customer_data(transformer_id: str, selected_date: date) -> pd.DataFrame:
    """Get customer data for a specific transformer and date"""
    try:
        logger.info(f"Retrieving customer data for transformer {transformer_id} on {selected_date}")
        
        # Extract feeder number from transformer ID (e.g., S1F1ATF001 -> 1)
        try:
            feeder_match = transformer_id.split('F')[1][0]  # Get the first character after 'F'
            feeder_dir = f"feeder{feeder_match}"
            logger.info(f"Identified feeder directory: {feeder_dir}")
        except (IndexError, AttributeError) as e:
            logger.error(f"Failed to extract feeder number from transformer ID {transformer_id}: {str(e)}")
            return pd.DataFrame()
        
        # Construct base path
        base_path = get_customer_data_path() / feeder_dir
        
        if not base_path.exists():
            logger.error(f"Customer data directory not found: {base_path}")
            return pd.DataFrame()
            
        # Get the monthly file for the selected date
        month_file = f"{transformer_id}_{selected_date.strftime('%Y-%m')}.parquet"
        file_path = base_path / month_file
        logger.info(f"Reading file: {month_file}")
        
        if not file_path.exists():
            logger.error(f"Customer data file not found: {file_path}")
            return pd.DataFrame()
            
        # Query the parquet file for the specific date using DuckDB's date_trunc
        with Timer("Customer Data Query"):
            with SuppressOutput():
                query = f"""
                SELECT 
                    timestamp,
                    customer_id,
                    power_kw,
                    current_a,
                    voltage_v,  -- Make sure we're selecting voltage
                    power_factor
                FROM read_parquet('{str(file_path)}')
                WHERE date_trunc('day', timestamp) = date_trunc('day', '{selected_date.strftime('%Y-%m-%d')}'::DATE)
                ORDER BY timestamp, customer_id
                """
                df = st.session_state.db_con.execute(query).df()
                
                # Debug log the columns
                logger.info(f"Retrieved columns: {df.columns.tolist()}")
                
        if df.empty:
            logger.warning(f"No customer data found for date {selected_date}")
        else:
            logger.info(f"Successfully retrieved {len(df)} records for {len(df['customer_id'].unique())} customers")
            
        return df
        
    except Exception as e:
        logger.error(f"Error getting customer data: {str(e)}", exc_info=True)
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
        # Get customer data to count customers
        customer_data = get_customer_data(transformer_id, date.today())
        if customer_data is None or customer_data.empty:
            return pd.DataFrame()
            
        # Count unique customers per transformer
        attributes = pd.DataFrame({
            'transformer_id': [transformer_id],
            'number_of_customers': [customer_data['customer_id'].nunique()],
            'x_coordinate': [None],  # Placeholder for now
            'y_coordinate': [None]   # Placeholder for now
        })
        
        return attributes
        
    except Exception as e:
        logger.error(f"Error getting transformer attributes: {str(e)}")
        return pd.DataFrame()
