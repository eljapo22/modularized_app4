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

## Support

For issues and questions:
1. Check the troubleshooting section in the architecture documentation
2. Review application logs in `logs/app.log`
3. Contact system administrator for data access issues

## License

Internal use only. All rights reserved.
