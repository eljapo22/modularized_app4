"""
Table configuration for MotherDuck database
"""

# Table names
TRANSFORMER_TABLE_TEMPLATE = "Transformer Feeder {}"  # 1-4
CUSTOMER_TABLE_TEMPLATE = "Customer Feeder {}"        # 1-4

# List of available feeder numbers
FEEDER_NUMBERS = [1, 2, 3, 4]

# Common column names
COMMON_COLUMNS = {
    'timestamp': 'timestamp',
    'transformer_id': 'transformer_id',
    'power_kw': 'power_kw',
    'power_factor': 'power_factor',
    'voltage_v': 'voltage_v',
    'current_a': 'current_a'
}

TRANSFORMER_COLUMNS = {
    **COMMON_COLUMNS,
    'power_kva': 'power_kva',
    'loading_percentage': 'loading_percentage'
}

CUSTOMER_COLUMNS = {
    **COMMON_COLUMNS,
    'customer_id': 'customer_id'
}
