import duckdb

def show_database_info():
    """Show all information about the MotherDuck database"""
    try:
        # Connect directly to your database
        print("\n1. Connecting to your database...")
        con = duckdb.connect('md:ModApp4DB')
        
        # List all schemas
        print("\n2. Listing all schemas:")
        schemas = con.execute("SHOW SCHEMAS").fetchdf()
        print(schemas)
        
        # List all tables in processed_data schema
        print("\n3. Listing all tables in processed_data schema:")
        tables = con.execute("""
            SELECT * FROM information_schema.tables 
            WHERE table_schema = 'processed_data'
        """).fetchdf()
        print(tables)
        
        # Show sample data from one table
        print("\n4. Sample data from transformer_analysis_hourly_feeder1:")
        sample = con.execute("""
            SELECT * FROM processed_data.transformer_analysis_hourly_feeder1 
            LIMIT 5
        """).fetchdf()
        print(sample)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    show_database_info()
