from setuptools import setup, find_namespace_packages

setup(
    name="app",  # Changed from transformer_analysis to match import
    version="0.1.0",
    packages=find_namespace_packages(include=['app*']),  # Changed to find_namespace_packages
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
