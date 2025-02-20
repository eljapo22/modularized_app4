import duckdb

def print_table_info(conn, table_name):
    print(f"\n=== Table: {table_name} ===")
    
    # Get schema
    print("\nSchema:")
    schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
    print(schema.to_string())
    
    # Get row count
    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"\nRow count: {count:,}")
    
    # Get sample data
    print("\nSample data:")
    sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchdf()
    print(sample.to_string())
    
    # Get min/max timestamps if they exist
    try:
        time_range = conn.execute(f"""
            SELECT 
                MIN(timestamp) as min_time,
                MAX(timestamp) as max_time
            FROM {table_name}
            WHERE timestamp IS NOT NULL
        """).fetchdf()
        print("\nTime range:")
        print(time_range.to_string())
    except:
        pass

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("Using ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # Get list of tables
        tables = conn.execute("SHOW TABLES").fetchdf()
        print("\nAvailable tables:")
        print(tables.to_string())
        
        # Inspect each table
        for table_name in tables['name']:
            print_table_info(conn, table_name)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
