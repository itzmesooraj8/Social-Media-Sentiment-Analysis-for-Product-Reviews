#!/bin/bash

echo "========================================"
echo "  Sentiment Beacon - Backend Setup"
echo "========================================"
echo ""

echo "[1/4] Checking Python installation..."
python3 --version || python --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.9+ from https://python.org"
    exit 1
fi
echo ""

echo "[2/4] Installing Python dependencies..."
pip3 install -r requirements.txt || pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

echo "[3/4] Checking environment variables..."
if [ ! -f ../.env ]; then
    echo "WARNING: .env file not found!"
    echo "Please create .env file with your API keys"
    echo "See README.md for instructions"
    read -p "Press enter to continue..."
fi
echo ""

echo "[4/4] Starting FastAPI server..."
echo ""
echo "Backend API will run on: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 main.py || python main.py
