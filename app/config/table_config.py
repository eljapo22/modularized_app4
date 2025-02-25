"""
Table configuration for MotherDuck database

Database Structure:
-----------------
1. Tables:
   - Each feeder (1-4) has two tables:
     * "Transformer Feeder X": Contains transformer measurements
     * "Customer Feeder X": Contains customer measurements
   - Total of 8 tables (4 transformer + 4 customer tables)

2. Naming Conventions:
   - Transformer IDs: S1FxATFyyy where:
     * S1 = Station 1
     * Fx = Feeder number (1-4)
     * ATF = Auto Transformer
     * yyy = Sequential number (001-999)
   - Customer IDs: Unique identifiers linked to transformers

3. Data Types and Rounding Requirements:
   Transformer Tables:
   - timestamp: TIMESTAMP_NS (no rounding)
   - voltage_v: DOUBLE (no rounding)
   - size_kva: DOUBLE (no rounding)
   - loading_percentage: DOUBLE -> DECIMAL(3,0) (no decimals, e.g., 85%)
   - current_a: DOUBLE -> DECIMAL(5,2) (2 decimals, e.g., 10.25 A)
   - power_kw: DOUBLE -> DECIMAL(5,2) (2 decimals, e.g., 45.75 kW)
   - power_kva: DOUBLE -> DECIMAL(5,2) (2 decimals, e.g., 48.30 kVA)
   - power_factor: DOUBLE -> DECIMAL(4,3) (3 decimals, e.g., 0.945)
   - transformer_id: VARCHAR
   - load_range: VARCHAR

   Customer Tables:
   - index_level_0: BIGINT
   - current_a: DOUBLE -> DECIMAL(5,2) (2 decimals)
   - customer_id: VARCHAR
   - hour: VARCHAR
   - power_factor: DOUBLE -> DECIMAL(4,3) (3 decimals)
   - power_kva: DOUBLE -> DECIMAL(5,2) (2 decimals)
   - power_kw: DOUBLE -> DECIMAL(5,2) (2 decimals)
   - size_kva: DOUBLE (no rounding)
   - timestamp: TIMESTAMP_NS
   - transformer_id: VARCHAR
   - voltage_v: INTEGER

4. Data Coverage:
   - Time Range: 2024-01-01 to 2024-06-28
   - Measurement Frequency: Hourly
"""

# Column decimal place configuration
DECIMAL_PLACES = {
    'loading_percentage': 0,
    'current_a': 2,
    'power_kw': 2,
    'power_kva': 2,
    'power_factor': 3
}

# Table names - with proper quoting for SQL
TRANSFORMER_TABLE_TEMPLATE = '"Transformer Feeder {}"'  # Already includes quotes for SQL
CUSTOMER_TABLE_TEMPLATE = '"Customer Feeder {}"'        # Already includes quotes for SQL

# List of available feeder numbers - we know there are exactly 4 feeders
FEEDER_NUMBERS = [1, 2, 3, 4]  # All feeders in the database

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
    'index_level_0': 'BIGINT',
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
