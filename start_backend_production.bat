@echo off
echo Starting Backend in High-Performance Mode (4 Workers)...
cd backend
.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
pause
