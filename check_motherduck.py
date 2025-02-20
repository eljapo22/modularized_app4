import duckdb
import os
import streamlit as st
import pandas as pd

def print_section(title):
    print(f"\n{title}")
    print("=" * len(title))

def check_table_stats(conn, table_name):
    # Basic table info
    stats_query = f"""
    SELECT 
        COUNT(*) as row_count,
        COUNT(DISTINCT transformer_id) as unique_transformers,
        MIN(timestamp) as earliest_date,
        MAX(timestamp) as latest_date,
        ROUND(AVG(loading_percentage), 2) as avg_loading,
        ROUND(AVG(power_factor), 2) as avg_power_factor,
        COUNT(CASE WHEN loading_percentage >= 120 THEN 1 END) as critical_count,
        COUNT(CASE WHEN loading_percentage >= 100 AND loading_percentage < 120 THEN 1 END) as overloaded_count,
        COUNT(CASE WHEN loading_percentage >= 80 AND loading_percentage < 100 THEN 1 END) as warning_count
    FROM "{table_name}"
    """
    
    try:
        stats = conn.execute(stats_query).df()
        print(f"\nStatistics for {table_name}:")
        print("-" * 40)
        
        # Format the stats nicely
        stats_dict = stats.iloc[0].to_dict()
        for key, value in stats_dict.items():
            print(f"{key:20}: {value}")
            
        # Check recent high loads
        high_loads_query = f"""
        SELECT 
            transformer_id,
            timestamp,
            ROUND(loading_percentage, 2) as loading_percentage,
            ROUND(power_factor, 2) as power_factor,
            voltage_v
        FROM "{table_name}"
        WHERE loading_percentage >= 80
            AND timestamp >= (SELECT MAX(timestamp) - INTERVAL '24 HOURS' FROM "{table_name}")
        ORDER BY loading_percentage DESC
        LIMIT 5
        """
        
        high_loads = conn.execute(high_loads_query).df()
        if not high_loads.empty:
            print(f"\nRecent high loads in {table_name}:")
            print(high_loads)
            
    except Exception as e:
        print(f"Error analyzing {table_name}: {str(e)}")

def check_customer_table_stats(conn, table_name):
    # Basic table info
    stats_query = f"""
    SELECT 
        COUNT(*) as row_count,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(DISTINCT transformer_id) as unique_transformers,
        MIN(timestamp) as earliest_date,
        MAX(timestamp) as latest_date,
        ROUND(AVG(power_kw), 2) as avg_power_kw,
        ROUND(AVG(power_factor), 2) as avg_power_factor
    FROM "{table_name}"
    """
    
    try:
        stats = conn.execute(stats_query).df()
        print(f"\nStatistics for {table_name}:")
        print("-" * 40)
        
        # Format the stats nicely
        stats_dict = stats.iloc[0].to_dict()
        for key, value in stats_dict.items():
            print(f"{key:20}: {value}")
            
        # Check recent high power usage
        high_power_query = f"""
        SELECT 
            customer_id,
            transformer_id,
            timestamp,
            ROUND(power_kw, 2) as power_kw,
            ROUND(power_factor, 2) as power_factor,
            voltage_v
        FROM "{table_name}"
        WHERE timestamp >= (SELECT MAX(timestamp) - INTERVAL '24 HOURS' FROM "{table_name}")
        ORDER BY power_kw DESC
        LIMIT 5
        """
        
        high_power = conn.execute(high_power_query).df()
        if not high_power.empty:
            print(f"\nRecent high power usage in {table_name}:")
            print(high_power)
            
    except Exception as e:
        print(f"Error analyzing {table_name}: {str(e)}")

def main():
    # Get token from secrets and set it
    token = st.secrets["MOTHERDUCK_TOKEN"]
    os.environ["motherduck_token"] = token

    # Connect to MotherDuck
    conn = duckdb.connect('md:ModApp4DB')
    
    print_section("MotherDuck Database Analysis")
    
    # Check transformer feeders
    for i in range(1, 5):
        check_table_stats(conn, f"Transformer Feeder {i}")
        
    # Check customer feeders
    for i in range(1, 5):
        check_customer_table_stats(conn, f"Customer Feeder {i}")

if __name__ == "__main__":
    main()
