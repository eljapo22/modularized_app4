import duckdb
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_motherduck_connection():
    """Test connection to MotherDuck"""
    try:
        # Get token from environment variable
        token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            print("No MotherDuck token found in environment variables")
            return False
            
        # Try to connect
        print("Attempting to connect to MotherDuck...")
        con = duckdb.connect(f'md:transformer_analysis?motherduck_token={token}')
        
        # Test the connection with a simple query
        result = con.execute("SELECT 1 as test").fetchall()
        print("Successfully connected to MotherDuck!")
        
        # Get list of existing tables
        print("\nExisting tables in database:")
        tables = con.execute("SHOW TABLES").fetchdf()
        print(tables if not tables.empty else "No tables found")
        
        return True
        
    except Exception as e:
        print(f"Error connecting to MotherDuck: {str(e)}")
        return False

if __name__ == "__main__":
    test_motherduck_connection()
