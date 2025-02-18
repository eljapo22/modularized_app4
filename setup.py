from setuptools import setup, find_packages

setup(
    name="transformer_analysis",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "streamlit>=1.24.0",
        "duckdb>=0.8.1",
        "pandas>=2.0.3",
        "plotly>=5.15.0",
        "numpy>=1.24.3",
        "google-auth-oauthlib>=1.0.0",
        "google-auth>=2.22.0",
        "google-api-python-client>=2.95.0",
        "python-dotenv>=1.0.0"
    ]
)
