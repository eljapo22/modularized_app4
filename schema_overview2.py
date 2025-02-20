import duckdb

def main():
    try:
        print("Connecting to MotherDuck...")
        conn = duckdb.connect('motherduck:')
        
        print("\nUsing ModApp4DB...")
        conn.execute('USE ModApp4DB;')
        
        # Get all tables
        tables = conn.execute("SHOW TABLES").fetchdf()
        
        # For each table, describe its structure
        for _, row in tables.iterrows():
            table_name = row['name']
            print(f"\n=== {table_name} ===")
            schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
            print(schema.to_string())
            
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
