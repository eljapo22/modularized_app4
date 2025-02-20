# Configuration Directory

This directory contains all configuration files for the Transformer Loading Analysis Application.

## Files and Their Functions

### cloud_config.py (1.7KB)
- Manages cloud service configurations
- Gmail API scope definitions
- MotherDuck usage detection
- Environment detection (cloud vs local)
- Email recipient settings

### constants.py (973B)
- System-wide constants
- Loading thresholds:
  - Critical: >= 120%
  - Overloaded: >= 100%
  - Warning: >= 80%
  - Pre-Warning: >= 50%
  - Normal: < 50%
- Color schemes for UI
- Chart colors
- Status indicators

### database_config.py (2.3KB)
- SQL query templates
- Transformer data queries
- Customer data queries
- Data rounding configurations
- Table access patterns

### feature_flags.py (2KB)
- Feature management system
- MotherDuck migration controls
- Feature toggles for:
  - Transformer data
  - Customer data
  - Alert system
- Flag initialization and management

### table_config.py (1.4KB)
- Database schema definitions
- Table templates
- Column specifications
- Data type definitions for:
  - Transformer data
  - Customer data
  - Timestamps
  - Measurements

## Code Interactions and Dependencies

### cloud_config.py
Interacts with:
- `services/cloud_alert_service.py`: For email configuration
- `core/database.py`: For environment detection
- External: Gmail API for email services

Key Variables:
```python
SCOPES: List[str]             # Gmail API scopes
TOKEN_PATH: str              # Path to Gmail token file
CREDENTIALS_PATH: str        # Path to credentials file
IS_CLOUD: bool              # Environment detection
DEFAULT_RECIPIENT: str      # Default alert email
```

### constants.py
Interacts with:
- `services/cloud_alert_service.py`: For thresholds
- `utils/ui_utils.py`: For status colors
- `visualization/charts.py`: For chart colors

Key Variables:
```python
LOADING_THRESHOLDS: Dict[str, float] = {
    'CRITICAL': 120.0,
    'OVERLOADED': 100.0,
    'WARNING': 80.0,
    'PRE_WARNING': 50.0
}

STATUS_COLORS: Dict[str, str] = {
    'Critical': '#dc3545',
    'Overloaded': '#fd7e14',
    'Warning': '#ffc107',
    'Pre-Warning': '#17a2b8',
    'Normal': '#28a745'
}
```

### database_config.py
Interacts with:
- `services/cloud_data_service.py`: For queries
- `core/database.py`: For execution
- `core/database_adapter.py`: For data types

Key SQL Templates:
```sql
TRANSFORMER_DATA_QUERY = """
    SELECT timestamp, voltage_v, current_a, power_kw, loading_percentage
    FROM transformer_data
    WHERE transformer_id = ? AND date(timestamp) BETWEEN ? AND ?
    ORDER BY timestamp
"""

CUSTOMER_DATA_QUERY = """
    SELECT customer_id, usage_kwh, peak_demand_kw
    FROM customer_data
    WHERE transformer_id = ? AND date = ?
"""
```

### feature_flags.py
Interacts with:
- `cloud_main.py`: For feature control
- All service modules: For feature checks

Key Variables:
```python
FEATURE_FLAGS: Dict[str, bool] = {
    'USE_MOTHERDUCK': True,
    'ENABLE_ALERTS': True,
    'SHOW_CUSTOMER_DATA': False,
    'DEBUG_MODE': False
}
```

### table_config.py
Interacts with:
- `core/database_adapter.py`: For schema
- `services/cloud_data_service.py`: For data types

Key Schemas:
```python
TRANSFORMER_TABLE_SCHEMA = {
    'transformer_id': 'TEXT',
    'timestamp': 'TIMESTAMP',
    'voltage_v': 'FLOAT',
    'current_a': 'FLOAT',
    'power_kw': 'FLOAT',
    'loading_percentage': 'FLOAT'
}

CUSTOMER_TABLE_SCHEMA = {
    'customer_id': 'TEXT',
    'transformer_id': 'TEXT',
    'usage_kwh': 'FLOAT',
    'peak_demand_kw': 'FLOAT'
}
```

## Configuration Files
- `cloud_token.json`: Cloud service authentication
- `credentials.json`: API credentials
- `token.json`: Authentication tokens

## Usage
These configurations are used throughout the application to maintain consistent:
- Data handling
- Alert thresholds
- UI appearance
- Feature availability
- Database connections

## Configuration Flow Examples

### Alert Configuration:
```python
# In cloud_alert_service.py
from config.constants import LOADING_THRESHOLDS, STATUS_COLORS

def get_alert_status(loading_percentage: float) -> Tuple[str, str]:
    if loading_percentage >= LOADING_THRESHOLDS['CRITICAL']:
        return 'Critical', STATUS_COLORS['Critical']
    # ... etc
```

### Database Configuration:
```python
# In cloud_data_service.py
from config.database_config import TRANSFORMER_DATA_QUERY
from config.table_config import TRANSFORMER_TABLE_SCHEMA

def get_transformer_data(self, transformer_id: str, date: date) -> pd.DataFrame:
    query = TRANSFORMER_DATA_QUERY
    results = self._execute_query(query, (transformer_id, date))
```

## Environment Variables
Required environment variables:
```bash
MOTHERDUCK_TOKEN=<token>      # MotherDuck connection
STREAMLIT_SERVER_PORT=8501    # Server configuration
DEBUG=False                   # Debug mode
EMAIL_RECIPIENT=user@domain.com  # Alert recipient
