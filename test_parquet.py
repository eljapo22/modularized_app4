import duckdb
import os
import pandas as pd

def test_single_parquet():
    try:
        # Connect to in-memory DuckDB
        conn = duckdb.connect(':memory:')
        
        # Test file path
        file_path = os.path.normpath(r"C:\Users\JohnApostolo\CascadeProjects\processed_data\transformer_analysis\hourly\feeder1\2024-01-01.parquet").replace('\\', '/')
        
        print(f"Testing file: {file_path}")
        
        # Try pandas first
        print("\nReading with pandas:")
        df = pd.read_parquet(file_path)
        print("\nDataFrame Info:")
        print(df.info())
        print("\nFirst few rows:")
        print(df.head(2))
        
        # Now try DuckDB
        print("\nReading with DuckDB:")
        
        # Get schema
        print("\nSchema:")
        schema = conn.execute(f"SELECT * FROM parquet_schema('{file_path}')").fetchall()
        for col in schema:
            print(f"  {col}")
        
        # Create view and get sample data
        conn.execute(f"CREATE VIEW test_view AS SELECT * FROM read_parquet('{file_path}')")
        
        # Get column names and types
        print("\nColumns:")
        columns = conn.execute("DESCRIBE test_view").fetchall()
        for col in columns:
            print(f"  {col}")
        
        # Get row count
        row_count = conn.execute("SELECT COUNT(*) FROM test_view").fetchone()[0]
        print(f"\nRow count: {row_count}")
        
        # Get sample data
        print("\nSample data:")
        sample = conn.execute("SELECT * FROM test_view LIMIT 2").fetchall()
        for row in sample:
            print(f"  {row}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_single_parquet()
