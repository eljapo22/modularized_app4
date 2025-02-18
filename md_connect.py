import duckdb
import os
from dotenv import load_dotenv

def connect_to_motherduck():
    """Connect to MotherDuck and show available databases"""
    try:
        # Get token from environment variable
        token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            print("Please set your MOTHERDUCK_TOKEN environment variable")
            return
        
        print("Connecting to MotherDuck root...")
        # First connect to root to list databases
        root_conn = duckdb.connect(f'md:?motherduck_token={token}')
        
        # List existing databases
        print("\nExisting databases:")
        databases = root_conn.execute("SHOW DATABASES").fetchdf()
        print(databases if not databases.empty else "No databases found")
        
        # Ask for confirmation
        db_name = "ModApp4DB"
        proceed = input(f"\nDo you want to connect to/create database '{db_name}'? (y/n): ")
        
        if proceed.lower() != 'y':
            print("Operation cancelled")
            return None
            
        print(f"\nAttempting to connect to database: {db_name}")
        conn = duckdb.connect(f'md:{db_name}?motherduck_token={token}')
        
        # Show tables in the database
        print(f"\nTables in {db_name}:")
        tables = conn.execute("SHOW TABLES").fetchdf()
        print(tables if not tables.empty else "No tables found")
        
        return conn
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    load_dotenv()  # Load environment variables
    conn = connect_to_motherduck()
