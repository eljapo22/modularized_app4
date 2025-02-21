"""
Table configuration for MotherDuck database
"""

# Table names - with proper quoting for SQL
TRANSFORMER_TABLE_TEMPLATE = '"Transformer Feeder {}"'  # Already includes quotes for SQL
CUSTOMER_TABLE_TEMPLATE = '"Customer Feeder {}"'        # Already includes quotes for SQL

# List of available feeder numbers
FEEDER_NUMBERS = [1]  # Start with just feeder 1 for now

# Transformer table columns with their exact types from MotherDuck
TRANSFORMER_COLUMNS = {
    'timestamp': 'TIMESTAMP_NS',
    'voltage_v': 'DOUBLE',
    'size_kva': 'DOUBLE',
    'loading_percentage': 'DOUBLE',  # Will be rounded to xx.xx in queries
    'current_a': 'DOUBLE',          # Will be rounded to xx.xx in queries
    'power_kw': 'DOUBLE',          # Will be rounded to xx.xx in queries
    'power_kva': 'DOUBLE',
    'power_factor': 'DOUBLE',
    'transformer_id': 'VARCHAR',
    'load_range': 'VARCHAR'
}

# Customer table columns with their exact types from MotherDuck
CUSTOMER_COLUMNS = {
    'current_a': 'DOUBLE',         # Will be rounded to x.xx in queries
    'customer_id': 'VARCHAR',
    'hour': 'VARCHAR',
    'power_factor': 'DOUBLE',
    'power_kva': 'DOUBLE',        # Will be rounded to x.xx in queries
    'power_kw': 'DOUBLE',         # Will be rounded to x.xx in queries
    'size_kva': 'DOUBLE',
    'timestamp': 'TIMESTAMP_NS',
    'transformer_id': 'VARCHAR',
    'voltage_v': 'INTEGER'
}
