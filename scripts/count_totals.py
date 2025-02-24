import duckdb
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
),
feeder_totals AS (
    SELECT 
        CASE 
            WHEN transformer_id LIKE 'S1F1%' THEN 'Feeder 1'
            WHEN transformer_id LIKE 'S1F2%' THEN 'Feeder 2'
            WHEN transformer_id LIKE 'S1F3%' THEN 'Feeder 3'
            WHEN transformer_id LIKE 'S1F4%' THEN 'Feeder 4'
        END as feeder,
        COUNT(DISTINCT transformer_id) as num_transformers,
        COUNT(DISTINCT customer_id) as num_customers
    FROM all_customers
    GROUP BY 1
)
SELECT 
    feeder,
    num_transformers,
    num_customers,
    ROUND(num_customers * 100.0 / SUM(num_customers) OVER (), 1) as pct_of_total
FROM feeder_totals
ORDER BY feeder;
'''

# Execute query and print results
results = conn.execute(query).fetchall()
print('Feeder Summary')
print('-' * 70)
print('Feeder | # Transformers | # Customers | % of Total')
print('-' * 70)
for row in results:
    print(f'{row[0]:<7} | {row[1]:<13} | {row[2]:<11} | {row[3]}%')

# Get total
total_query = '''
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
    COUNT(DISTINCT transformer_id) as total_transformers,
    COUNT(DISTINCT customer_id) as total_customers
FROM all_customers;
'''

totals = conn.execute(total_query).fetchone()
print('-' * 70)
print(f'Total: {totals[0]} transformers, {totals[1]} customers')
