# Transformer Loading Analysis Application

## Directory Structure

### Main Components
- `cloud_main.py`: Cloud deployment entry point
- `local_main.py`: Local development entry point
- `__init__.py`: Application initialization

### Subdirectories

#### /config
- Configuration files
- Constants
- Database settings
- Feature flags
- Table schemas

#### /core
- Database management
- Connection handling
- Query execution
- Data adapters

#### /services
- Business logic
- Data retrieval
- Alert system
- Email notifications

#### /utils
- Helper functions
- UI components
- Database utilities
- Environment checks

#### /visualization
- Chart generation
- Data presentation
- Dashboard components
- Interactive displays

## Application Flow

### Data Flow
```
User Interface (cloud_main.py)
    ↓
Services Layer
    ↓
Core Database
    ↓
Data Processing
    ↓
Visualization
```

### Alert System
```
Data Monitoring
    ↓
Threshold Check
    ↓
Alert Generation
    ↓
Email Notification
```

## Key Features
1. Real-time transformer monitoring
2. Loading status visualization
3. Email alert system
4. Interactive dashboard
5. Data analysis tools

## Configuration
- Environment-based settings
- Feature flags
- Database connections
- Alert thresholds
- UI customization

## Usage
The application provides:
- Transformer loading analysis
- Alert monitoring
- Data visualization
- Performance tracking
- Email notifications

## Code Interactions and Key Variables

### cloud_main.py
Interacts with:
- `services/cloud_data_service.py`: For data retrieval
- `services/cloud_alert_service.py`: For alerts
- `utils/ui_utils.py`: For UI components
- `visualization/charts.py`: For displays
- `config/*`: For all configurations

Key Variables:
```python
# Streamlit State
st.session_state: SessionState = {
    'transformer': str,              # Selected transformer ID
    'date_range': Tuple[date, date], # Selected date range
    'results': pd.DataFrame,         # Query results
    'alert_status': str,            # Current alert status
    'email_sent': bool              # Alert email status
}

# Page Configuration
st.set_page_config(
    page_title="Transformer Loading Analysis",
    page_icon="⚡",
    layout="wide"
)

# Service Instances
data_service: CloudDataService      # Data retrieval service
alert_service: CloudAlertService    # Alert handling service
```

### local_main.py
Interacts with:
- `services/local_data_service.py`: For local data
- `services/local_alert_service.py`: For local alerts
- Same UI/visualization components as cloud_main.py

Key Variables:
```python
# Development Settings
DEBUG: bool = True                  # Debug mode flag
LOCAL_DATA_PATH: str               # Local data location
MOCK_EMAIL: bool = True            # Email simulation

# Test Data
sample_data: pd.DataFrame = {
    'transformer_id': ['TEST_001'],
    'timestamp': [datetime.now()],
    'loading_percentage': [75.0]
}
```

## Cross-Component Data Flow

### 1. Data Retrieval Flow
```python
# User selects parameters in cloud_main.py
transformer_id = st.selectbox("Select Transformer", transformer_options)
date_range = st.date_input("Select Date Range", [start_date, end_date])

# Data service retrieves data
results = data_service.get_transformer_data_range(
    transformer_id=transformer_id,
    start_date=date_range[0],
    end_date=date_range[1]
)

# Results processed through visualization
charts.display_transformer_dashboard(results)
```

### 2. Alert System Flow
```python
# Alert check in cloud_main.py
if st.button("Search & Alert"):
    # Get data from service
    results = data_service.get_transformer_data_range(...)
    
    # Process through alert service
    alert_service.check_and_send_alert(
        results,
        transformer_id,
        date_range
    )
    
    # Update UI
    st.success("Alert check complete!")
```

### 3. Configuration Flow
```python
# Environment setup
from config.cloud_config import IS_CLOUD
from config.feature_flags import FEATURE_FLAGS

if IS_CLOUD:
    # Cloud-specific setup
    validate_environment()
    init_cloud_services()
else:
    # Local setup
    init_local_services()

if FEATURE_FLAGS['USE_MOTHERDUCK']:
    # MotherDuck setup
    init_motherduck_connection()
```

## Key Integration Points

### Database Integration
```python
# In cloud_main.py
from core.database import get_connection
from services.cloud_data_service import CloudDataService

# Initialize services
conn = get_connection()
data_service = CloudDataService(conn)
```

### UI Integration
```python
# In cloud_main.py
from utils.ui_utils import create_banner
from visualization.charts import display_transformer_dashboard

def main():
    create_banner("Transformer Loading Analysis")
    results = data_service.get_transformer_data(...)
    display_transformer_dashboard(results)
```

### Alert Integration
```python
# In cloud_main.py
from services.cloud_alert_service import CloudAlertService

alert_service = CloudAlertService(
    email_recipient=st.secrets["email"]["recipient"],
    app_url=st.secrets["app"]["url"]
)
```

## Error Handling

### Common Error States
```python
# Database Errors
MotherDuckConnectionError: "Failed to connect to MotherDuck"
QueryError: "Invalid query parameters"

# UI Errors
StreamlitAPIError: "Cannot modify state after widget"
WidgetError: "Duplicate widget key"

# Alert Errors
EmailError: "Failed to send alert email"
ValidationError: "Invalid date range selected"
```

### Error Recovery
```python
try:
    results = data_service.get_transformer_data(...)
except Exception as e:
    st.error(f"Error retrieving data: {str(e)}")
    logger.error(f"Data retrieval failed: {e}")
    # Attempt recovery or show fallback UI
