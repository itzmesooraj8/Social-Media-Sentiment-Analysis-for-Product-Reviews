$ErrorActionPreference = "Stop"

Write-Host "🚀 STARTING SENTIMENT BEACON (DEV MODE)..." -ForegroundColor Cyan

# 0. Cleanup Old Processes
Write-Host "Cleaning up old processes on port 8000..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { 
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# 1. Start Backend (New Window)
Write-Host "Starting Backend Service..." -ForegroundColor Green
if (Test-Path "backend\.venv") {
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --reload --port 8000"
} else {
    Write-Host "⚠️  Backend checks: Virtual Environment not found. Please run 'python -m venv .venv' inside backend folder and install requirements." -ForegroundColor Red
}

# 2. Start Frontend (Current Window)
Write-Host "Starting Frontend Service..." -ForegroundColor Green
if (Test-Path "node_modules") {
    npm run dev
} else {
    Write-Host "⚠️  Frontend checks: node_modules not found. Running npm install..." -ForegroundColor Yellow
    npm install
    npm run dev
}
