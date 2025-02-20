import duckdb

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("\nUsing ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # List all tables
        tables = conn.execute("SHOW TABLES").fetchdf()
        print("\nAvailable tables:")
        for _, row in tables.iterrows():
            table_name = row['name']
            print(f"\n=== {table_name} ===")
            
            # Get schema
            schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
            print("\nColumns:")
            for _, col in schema.iterrows():
                print(f"- {col['column_name']}: {col['column_type']}")
            
            # Get row count
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"\nRow count: {count:,}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
