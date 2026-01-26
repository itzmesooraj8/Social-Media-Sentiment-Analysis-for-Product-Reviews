@echo off
echo ==========================================
echo   Sentiment Beacon - Automated Setup 🚀
echo ==========================================

cd /d "%~dp0"

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: 2. Backend Setup
echo.
echo [1/4] Setting up Backend...
cd backend

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating venv and installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt

:: 3. Database Seeding
echo.
echo [2/4] Seeding Demo Data...
python scripts/populate_data.py

:: 4. Frontend Setup
echo.
echo [3/4] Setting up Frontend...
cd ..
if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install
)

:: 5. Launch
echo.
echo [4/4] Launching System...
echo Starting Backend (Port 8000)...
start "Sentiment Beacon Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn main:app --reload --port 8000"

echo Starting Frontend (Port 5173)...
start "Sentiment Beacon Frontend" cmd /k "npm run dev"

echo.
echo ==========================================
echo   System is running!
echo   Frontend: http://localhost:8000 (Vite default) or checks console
echo   Backend:  http://localhost:8000/docs
echo ==========================================
pause
