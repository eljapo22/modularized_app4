import duckdb
import os

def check_duckdb_version():
    version = duckdb.__version__
    print(f"DuckDB version: {version}")
    return version

try:
    # Check DuckDB version
    version = check_duckdb_version()
    if version != "1.2.0":
        print("Warning: You're not using DuckDB 1.2.0")
    
    print("\nConnecting to MotherDuck...")
    # Connect using recommended format
    conn = duckdb.connect('motherduck:')
    
    print("\nCreating and using database...")
    conn.execute('CREATE DATABASE IF NOT EXISTS ModApp4DB')
    conn.execute('USE ModApp4DB')
    
    print("\nListing tables...")
    tables = conn.execute('SHOW TABLES').fetchdf()
    print(tables)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
