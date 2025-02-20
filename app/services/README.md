# Services Directory

This directory contains the core business logic services for the Transformer Loading Analysis Application.

## Core Services

### cloud_data_service.py (14KB)
- Primary data retrieval service
- Transformer data operations
- Date range handling
- Database interactions
- Data validation and processing
- Methods:
  - `get_transformer_data()`: Single point data
  - `get_transformer_data_range()`: Date range data
  - `get_feeder_options()`: Available feeders
  - `get_load_options()`: Load configurations

### cloud_alert_service.py (11.7KB)
- Alert system implementation
- Loading threshold monitoring
- Email alert generation
- Status determination
- Key features:
  - HTML-formatted emails
  - Color-coded alerts
  - Deep linking to dashboard
  - Gmail integration
  - Alert thresholds management

### data_service.py (24.4KB)
- Base data service interface
- Common data operations
- Shared utility methods
- Data transformation logic
- Error handling

### local_alert_service.py (6.4KB)
- Local development alert system
- Test email functionality
- Mock alert generation
- Development utilities

## Service Integration
These services work together to:
1. Retrieve transformer data
2. Monitor loading conditions
3. Generate alerts
4. Send notifications
5. Maintain data consistency

## Alert System Flow
```
Data Service
    ↓
Loading Analysis
    ↓
Alert Threshold Check
    ↓
Email Generation
```

## Code Interactions

### cloud_data_service.py
Interacts with:
- `core/database.py`: For database connections
- `config/database_config.py`: For SQL queries
- `config/table_config.py`: For table schemas
- `cloud_main.py`: For data requests
- `cloud_alert_service.py`: Provides data for alerts

Key Variables:
```python
self._transformer_ids: List[str]  # Cache of available transformer IDs
self.min_date: date              # Minimum available date (2024-01-01)
self.max_date: date              # Maximum available date (2024-06-28)
results_df: pd.DataFrame         # Transformer data with columns:
    - timestamp: datetime        # Measurement timestamp
    - voltage_v: float          # Voltage in volts
    - loading_percentage: float  # Current loading %
    - current_a: float          # Current in amperes
    - power_kw: float          # Power in kilowatts
```

### cloud_alert_service.py
Interacts with:
- `config/constants.py`: For alert thresholds
- `utils/ui_utils.py`: For status display
- `cloud_main.py`: For alert triggers
- `visualization/charts.py`: For alert visualization

Key Variables:
```python
self.app_url: str               # Application URL for deep links
self.email: str                 # Alert recipient email
loading_percentage: float       # Current loading value
alert_time: datetime           # Time of alert condition
alert_status: str              # One of: Critical, Overloaded, Warning, Pre-Warning, Normal
```

### data_service.py
Interacts with:
- `core/database_adapter.py`: For query execution
- `config/feature_flags.py`: For feature management
- `utils/db_utils.py`: For database operations

Key Variables:
```python
query_date: date               # Date for data retrieval
feeder_num: int               # Feeder number (1-N)
transformer_id: str           # Transformer identifier
size_kva: float              # Transformer size in kVA
```

## Data Flow Examples

### Alert Generation Flow:
```python
# In cloud_main.py
results = data_service.get_transformer_data_range(
    transformer_id=selected_transformer,
    start_date=date_range[0],
    end_date=date_range[1]
)

# In cloud_alert_service.py
max_loading_idx = results_df['loading_percentage'].idxmax()
max_loading_row = results_df.loc[max_loading_idx]
alert_time = max_loading_idx  # This is the datetime of max loading

# Alert status determination
status, color = get_alert_status(max_loading_row['loading_percentage'])
```

### Data Query Flow:
```python
# In cloud_data_service.py
def get_transformer_data_range(self, transformer_id: str, start_date: date, end_date: date):
    query = TRANSFORMER_DATA_QUERY  # From database_config.py
    results = self._execute_query(query, (transformer_id, start_date, end_date))
    return pd.DataFrame(results)
```

## State Management
- Session state in `cloud_main.py` manages:
  ```python
  st.session_state.results      # Current query results
  st.session_state.date_range   # Selected date range
  st.session_state.transformer  # Selected transformer
  ```

## Error Handling
Common error states:
```python
'str' object has no attribute 'date'  # Date format error
'loading_percentage' not in DataFrame  # Missing data
MotherDuck connection failed          # Database error
```

## Usage
Services are initialized and coordinated through the main application entry points (`cloud_main.py` or `local_main.py`).
