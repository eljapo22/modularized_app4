# Transformer Loading Analysis Application

A comprehensive dashboard for monitoring and analyzing transformer loading data, built with Streamlit and DuckDB.

## Quick Start

1. **Setup Environment**:
   ```bash
   setup_environment.bat
   ```

2. **Run Application**:
   ```bash
   python run_main.py
   ```

3. **Access Dashboard**:
   - Open browser
   - Navigate to `http://localhost:8404`

## Features

- Real-time transformer loading monitoring
- Historical data analysis
- Interactive visualizations
- Email alerts for critical loads
- Customer data integration
- Customizable thresholds

## Documentation

For detailed information about the application architecture and implementation, see:
- [Architecture Documentation](modularized_app4_arch.md)
- [Data Retrieval Process](data_retrieval_process.md)

## Data Structure

The application expects data in the following structure:
```
processed_data/
└── transformer_analysis/
    └── hourly/
        └── feeder{1,2,3,4}/
            └── YYYY-MM-DD.parquet
```

## Dependencies

Main dependencies (see `requirements.txt` for full list):
- Python 3.8+
- Streamlit
- DuckDB
- Pandas
- Plotly

## Google API Setup

### Local Development
1. Create a Google Cloud Project and enable Gmail API
2. Create OAuth 2.0 credentials (Desktop application)
3. Download `credentials.json` and place it in `app/config/`
4. Add your email as a test user in OAuth consent screen
5. Run the app locally first to generate `token.json`

### Streamlit Cloud Deployment
1. In Streamlit Cloud dashboard, add these secrets:
   ```toml
   [secrets]
   GMAIL_CREDENTIALS = "YOUR_CREDENTIALS_JSON_CONTENT"
   GMAIL_TOKEN = "YOUR_TOKEN_JSON_CONTENT"
   DEFAULT_RECIPIENT = "your-email@example.com"
   ```

### Security Notes
- NEVER commit credentials to GitHub
- Keep `credentials.json` and `token.json` private
- Use Streamlit's secret management for cloud deployment
- The following files are ignored in git:
  * `credentials.json`
  * `token.json`
  * `.env`
  * `.streamlit/secrets.toml`

## Support

For issues and questions:
1. Check the troubleshooting section in the architecture documentation
2. Review application logs in `logs/app.log`
3. Contact system administrator for data access issues

## License

Internal use only. All rights reserved.
