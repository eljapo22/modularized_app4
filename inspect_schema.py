import duckdb

def inspect_table(conn, table_name):
    print(f"\nSchema for {table_name}:")
    try:
        # Get table schema
        schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
        print(schema)
        
        # Get sample data
        print(f"\nSample data from {table_name}:")
        sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchdf()
        print(sample)
    except Exception as e:
        print(f"Error inspecting {table_name}: {str(e)}")

try:
    print("Connecting to MotherDuck...")
    conn = duckdb.connect('motherduck:')
    conn.execute('USE ModApp4DB')
    
    # List of tables to inspect
    tables = [
        'transformer_reading',
        'customer_reading',
        'transformer',
        'customer',
        'feeder',
        'transformer_alerts',
        'transformer_customer_stats',
        'transformer_loading'
    ]
    
    # Inspect each table
    for table in tables:
        inspect_table(conn, table)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close()
