import duckdb
import os
from pathlib import Path
import pandas as pd

def get_sample_transformer_data():
    """Get sample transformer data to infer schema"""
    data_path = Path(__file__).parent.parent / "processed_data" / "transformer_analysis" / "hourly"
    
    # Find first parquet file
    for feeder_dir in data_path.glob("feeder*"):
        for file in feeder_dir.glob("*.parquet"):
            print(f"Reading schema from {file}")
            return pd.read_parquet(file)
    return None

def get_sample_customer_data():
    """Get sample customer data to infer schema"""
    data_path = Path(__file__).parent.parent / "processed_data" / "customer_analysis" / "hourly"
    
    # Find first parquet file
    for feeder_dir in data_path.glob("feeder*"):
        for file in feeder_dir.glob("*.parquet"):
            print(f"Reading schema from {file}")
            return pd.read_parquet(file)
    return None

def main():
    # Get sample data
    transformer_df = get_sample_transformer_data()
    customer_df = get_sample_customer_data()
    
    if transformer_df is not None:
        print("\nTransformer data schema:")
        print(transformer_df.dtypes)
        
    if customer_df is not None:
        print("\nCustomer data schema:")
        print(customer_df.dtypes)
        
    # Create SQL schema
    print("\nSQL schema for transformer data:")
    transformer_schema = []
    if transformer_df is not None:
        for col, dtype in transformer_df.dtypes.items():
            sql_type = "DOUBLE" if "float" in str(dtype) else \
                      "TIMESTAMP" if "datetime" in str(dtype) else \
                      "VARCHAR" if "object" in str(dtype) else \
                      "BIGINT" if "int" in str(dtype) else \
                      "VARCHAR"
            transformer_schema.append(f"{col} {sql_type}")
        print("CREATE TABLE transformer_readings (")
        print("    " + ",\n    ".join(transformer_schema))
        print(");")
        
    print("\nSQL schema for customer data:")
    customer_schema = []
    if customer_df is not None:
        for col, dtype in customer_df.dtypes.items():
            sql_type = "DOUBLE" if "float" in str(dtype) else \
                      "TIMESTAMP" if "datetime" in str(dtype) else \
                      "VARCHAR" if "object" in str(dtype) else \
                      "BIGINT" if "int" in str(dtype) else \
                      "VARCHAR"
            customer_schema.append(f"{col} {sql_type}")
        print("CREATE TABLE customer_readings (")
        print("    " + ",\n    ".join(customer_schema))
        print(");")

if __name__ == "__main__":
    main()
