"""
Database table configuration
"""

# Table names
TRANSFORMER_TABLE_TEMPLATE = "TransformerFeeder_{}"  # 1-4
CUSTOMER_TABLE_TEMPLATE = "CustomerFeeder_{}"        # 1-4

# List of available feeder numbers
FEEDER_NUMBERS = [1, 2, 3, 4]

# Column names - must match database schema exactly
COMMON_COLUMNS = {
    'TIMESTAMP': 'timestamp',
    'POWER_KW': 'power_kw',
    'POWER_FACTOR': 'power_factor',
    'POWER_KVA': 'power_kva',
    'VOLTAGE_V': 'voltage_v',
    'CURRENT_A': 'current_a',
    'INDEX': 'index_level_0_'
}

TRANSFORMER_COLUMNS = {
    **COMMON_COLUMNS,
    'TRANSFORMER_ID': 'transformer_id'
}

CUSTOMER_COLUMNS = {
    **COMMON_COLUMNS,
    'CUSTOMER_ID': 'customer_id',
    'TRANSFORMER_ID': 'transformer_id'  # Foreign key to transformer
}
