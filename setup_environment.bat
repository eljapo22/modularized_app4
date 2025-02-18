@echo off
echo Setting up virtual environment for Transformer Loading Analysis Application...

REM Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again
    pause
    exit /b 1
)

REM Check if virtualenv is installed
python -m pip show virtualenv > nul 2>&1
if errorlevel 1 (
    echo Installing virtualenv...
    python -m pip install virtualenv
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m virtualenv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment and install requirements
echo Activating virtual environment and installing requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Check if installation was successful
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo To activate the environment manually in the future, run:
echo     venv\Scripts\activate.bat
echo.
echo To start the application, run:
echo     python -m streamlit run app\main.py
echo.
echo Press any key to exit...
pause
