import duckdb
import streamlit as st

def test_connection():
    """Test connecting to MotherDuck and querying our table"""
    try:
        # Connect to DuckDB with MotherDuck token from Streamlit secrets
        print("1. Connecting to DuckDB...")
        motherduck_token = st.secrets["MOTHERDUCK_TOKEN"]
        con = duckdb.connect(f'md:?motherduck_token={motherduck_token}')
        
        # Test querying our table
        print("\n2. Testing query on Transformer Feeder 1:")
        result = con.execute("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                transformer_id,
                loading_percentage,
                load_range
            FROM "Transformer Feeder 1"
            ORDER BY timestamp
        """).fetchdf()
        
        print("\nResults:")
        print(result)
        
        print("\nConnection test successful!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'con' in locals():
            con.close()

if __name__ == "__main__":
    test_connection()
