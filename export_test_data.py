import duckdb
import pandas as pd
import os
from datetime import datetime, date
from dotenv import load_dotenv

def export_test_data():
    """Export a sample of data from one feeder for testing"""
    try:
        print("Starting test data export...")
        
        # Base path for data
        base_path = os.path.join("C:", "Users", "JohnApostolo", "CascadeProjects", 
                                "processed_data", "transformer_analysis", "hourly")
                                
        # Select a test feeder (Feeder1)
        feeder_path = os.path.join(base_path, "feeder1")
        
        if not os.path.exists(feeder_path):
            print(f"Error: Feeder path not found: {feeder_path}")
            return False
            
        # Get first available date's data
        parquet_files = [f for f in os.listdir(feeder_path) if f.endswith('.parquet')]
        if not parquet_files:
            print("No parquet files found")
            return False
            
        test_file = os.path.join(feeder_path, parquet_files[0])
        print(f"\nExporting data from: {test_file}")
        
        # Create local DuckDB connection for data export
        local_conn = duckdb.connect(database=':memory:', read_only=False)
        
        # Export transformer data
        print("\nExporting transformer data...")
        transformer_data = local_conn.execute("""
            SELECT DISTINCT
                transformer_id,
                'Feeder1' as feeder_id,
                size_kva,
                nominal_voltage,
                rated_current,
                CURRENT_TIMESTAMP as created_at,
                CURRENT_TIMESTAMP as updated_at
            FROM read_parquet(?)
        """, [test_file]).fetchdf()
        
        print(f"Found {len(transformer_data)} transformers")
        print("\nSample transformer data:")
        print(transformer_data.head())
        
        # Export transformer readings
        print("\nExporting transformer readings...")
        readings_data = local_conn.execute("""
            SELECT 
                transformer_id,
                timestamp,
                power_kw,
                current_a,
                voltage_v,
                power_factor,
                power_kw / NULLIF(size_kva * power_factor, 0) * 100 as loading_percentage,
                CASE
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 120 THEN 'Critical'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 100 THEN 'Overloaded'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 80 THEN 'Warning'
                    WHEN power_kw / NULLIF(size_kva * power_factor, 0) * 100 >= 50 THEN 'Pre-Warning'
                    ELSE 'Normal'
                END as load_range
            FROM read_parquet(?)
            LIMIT 10
        """, [test_file]).fetchdf()
        
        print(f"Sample size: {len(readings_data)} readings")
        print("\nSample readings data:")
        print(readings_data.head())
        
        # Save exported data to CSV for verification
        export_path = os.path.join("C:", "Users", "JohnApostolo", "CascadeProjects", 
                                  "modularized_app4", "data_export")
        os.makedirs(export_path, exist_ok=True)
        
        transformer_file = os.path.join(export_path, "test_transformers.csv")
        readings_file = os.path.join(export_path, "test_readings.csv")
        
        transformer_data.to_csv(transformer_file, index=False)
        readings_data.to_csv(readings_file, index=False)
        
        print(f"\nExported data saved to:")
        print(f"Transformers: {transformer_file}")
        print(f"Readings: {readings_file}")
        
        return True
        
    except Exception as e:
        print(f"Error during export: {str(e)}")
        return False

if __name__ == "__main__":
    success = export_test_data()
    if success:
        print("\nTest data export completed successfully!")
    else:
        print("\nFailed to export test data.")
