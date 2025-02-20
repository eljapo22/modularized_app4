# Cloud Deployment Checklist

## Pre-Deployment Checks

### 1. Code Organization
- [ ] All imports use `app.` prefix
- [ ] No local-only files in git:
  - [ ] `app/config/credentials.json`
  - [ ] `app/config/token.json`
  - [ ] Any `.env` files
- [ ] All cloud-specific files present:
  - [ ] `app/services/cloud_alert_service.py`
  - [ ] `app/services/cloud_data_service.py`
  - [ ] `app/config/cloud_config.py`

### 2. Environment Variables
- [ ] `requirements.txt` is up to date
- [ ] Python version specified in runtime.txt
- [ ] `.streamlit/config.toml` configured correctly

### 3. Data Files
- [ ] Required data files uploaded to cloud storage
- [ ] Data paths updated for cloud environment
- [ ] Test data available for validation

### 4. GitHub Repository Setup
- [ ] Repository structure:
  ```
  modularized_app4/
  ├── .streamlit/
  │   └── config.toml         # Committed: UI configuration
  ├── .gitignore             # Committed: Properly configured
  ├── app/
  │   ├── config/
  │   │   ├── cloud_config.py    # Committed: Cloud settings
  │   │   ├── credentials.json   # NOT committed: Local only
  │   │   └── token.json        # NOT committed: Local only
  │   └── services/
  │       ├── cloud_*.py        # Committed: Cloud services
  │       └── local_*.py        # Committed: Local services
  ├── requirements.txt       # Committed: Dependencies
  └── README.md             # Committed: Documentation
  ```

- [ ] Branch strategy:
  ```
  main ──────────┬─────────┬─────────
                 │         │
  cloud ─────────┘         │
                           │
  local ─────────────────┘
  ```
  - `main`: Production code, deploys to Streamlit Cloud
  - `cloud`: Testing cloud-specific changes
  - `local`: Local development

### 5. GitHub Actions (Optional)
```yaml
name: Streamlit Cloud Checks

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Check imports
      run: |
        ! find . -type f -name "*.py" | xargs grep "^from config\|^import config"
    - name: Check sensitive files
      run: |
        ! find . -type f -name "credentials.json"
        ! find . -type f -name "token.json"
```

### 6. GitHub-Streamlit Integration
- [ ] Repository connected to Streamlit Cloud
- [ ] Main branch set as deployment source
- [ ] Automatic deploys enabled
- [ ] Deploy URL configured: `https://transformerapp.streamlit.app`

## Streamlit Cloud Configuration

### 1. Secrets Management
```toml
# Required secrets in Streamlit Cloud dashboard
[secrets]
GMAIL_TOKEN = "..." # Gmail API token (JSON format)
DEFAULT_RECIPIENT = "jhnapo2213@gmail.com"
USE_MOTHERDUCK = "1"
```

### 2. Gmail API Setup
1. [ ] Gmail API enabled in Google Cloud Console
2. [ ] OAuth consent screen configured
3. [ ] OAuth credentials created
4. [ ] Token generated and formatted as JSON:
   ```json
   {
     "token": "...",
     "refresh_token": "...",
     "token_uri": "https://oauth2.googleapis.com/token",
     "client_id": "...",
     "client_secret": "...",
     "scopes": ["https://www.googleapis.com/auth/gmail.send"]
   }
   ```

### 3. MotherDuck Configuration
- [ ] MotherDuck connection string set
- [ ] Database tables created
- [ ] Data synchronized

## Deployment Process

### 1. Local Testing
```bash
# Test environment detection
streamlit run main.py

# Verify cloud imports work
python -c "from app.services.cloud_alert_service import CloudAlertService"
python -c "from app.services.cloud_data_service import CloudDataService"
```

### 2. GitHub Workflow
```bash
# Create new feature branch
git checkout -b feature/new-feature

# Make changes and test locally
streamlit run main.py

# Commit changes
git add .
git commit -m "feat: description of changes"

# Push to GitHub
git push origin feature/new-feature

# Create pull request to main
# Wait for Streamlit Cloud preview deployment
# Test in preview environment
# Merge to main if tests pass
```

### 3. Sensitive Data Protection
- [ ] Check no secrets in commits:
  ```bash
  git log -p | grep -i "token"
  git log -p | grep -i "secret"
  git log -p | grep -i "password"
  ```

- [ ] Remove any sensitive data from history:
  ```bash
  # If sensitive data was committed
  git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch app/config/credentials.json" \
  --prune-empty --tag-name-filter cat -- --all
  ```

### 4. Git Repository
- [ ] All changes committed
- [ ] No sensitive data in git history
- [ ] `.gitignore` includes:
  ```
  # Local development
  app/config/credentials.json
  app/config/token.json
  .env
  
  # Python
  __pycache__/
  *.pyc
  
  # Data
  data/
  processed_data/
  ```

### 5. Streamlit Cloud Deployment
1. [ ] Connect GitHub repository
2. [ ] Set main branch as deployment source
3. [ ] Configure build settings:
   - [ ] Python version
   - [ ] Requirements installation
   - [ ] Environment variables

