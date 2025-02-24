import duckdb
import streamlit as st

# Connect to MotherDuck
token = st.secrets.get('MOTHERDUCK_TOKEN')
conn = duckdb.connect(f'md:?motherduck_token={token}')

# Show transformer IDs from each feeder
for i in range(1, 5):
    print(f"\nTransformer IDs in Feeder {i}:")
    ids = conn.execute(f'''
        SELECT DISTINCT transformer_id 
        FROM "Transformer Feeder {i}"
        ORDER BY transformer_id
        LIMIT 5;
    ''').fetchall()
    for row in ids:
        print(row[0])
        
    # Show sample data for first transformer
    if ids:
        first_id = ids[0][0]
        print(f"\nSample data for {first_id}:")
        sample = conn.execute(f'''
            SELECT timestamp, loading_percentage, load_range
            FROM "Transformer Feeder {i}"
            WHERE transformer_id = ?
            ORDER BY timestamp
            LIMIT 3;
        ''', [first_id]).fetchall()
        for row in sample:
            print(row)

conn.close()
