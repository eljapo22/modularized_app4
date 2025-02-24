import duckdb
import streamlit as st
import toml
from pathlib import Path

# Load secrets from .streamlit/secrets.toml
secrets_path = Path('.streamlit/secrets.toml')
secrets = toml.load(secrets_path)
token = secrets['MOTHERDUCK_TOKEN']

# Connect to MotherDuck
conn = duckdb.connect(f'md:?motherduck_token={token}')

query = '''
WITH all_customers AS (
    SELECT transformer_id, customer_id FROM "Customer Feeder 1"
    UNION
    SELECT transformer_id, customer_id FROM "Customer Feeder 2"
    UNION
    SELECT transformer_id, customer_id FROM "Customer Feeder 3"
    UNION
    SELECT transformer_id, customer_id FROM "Customer Feeder 4"
)
SELECT 
    transformer_id,
    COUNT(DISTINCT customer_id) as num_customers,
    MIN(customer_id) as first_customer,
    MAX(customer_id) as last_customer
FROM all_customers
GROUP BY transformer_id
ORDER BY transformer_id;
'''

# Execute query and print results
results = conn.execute(query).fetchall()
print('Transformer ID | # Customers | First Customer ID | Last Customer ID')
print('-' * 70)
for row in results:
    print(f'{row[0]:<13} | {row[1]:<11} | {row[2]:<15} | {row[3]}')
