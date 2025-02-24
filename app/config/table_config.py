"""
Table configuration for MotherDuck database
"""

# Table names - with proper quoting for SQL
TRANSFORMER_TABLE_TEMPLATE = '"Transformer Feeder {}"'  # Template for transformer tables
CUSTOMER_TABLE_TEMPLATE = '"Customer Feeder {}"'        # Template for customer tables

# List of available feeder numbers
FEEDER_NUMBERS = [1, 2, 3, 4]  # All available feeders

# Transformer ID pattern: S1F{feeder}ATF{number}
TRANSFORMER_ID_PATTERN = "S1F{}ATF{:03d}"  # e.g., S1F2ATF001

# Customer ID pattern: {transformer_id}C{number}
CUSTOMER_ID_PATTERN = "{}C{:03d}"  # e.g., S1F1ATF001C001

# Transformer table columns with their exact types from MotherDuck
TRANSFORMER_COLUMNS = {
    'timestamp': 'TIMESTAMP',
    'transformer_id': 'VARCHAR',
    'size_kva': 'DOUBLE',
    'load_range': 'VARCHAR',
    'loading_percentage': 'DOUBLE',
    'current_a': 'DOUBLE',
    'voltage_v': 'DOUBLE',
    'power_kw': 'DOUBLE',
    'power_kva': 'DOUBLE',
    'power_factor': 'DOUBLE'
}

# Customer table columns with their exact types from MotherDuck
CUSTOMER_COLUMNS = {
    'timestamp': 'TIMESTAMP',
    'customer_id': 'VARCHAR',
    'transformer_id': 'VARCHAR',
    'power_kw': 'DOUBLE',
    'power_factor': 'DOUBLE',
    'power_kva': 'DOUBLE',
    '__index_level_0__': 'BIGINT',
    'voltage_v': 'INTEGER',
    'current_a': 'DOUBLE'
}

def parse_transformer_id(transformer_id: str) -> tuple[int, int]:
    """Parse a transformer ID to get feeder number and transformer number
    
    Args:
        transformer_id: ID in format S1F{feeder}ATF{number}
        
    Returns:
        Tuple of (feeder_number, transformer_number)
    """
    # Extract feeder number (e.g., 2 from S1F2ATF001)
    feeder = int(transformer_id[3])
    # Extract transformer number (e.g., 1 from S1F2ATF001)
    transformer = int(transformer_id[-3:])
    return feeder, transformer

def get_transformer_table(transformer_id: str) -> str:
    """Get the correct transformer table name for a transformer ID
    
    Args:
        transformer_id: ID in format S1F{feeder}ATF{number}
        
    Returns:
        Table name in format "Transformer Feeder {number}"
    """
    feeder, _ = parse_transformer_id(transformer_id)
    return TRANSFORMER_TABLE_TEMPLATE.format(feeder)

def get_customer_table(transformer_id: str) -> str:
    """Get the correct customer table name for a transformer ID
    
    Args:
        transformer_id: ID in format S1F{feeder}ATF{number}
        
    Returns:
        Table name in format "Customer Feeder {number}"
    """
    feeder, _ = parse_transformer_id(transformer_id)
    return CUSTOMER_TABLE_TEMPLATE.format(feeder)
