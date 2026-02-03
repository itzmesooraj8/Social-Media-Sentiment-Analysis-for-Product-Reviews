$ErrorActionPreference = "Stop"

Write-Host "🚀 STARTING SENTIMENT BEACON..." -ForegroundColor Cyan

# 1. Database Verification Skipped (Migration script removed per requirements)
Write-Host "1️⃣  Database Verification: Skipped (Pre-configured)" -ForegroundColor Yellow

# 2. Kill Old Backend
Write-Host "2️⃣  Cleaning up old processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { 
    Write-Host "   Killing PID $($_.OwningProcess)"
    Stop-Process -Id $_.OwningProcess -Force 
}

# 3. Start Backend
Write-Host "3️⃣  Starting Backend Server..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn main:app --reload --port 8000" `
    -WorkingDirectory "backend" `
    -PassThru `
    -NoNewWindow

# 4. Start Frontend
Write-Host "4️⃣  Starting Frontend..." -ForegroundColor Green
Write-Host "✅ SYSTEM LAUNCHED! Access at http://localhost:5173" -ForegroundColor Cyan
npm run dev