## Streamlit Cloud Deployment Checklist

### Pre-Deployment Steps

#### 1. Code Organization
- [x] Separate cloud and local entry points
  - `app/cloud_main.py` for cloud
  - `app/local_main.py` for local
  - `main.py` as router
- [x] All imports use `app.` prefix in cloud code
- [x] No local-only files imported in cloud code

#### 2. Environment Setup
- [ ] Set Streamlit Cloud secrets
  ```toml
  # .streamlit/secrets.toml in Streamlit Cloud Dashboard
  [gmail]
  token = "YOUR_CLOUD_TOKEN_JSON"
  recipient = "your.email@example.com"
  ```
- [ ] Configure environment variables
  ```
  STREAMLIT_CLOUD=true
  ```

#### 3. Data Access
- [ ] Upload data to cloud storage
  ```bash
  python scripts/prepare_cloud_data.py
  ```
- [ ] Verify data paths in cloud code
  ```python
  # Should use cloud paths
  data_path = Path("/mount/src/modularized_app4/data")
  ```

#### 4. Gmail Integration
- [ ] Generate cloud Gmail token
  ```bash
  python scripts/generate_cloud_token.py
  ```
- [ ] Add token to Streamlit secrets
- [ ] Test email functionality in cloud

### Deployment Process

1. Push code to GitHub:
   ```bash
   git checkout cloud
   git push origin cloud
   ```

2. In Streamlit Cloud Dashboard:
   - Connect to GitHub repository
   - Select `cloud` branch
   - Set Python version to 3.10
   - Add required secrets
   - Deploy app

3. Post-Deployment Verification:
   - Check "Environment Status" in sidebar
   - Test email alerts
   - Verify data loading
   - Check all visualizations

### Troubleshooting

#### Common Issues

1. Import Errors
   ```
   ImportError: No module named 'app'
   ```
   Solution: Ensure all imports use `app.` prefix

2. Data Access Errors
   ```
   FileNotFoundError: data not found
   ```
   Solution: Check cloud data paths and mounting

3. Gmail Authentication
   ```
   google.auth.exceptions.DefaultCredentialsError
   ```
   Solution: Verify cloud token in secrets

### Quick Fixes

1. Refresh Cloud Token:
   ```bash
   python scripts/generate_cloud_token.py --cloud
   ```

2. Update Secrets:
   - Go to Streamlit Cloud Dashboard
   - App Settings → Secrets
   - Paste new token

3. Clear Cache:
   - Stop app in Streamlit Cloud
   - Clear browser cache
   - Restart app

## Post-Deployment Validation

### 1. Environment Check
- [ ] Open app in Streamlit Cloud
- [ ] Check "Environment Status" in sidebar
- [ ] Verify all required secrets are present

### 2. Functionality Testing
- [ ] Test transformer loading analysis
- [ ] Verify data retrieval from MotherDuck
- [ ] Test email alerts:
  1. [ ] Send test alert
  2. [ ] Check email formatting
  3. [ ] Verify dashboard links work

### 3. Error Handling
- [ ] Check error messages are clear
- [ ] Verify logging works
- [ ] Test recovery from common errors:
  - [ ] Missing data
  - [ ] Invalid parameters
  - [ ] Network issues

## Troubleshooting Guide

### Common Issues

1. Import Errors
```python
# Wrong:
from config.constants import SCOPES
# Correct:
from app.config.constants import SCOPES
```

2. Gmail Token Format
```python
# Token must be valid JSON string
token_info = st.secrets["GMAIL_TOKEN"]
if isinstance(token_info, str):
    token_info = json.loads(token_info)
```

3. Data Path Issues
```python
# Wrong:
data_path = Path(__file__).parent / "data"
# Correct:
data_path = Path("/mount/src/modularized_app4/data")
```

### GitHub-Related Issues

1. Wrong Files Committed
```bash
# Remove file from git but keep locally
git rm --cached app/config/credentials.json
git commit -m "remove sensitive file"

# Update .gitignore
echo "app/config/credentials.json" >> .gitignore
```

2. Deployment Failures
- Check GitHub Actions logs
- Verify main branch is clean
- Test deployment preview

3. Import Issues
```bash
# Wrong (will fail in cloud):
git grep "from config import"

# Correct:
git grep "from app.config import"
```

### Error Messages

1. "Module not found"
- Check import paths use `app.` prefix
- Verify file exists in correct location
- Check `__init__.py` files are present

2. "Gmail token invalid"
- Verify token format in Streamlit secrets
- Check token hasn't expired
- Ensure all required fields present

3. "Data not found"
- Check cloud data paths
- Verify MotherDuck connection
- Check data synchronization

## Maintenance

### Regular Checks
- [ ] Monitor Gmail token expiration
- [ ] Check MotherDuck data synchronization
- [ ] Review application logs
- [ ] Test alert system functionality

### Updates
- [ ] Keep dependencies updated
- [ ] Monitor Streamlit Cloud resource usage
- [ ] Update documentation as needed

## Support

For issues or questions:
1. Check Environment Status in sidebar
2. Review error messages and logs
3. Consult this checklist
4. Contact: jhnapo2213@gmail.com
