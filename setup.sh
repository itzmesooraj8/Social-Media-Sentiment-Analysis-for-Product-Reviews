#!/bin/bash

echo "=========================================="
echo "  Sentiment Beacon - Automated Setup 🚀"
echo "=========================================="

# Ensure we are in the project root
cd "$(dirname "$0")"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    exit 1
fi

# 2. Backend Setup
echo ""
echo "[1/4] Setting up Backend..."
cd backend

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating venv and installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# 3. Database Seeding
echo ""
echo "[2/4] Seeding Demo Data..."
python scripts/populate_data.py

# 4. Frontend Setup
echo ""
echo "[3/4] Setting up Frontend..."
cd ..
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

# 5. Launch
echo ""
echo "[4/4] Launching System..."

# Start Backend in background
echo "Starting Backend (Port 8000)..."
(cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  System is running!"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo "  Press Ctrl+C to stop all services."
echo "=========================================="

# Trap SIGINT to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

wait
