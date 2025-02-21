# Project Structure Guide

## Directory Structure

```
modularized_app4/
├── app/                           # Main application package
│   ├── __init__.py
│   ├── cloud_main.py             # Cloud deployment entry point
│   ├── local_main.py             # Local development entry point
│   ├── config/                   # Configuration files
│   │   ├── __init__.py
│   │   ├── cloud_config.py       # Cloud-specific settings
│   │   ├── database_config.py    # Database configuration
│   │   └── feature_flags.py      # Feature toggles
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   └── database.py          # Database operations
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── cloud_data_service.py
│   │   └── cloud_alert_service.py
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── ui_utils.py
│   │   └── performance.py
│   └── visualization/            # Data visualization
│       ├── __init__.py
│       ├── charts.py
│       └── tables.py
├── .streamlit/                   # Streamlit configuration
│   └── secrets.toml             # Secrets (not in version control)
├── tests/                        # Test files
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── PROJECT_STRUCTURE.md          # This file
└── README.md                     # Project overview
```

## Important Rules

1. **Entry Points**
   - Cloud deployment MUST use: `app/cloud_main.py`
   - Local development MUST use: `app/local_main.py`
   - NO Python files should exist in the root directory

2. **Branch Management**
   - `main`: Development branch
   - `cloud-deployment`: Production branch for Streamlit Cloud
   - Always merge changes from `main` to `cloud-deployment` before deployment

3. **Configuration**
   - All configuration files MUST be in `app/config/`
   - Secrets MUST be in `.streamlit/secrets.toml` (not in version control)
   - Environment-specific settings in respective config files

4. **Code Organization**
   - All application code MUST be under the `app/` directory
   - Each subdirectory MUST have its own `__init__.py`
   - Each subdirectory SHOULD have its own `README.md`

## Streamlit Cloud Deployment

1. **Configuration**
   ```toml
   # .streamlit/config.toml
   [server]
   # Ensure this points to the cloud entry point
   entrypoint = "app/cloud_main.py"
   ```

2. **Environment Variables**
   - `STREAMLIT_SERVER_PORT`: Set by Streamlit Cloud
   - `STREAMLIT_CLOUD`: Set to 'true' in cloud environment

3. **Deployment Checklist**
   - [ ] All changes merged to `cloud-deployment` branch
   - [ ] Entry point correctly set to `app/cloud_main.py`
   - [ ] All dependencies in `requirements.txt`
   - [ ] Secrets configured in Streamlit Cloud dashboard

## Common Issues Prevention

1. **Duplicate Files**
   - Never create Python files in the root directory
   - Use `git status` to check for untracked files
   - Regular cleanup: `git clean -n` to preview, `git clean -f` to remove

2. **Branch Sync**
   ```bash
   # Before deployment
   git checkout main
   git pull
   git checkout cloud-deployment
   git merge main
   git push origin cloud-deployment
   ```

3. **Cache Issues**
   - Clear Streamlit cache: `st.cache_data.clear()`
   - Browser hard refresh: `Ctrl + Shift + R`
   - Check Python cache: Remove `__pycache__` directories

## Development Workflow

1. **Local Development**
   ```bash
   # Run local version
   streamlit run app/local_main.py
   ```

2. **Cloud Testing**
   ```bash
   # Run cloud version locally
   streamlit run app/cloud_main.py
   ```

3. **Deployment**
   ```bash
   # Merge and deploy
   git checkout cloud-deployment
   git merge main
   git push origin cloud-deployment
   ```

## Monitoring and Debugging

1. **Logging**
   - All modules should use the logging configuration in `utils/logging_utils.py`
   - Log files are stored in `logs/` (not in version control)

2. **Error Tracking**
   - Check Streamlit Cloud logs in dashboard
   - Monitor application logs for issues
   - Use logging levels appropriately:
     - DEBUG: Detailed information
     - INFO: General operational events
     - WARNING: Unexpected but handled events
     - ERROR: Serious issues that need attention
