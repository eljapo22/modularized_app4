"""
Main application runner that ensures proper Python path setup
"""
import os
import sys
import subprocess

def run_app():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Run the Streamlit app
    subprocess.run([
        "streamlit", "run",
        os.path.join(project_root, "app", "main.py"),
        "--server.port", "8404"
    ])

if __name__ == "__main__":
    run_app()
