"""
Script to load test data into MotherDuck
"""
import streamlit as st
import duckdb
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_test_data():
    """Create sample transformer readings data"""
    # Generate sample data
    n_readings = 1000
    n_transformers = 5
    n_feeders = 2
    
    # Generate timestamps for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    timestamps = pd.date_range(start=start_date, end=end_date, periods=n_readings)
    
    # Generate data
    data = []
    for feeder_id in range(1, n_feeders + 1):
        for transformer_id in range(1, n_transformers + 1):
            transformer_name = f"T{feeder_id}_{transformer_id}"
            for ts in timestamps:
                # Generate random load between 20% and 150%
                load_pct = np.random.uniform(20, 150)
                data.append({
                    'transformer_id': transformer_name,
                    'feeder_id': feeder_id,
                    'timestamp': ts,
                    'load_pct': load_pct,
                    'voltage_v': np.random.normal(240, 5),
                    'current_a': np.random.normal(100, 10),
                    'power_kw': np.random.normal(50, 5)
                })
    
    return pd.DataFrame(data)

def main():
    st.title("Load Test Data into MotherDuck")
    
    try:
        # Get token from secrets
        token = st.secrets["MOTHERDUCK_TOKEN"]
        os.environ["motherduck_token"] = token
        
        # Connect to MotherDuck
        conn = duckdb.connect('md:ModApp4DB')
        st.success("✓ Connected to MotherDuck")
        
        # Create test data
        st.write("### Creating test data...")
        df = create_test_data()
        st.write(f"Created {len(df)} sample readings")
        
        # Create table
        st.write("### Creating table...")
        conn.execute("""
            DROP TABLE IF EXISTS transformer_readings;
            
            CREATE TABLE transformer_readings (
                transformer_id VARCHAR,
                feeder_id INTEGER,
                timestamp TIMESTAMP,
                load_pct DOUBLE,
                voltage_v DOUBLE,
                current_a DOUBLE,
                power_kw DOUBLE
            );
        """)
        st.success("✓ Created table")
        
        # Load data
        st.write("### Loading data...")
        conn.execute("INSERT INTO transformer_readings SELECT * FROM df")
        st.success(f"✓ Loaded {len(df)} rows")
        
        # Verify data
        st.write("### Verifying data...")
        result = conn.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT transformer_id) as n_transformers,
                COUNT(DISTINCT feeder_id) as n_feeders,
                MIN(timestamp) as earliest,
                MAX(timestamp) as latest
            FROM transformer_readings
        """).df()
        st.dataframe(result)
        
        st.success("✓ Test data loaded successfully!")
        
    except Exception as e:
        st.error(f"Failed to load test data: {str(e)}")

if __name__ == "__main__":
    main()
