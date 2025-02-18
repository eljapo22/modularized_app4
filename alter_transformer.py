import duckdb
import os
from dotenv import load_dotenv

def alter_transformer_table():
    """Add coordinate columns to transformer table"""
    try:
        # Get token from environment variable
        token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            print("Please set your MOTHERDUCK_TOKEN environment variable")
            return False
            
        print("Connecting to ModApp4DB...")
        conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        
        # Add x_coordinate column
        print("\nAdding x_coordinate to transformer table...")
        conn.execute("""
            ALTER TABLE transformer 
            ADD COLUMN x_coordinate DOUBLE
        """)
        
        # Add y_coordinate column
        print("Adding y_coordinate to transformer table...")
        conn.execute("""
            ALTER TABLE transformer 
            ADD COLUMN y_coordinate DOUBLE
        """)
        
        # Verify the new structure
        print("\nVerifying updated transformer table structure:")
        schema = conn.execute("DESCRIBE transformer").fetchdf()
        print(schema)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    success = alter_transformer_table()
    if success:
        print("\nTransformer table updated successfully!")
    else:
        print("\nFailed to update transformer table.")
