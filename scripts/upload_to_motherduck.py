import os
import glob
import duckdb

# Define the directories and cloud paths
local_paths = {
    "transformer": {
        "feeder1": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\transformer_analysis\\hourly\\feeder1",
        "feeder2": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\transformer_analysis\\hourly\\feeder2",
        "feeder3": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\transformer_analysis\\hourly\\feeder3",
        "feeder4": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\transformer_analysis\\hourly\\feeder4"
    },
    "customer": {
        "feeder1": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\customer_analysis\\hourly\\feeder1",
        "feeder2": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\customer_analysis\\hourly\\feeder2",
        "feeder3": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\customer_analysis\\hourly\\feeder3",
        "feeder4": r"C:\\Users\\JohnApostolo\\CascadeProjects\\processed_data\\customer_analysis\\hourly\\feeder4"
    }
}

# Connect to MotherDuck
print("Connecting to MotherDuck...")
con = duckdb.connect('md:')  # Connect to default database first

# Create our database
print("Creating database...")
con.execute("CREATE DATABASE IF NOT EXISTS motherduck_db")
con.close()

# Connect to our specific database
con = duckdb.connect('md:motherduck_db')

# Create tables and upload data
for data_type, feeders in local_paths.items():
    for feeder, path in feeders.items():
        print(f"\nProcessing {data_type} data for {feeder}...")
        
        # Get all parquet files in the directory
        parquet_files = glob.glob(os.path.join(path, "*.parquet"))
        if not parquet_files:
            print(f"No parquet files found in {path}")
            continue
            
        # Create table name
        table_name = f"processed_data.{data_type}_analysis_hourly_{feeder}"
        
        try:
            # Create schema if it doesn't exist
            con.execute("CREATE SCHEMA IF NOT EXISTS processed_data")
            
            # Read and upload parquet files
            for parquet_file in parquet_files:
                print(f"Uploading {os.path.basename(parquet_file)}...")
                
                # Read parquet file into temporary table
                con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{parquet_file}')")
                
                print(f"Successfully uploaded {os.path.basename(parquet_file)}")
                
        except Exception as e:
            print(f"Error processing {parquet_file}: {str(e)}")
            continue

print("\nAll files processed!")
