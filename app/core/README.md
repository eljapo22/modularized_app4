# Core Directory

This directory contains core database and data management functionality for the Transformer Loading Analysis Application.

## Core Components

### database.py (2KB)
- Database connection management
- MotherDuck integration
- Connection caching
- Key features:
  - Cached database connections
  - MotherDuck token handling
  - Connection pool management
  - Error suppression
  - Environment-aware configuration

### database_adapter.py (6.8KB)
- Database interface layer
- Query execution
- Data transformation
- Key functionality:
  - SQL query execution
  - Result set handling
  - Error management
  - Connection pooling
  - Data type conversion

## Database Integration
The core components manage:
1. Database connections
2. Query execution
3. Data retrieval
4. Connection pooling
5. Error handling

## Usage
Core database functionality is used by:
- Data services for retrieval
- Alert system for monitoring
- Dashboard for visualization
- Analysis for processing

## Connection Flow
```
Application
    ↓
database.py (Connection Management)
    ↓
database_adapter.py (Query Execution)
    ↓
MotherDuck Database
```

## Configuration
Database configuration is managed through:
- Environment variables
- Streamlit secrets
- Configuration files
- Feature flags

## Code Interactions and Key Variables

### database.py
Interacts with:
- `config/cloud_config.py`: For environment settings
- `config/feature_flags.py`: For MotherDuck toggle
- `utils/db_utils.py`: For connection pooling
- External: MotherDuck database service

Key Variables:
```python
# Connection Management
_connection_pool: duckdb.DuckDBPyConnection  # Global connection pool
motherduck_token: str                        # MotherDuck authentication
connection_string: str                       # Database connection URL

# Query Parameters
query_timeout: int = 30                      # Query timeout in seconds
max_retries: int = 3                         # Max retry attempts
retry_delay: int = 1                         # Delay between retries

# Connection States
is_connected: bool                           # Connection status
is_motherduck: bool                          # MotherDuck usage flag
```

### database_adapter.py
Interacts with:
- `config/table_config.py`: For schemas
- `config/database_config.py`: For queries
- `services/cloud_data_service.py`: For data retrieval
- `utils/logging_utils.py`: For error tracking

Key Variables and Types:
```python
# Data Types
QueryResult = List[Dict[str, Any]]           # Standard query result type
TableSchema = Dict[str, str]                 # Table schema definition

# Query Components
params: Tuple[Any, ...]                      # Query parameters
query: str                                   # SQL query string
table_name: str                              # Target table

# Error Handling
max_attempts: int = 3                        # Maximum retry attempts
backoff_factor: float = 0.5                  # Retry delay multiplier
```

## Database Operations Examples

### Connection Management:
```python
# In database.py
def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection_pool
    if _connection_pool is None:
        motherduck_token = os.getenv('MOTHERDUCK_TOKEN')
        if USE_MOTHERDUCK and motherduck_token:
            _connection_pool = duckdb.connect(
                f'md:?motherduck_token={motherduck_token}'
            )
        else:
            _connection_pool = duckdb.connect(DATABASE_PATH)
    return _connection_pool
```

### Query Execution:
```python
# In database_adapter.py
def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
    try:
        conn = get_connection()
        if params:
            result = conn.execute(query, params).fetchdf()
        else:
            result = conn.execute(query).fetchdf()
        return result.to_dict('records')
    except Exception as e:
        self._handle_error(e, query, params)
```

## Error States and Recovery

### Common Error Patterns:
```python
# Connection Errors
MotherDuckConnectionError: "Failed to connect to MotherDuck"
TokenError: "Invalid or expired MotherDuck token"

# Query Errors
QueryTimeoutError: "Query execution exceeded timeout"
InvalidSchemaError: "Table schema mismatch"
```

### Error Recovery Flow:
```python
try:
    result = execute_query(query, params)
except MotherDuckConnectionError:
    if retry_count < max_retries:
        time.sleep(retry_delay * (2 ** retry_count))
        retry_count += 1
    else:
        raise DatabaseError("Max retries exceeded")
```

## Integration Points

### Service Layer Integration:
```python
# In cloud_data_service.py
from core.database import get_connection
from core.database_adapter import DatabaseAdapter

class CloudDataService:
    def __init__(self):
        self.db = DatabaseAdapter()
        self.conn = get_connection()
```

### Query Template Usage:
```python
# In database_adapter.py
from config.database_config import TRANSFORMER_DATA_QUERY

def get_transformer_data(self, transformer_id: str) -> QueryResult:
    return self.execute_query(
        TRANSFORMER_DATA_QUERY,
        (transformer_id,)
    )
