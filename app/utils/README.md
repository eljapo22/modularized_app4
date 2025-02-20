# Utilities Directory

This directory contains utility functions and helper modules for the Transformer Loading Analysis Application.

## Core Utilities

### ui_utils.py (14KB)
- UI generation utilities
- Chart creation functions
- Dashboard components
- Key functions:
  - `create_banner()`: Page headers
  - `create_metric_tiles()`: Info displays
  - `create_power_chart()`: Power visualization
  - `create_loading_chart()`: Loading status
  - `display_transformer_dashboard()`: Main dashboard
  - `get_alert_status()`: Alert determination

### db_utils.py (2.5KB)
- Database connection management
- Query execution wrapper
- Connection pooling
- Error handling
- MotherDuck integration
- Key functions:
  - `init_db_pool()`: Initialize connections
  - `execute_query()`: Safe query execution
  - `close_pool()`: Resource cleanup

### ui_components.py (2.8KB)
- Reusable UI components
- Styled elements
- Layout utilities
- Components:
  - `create_tile()`: Info tiles
  - `create_section_title()`: Headers
  - `create_banner()`: Page banners
  - `create_section_banner()`: Section headers

### cloud_environment_check.py (4.8KB)
- Environment detection
- Cloud configuration validation
- Service availability checks
- Environment-specific setup

### performance.py (1.1KB)
- Performance monitoring
- Optimization utilities
- Timing functions
- Resource tracking

### logging_utils.py (1.4KB)
- Logging configuration
- Error tracking
- Debug utilities
- Log formatting

### generate_token.py (1.4KB)
- Authentication token generation
- Token management
- Security utilities

## Code Interactions and Key Variables

### ui_utils.py
Interacts with:
- `config/constants.py`: For status colors
- `visualization/charts.py`: For chart creation
- `services/cloud_data_service.py`: For data display
- `cloud_main.py`: For UI components

Key Variables:
```python
# UI Components
title: str                              # Page/section title
transformer_id: str                     # Current transformer
feeder: str                            # Feeder identifier
size_kva: float                        # Transformer size
loading_pct: float                     # Loading percentage

# Chart Data
data: pd.DataFrame                     # Source data
selected_hour: Optional[int]           # Selected hour marker
marker_color: str = '#666666'          # Time marker color
marker_style: str = 'dash'             # Line style

# Layout Configuration
layout_config: Dict[str, Any] = {
    'showlegend': True,
    'hovermode': 'x unified',
    'height': 400,
    'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
}
```

### db_utils.py
Interacts with:
- `core/database.py`: For connections
- `config/feature_flags.py`: For MotherDuck
- `services/cloud_data_service.py`: For queries

Key Variables:
```python
# Database Connection
_connection_pool: Optional[duckdb.DuckDBPyConnection]
motherduck_token: str                  # From environment
query: str                             # SQL query
params: Optional[tuple]                # Query parameters

# Error Handling
max_retries: int = 3                   # Maximum retry attempts
retry_delay: float = 0.5               # Delay between retries
```

### ui_components.py
Interacts with:
- `cloud_main.py`: For UI elements
- `utils/ui_utils.py`: For styling
- `visualization/charts.py`: For display

Key Variables:
```python
# Component Properties
title: str                             # Component title
value: str                             # Display value
has_multiline_title: bool = False      # Title formatting
is_clickable: bool = False             # Interaction flag

# Styling
style: Dict[str, str] = {
    'background-color': 'white',
    'padding': '0.75rem',
    'border': '1px solid #dee2e6',
    'border-radius': '0.25rem'
}
```

### cloud_environment_check.py
Interacts with:
- `config/cloud_config.py`: For settings
- `core/database.py`: For connections
- `services/cloud_alert_service.py`: For email

Key Variables:
```python
# Environment Detection
IS_CLOUD: bool                         # Cloud environment flag
IS_LOCAL: bool                         # Local environment flag
ENV_VARS: List[str] = [               # Required variables
    'MOTHERDUCK_TOKEN',
    'EMAIL_RECIPIENT',
    'DEBUG'
]

# Service Status
services_status: Dict[str, bool] = {
    'database': False,
    'email': False,
    'motherduck': False
}
```

### logging_utils.py
Interacts with:
- All modules: For logging
- `config/cloud_config.py`: For settings

Key Variables:
```python
# Logger Configuration
logger: logging.Logger                 # Module logger
LOG_FORMAT: str                        # Log message format
LOG_LEVEL: str = 'INFO'               # Logging level
LOG_FILE: str = 'app.log'             # Log file path

# Error Tracking
error_count: Dict[str, int] = {        # Error frequency
    'database': 0,
    'api': 0,
    'ui': 0
}
```

## Integration
These utilities support the application by providing:
1. Consistent UI components
2. Reliable database access
3. Environment management
4. Performance optimization
5. Logging and debugging
6. Security functions

## Usage
Utilities are used throughout the application to:
- Create user interface elements
- Manage database connections
- Handle environment configuration
- Monitor performance
- Track errors and logs
- Manage authentication

## Function Examples

### UI Component Creation:
```python
# In ui_utils.py
def create_metric_tiles(transformer_id: str, feeder: str, 
                       size_kva: float, loading_pct: float):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div style="background-color:white; padding:1rem;">
                <p style="margin:0;">Transformer ID</p>
                <h3 style="margin:0;">{transformer_id}</h3>
            </div>
        """, unsafe_allow_html=True)
    # ... etc
```

### Database Operations:
```python
# In db_utils.py
def execute_query(query: str, params: Optional[tuple] = None):
    try:
        if _connection_pool is None:
            init_db_pool()
        
        if params:
            result = _connection_pool.execute(query, params).fetchdf()
        else:
            result = _connection_pool.execute(query).fetchdf()
            
        return result.to_dict('records')
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise
```

### Environment Checks:
```python
# In cloud_environment_check.py
def validate_environment():
    missing_vars = []
    for var in ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
```

## Integration Examples

### UI Integration:
```python
# In cloud_main.py
from utils.ui_utils import create_banner, create_metric_tiles
from utils.ui_components import create_section_title

def render_dashboard():
    create_banner("Transformer Loading Analysis")
    create_section_title("Current Status")
    create_metric_tiles(
        transformer_id=selected_transformer,
        feeder=feeder_num,
        size_kva=transformer_size,
        loading_pct=current_loading
    )
```

### Database Integration:
```python
# In cloud_data_service.py
from utils.db_utils import execute_query
from utils.logging_utils import logger

def get_transformer_data(self, transformer_id: str):
    try:
        return execute_query(
            TRANSFORMER_DATA_QUERY,
            (transformer_id,)
        )
    except Exception as e:
        logger.error(f"Failed to get transformer data: {e}")
        raise
