# Cloud vs Local Architecture Guide

## File Organization

```
modularized_app4/
├── app/
│   ├── config/
│   │   ├── cloud_config.py         # CLOUD-ONLY: Streamlit secrets and cloud settings
│   │   ├── constants.py            # SHARED: Constants for both environments
│   │   ├── credentials.json        # LOCAL-ONLY: OAuth credentials (gitignored)
│   │   └── token.json             # LOCAL-ONLY: OAuth token (gitignored)
│   ├── core/
│   │   ├── database.py            # SHARED: Core database utilities
│   │   └── database_adapter.py    # SHARED: Adapters for both environments
│   └── services/
│       ├── alert_service.py       # SHARED: Alert system with environment checks
│       ├── cloud_data_service.py  # CLOUD-ONLY: MotherDuck specific service
│       └── data_service.py        # SHARED: Data service with environment paths
```

## Environment Detection

The application uses consistent environment detection:
```python
# Check if running in Streamlit Cloud
if os.getenv('STREAMLIT_CLOUD'):
    # Cloud-specific code
else:
    # Local-specific code
```

## Configuration Files

### Local-Only Files (gitignored)
- `app/config/credentials.json`: OAuth credentials for Gmail API
- `app/config/token.json`: Local OAuth token storage

### Cloud-Only Files
- `app/config/cloud_config.py`: Loads settings from Streamlit secrets
- `app/services/cloud_data_service.py`: MotherDuck integration

### Shared Files
- `app/core/database.py`: Core database utilities
- `app/core/database_adapter.py`: Database adapters (Local DuckDB & MotherDuck)
- `app/services/data_service.py`: Data service with environment-specific paths
- `app/services/alert_service.py`: Alert system with environment handling

## Environment-Specific Behaviors

### Local Development
- Uses local file system for data storage
- OAuth flow for Gmail authentication
- Local DuckDB for data queries
- Local configuration files

### Cloud Deployment
- Uses Streamlit secrets for configuration
- MotherDuck for data storage
- Pre-configured Gmail token
- Mount points for data access

## Required Environment Variables

### Local Development
None required, uses local files

### Streamlit Cloud
Required secrets:
- `GMAIL_TOKEN`: Gmail API token
- `DEFAULT_RECIPIENT`: Default email recipient
- `USE_MOTHERDUCK`: Set to "1" to use MotherDuck

## File Access Patterns

### Local Development
```python
# Data paths
data_path = Path(__file__).parent.parent.parent / "data"

# Credentials
credentials_path = Path(__file__).parent.parent / 'config' / 'credentials.json'
token_path = Path(__file__).parent.parent / 'config' / 'token.json'
```

### Cloud Deployment
```python
# Data paths
data_path = Path("/mount/src/modularized_app4/data")

# Credentials from secrets
token_info = st.secrets["GMAIL_TOKEN"]
default_recipient = st.secrets["DEFAULT_RECIPIENT"]
```

## Database Adapters

### Local Development
```python
# Uses LocalDuckDBAdapter
adapter = LocalDuckDBAdapter()
```

### Cloud Deployment
```python
# Uses MotherDuckAdapter when USE_MOTHERDUCK is set
adapter = MotherDuckAdapter()
```

## Deployment Process

1. Local Development:
   - Create `credentials.json` and `token.json` locally
   - Use local DuckDB for development
   - Test features locally

2. Cloud Deployment:
   - Push code to GitHub (sensitive files are gitignored)
   - Configure Streamlit secrets
   - Deploy to Streamlit Cloud

## Common Issues

1. Import Errors:
   - Always use `app.` prefix for internal imports
   - Example: `from app.core.database import SuppressOutput`

2. Path Issues:
   - Use environment check before accessing paths
   - Cloud uses `/mount/src/modularized_app4`
   - Local uses relative paths

3. Configuration:
   - Never commit sensitive files
   - Use Streamlit secrets for cloud configuration
   - Keep local config files in gitignore

## Best Practices

1. Environment Detection:
   - Always use `os.getenv('STREAMLIT_CLOUD')`
   - Don't mix different detection methods

2. File Organization:
   - Keep cloud-specific code in cloud_* files
   - Use environment checks in shared files
   - Never commit sensitive data

3. Testing:
   - Test both environments before deployment
   - Verify secrets are properly set
   - Check data paths in both environments
