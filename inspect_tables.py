import duckdb

def inspect_table(conn, table_name):
    print(f"\nInspecting table: {table_name}")
    try:
        print("\nSchema:")
        schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
        print(schema)
        
        print("\nSample data:")
        sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 1").fetchdf()
        print(sample)
    except Exception as e:
        print(f"Error inspecting {table_name}: {str(e)}")

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("Using ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # Get list of tables
        tables = conn.execute("SHOW TABLES").fetchdf()
        print("\nAvailable tables:")
        print(tables)
        
        # Inspect each table
        for table_name in tables['name']:
            inspect_table(conn, table_name)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
