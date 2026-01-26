# Start Project Script for Windows (PowerShell)

Write-Host "Starting Sentiment Beacon Setup..." -ForegroundColor Green

# 1. Backend Setup
Write-Host "Setting up Backend..." -ForegroundColor Cyan
cd backend
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
Write-Host "Installing Backend Dependencies..."
pip install -r requirements.txt

# 2. Frontend Setup
Write-Host "Setting up Frontend..." -ForegroundColor Cyan
cd ..
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node modules..."
    npm install
}

# 3. Start Services
Write-Host "Starting Services..." -ForegroundColor Green
Write-Host "Backend running on http://localhost:8000"
Write-Host "Frontend running on http://localhost:5173"

# Run in parallel using Start-Process
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "Done! Check the opened windows." -ForegroundColor Yellow
