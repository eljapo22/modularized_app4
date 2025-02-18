import duckdb
import os
from dotenv import load_dotenv

def create_database_schema():
    """Create the database schema for the transformer loading analysis system"""
    try:
        # Get token from environment variable
        token = os.getenv('MOTHERDUCK_TOKEN')
        if not token:
            print("Please set your MOTHERDUCK_TOKEN environment variable")
            return
            
        # First connect to root to create database
        print("Connecting to MotherDuck root...")
        root_conn = duckdb.connect(f'md:?motherduck_token={token}')
        
        # Create database
        print("\nCreating ModApp4DB if it doesn't exist...")
        root_conn.execute("CREATE DATABASE IF NOT EXISTS ModApp4DB")
        root_conn.close()
            
        print("Connecting to ModApp4DB...")
        conn = duckdb.connect(f'md:ModApp4DB?motherduck_token={token}')
        
        # Create FEEDER table
        print("\nCreating FEEDER table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feeder (
                feeder_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                rated_capacity DOUBLE,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Create TRANSFORMER table
        print("Creating TRANSFORMER table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transformer (
                transformer_id VARCHAR PRIMARY KEY,
                feeder_id VARCHAR,
                size_kva DOUBLE,
                nominal_voltage DOUBLE,
                rated_current DOUBLE,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (feeder_id) REFERENCES feeder(feeder_id)
            )
        """)
        
        # Create TRANSFORMER_READING table
        print("Creating TRANSFORMER_READING table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transformer_reading (
                reading_id VARCHAR PRIMARY KEY,
                transformer_id VARCHAR,
                timestamp TIMESTAMP,
                power_kw DOUBLE,
                current_a DOUBLE,
                voltage_v DOUBLE,
                power_factor DOUBLE,
                loading_percentage DOUBLE,
                load_range VARCHAR,
                FOREIGN KEY (transformer_id) REFERENCES transformer(transformer_id)
            )
        """)
        
        # Create CUSTOMER table
        print("Creating CUSTOMER table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer (
                customer_id VARCHAR PRIMARY KEY,
                transformer_id VARCHAR,
                x_coordinate DOUBLE,
                y_coordinate DOUBLE,
                service_type VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (transformer_id) REFERENCES transformer(transformer_id)
            )
        """)
        
        # Create CUSTOMER_READING table
        print("Creating CUSTOMER_READING table...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer_reading (
                reading_id VARCHAR PRIMARY KEY,
                customer_id VARCHAR,
                timestamp TIMESTAMP,
                power_kw DOUBLE,
                current_a DOUBLE,
                power_factor DOUBLE,
                FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
            )
        """)
        
        print("\nVerifying tables...")
        tables = conn.execute("SHOW TABLES").fetchdf()
        print("\nCreated tables:")
        print(tables)
        
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    load_dotenv()
    success = create_database_schema()
    if success:
        print("\nDatabase schema created successfully!")
    else:
        print("\nFailed to create database schema.")
