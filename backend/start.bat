@echo off
echo ========================================
echo   Sentiment Beacon - Backend Setup
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)
echo.

echo [2/4] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [3/4] Checking environment variables...
if not exist ..\.env (
    echo WARNING: .env file not found!
    echo Please create .env file with your API keys
    echo See README.md for instructions
    pause
)
echo.

echo [4/4] Starting FastAPI server...
echo.
echo Backend API will run on: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py
