#!/bin/bash

echo "========================================"
echo "Real-Time Micro-Bridge - Quick Start"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js v18+ from https://nodejs.org"
    exit 1
fi

echo "[1/5] Checking Node.js version..."
node --version
echo ""

# Backend setup
echo "[2/5] Setting up backend..."
cd backend

if [ ! -d "node_modules" ]; then
    echo "Installing backend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] Backend npm install failed!"
        exit 1
    fi
fi

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Starting backend server..."
npm start &
BACKEND_PID=$!
sleep 3
cd ..

# Frontend setup
echo "[3/5] Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] Frontend npm install failed!"
        kill $BACKEND_PID
        exit 1
    fi
fi

if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "[4/5] Starting frontend server..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "[5/5] System Ready!"
echo "========================================"
echo "Backend:  http://localhost:3000"
echo "Frontend: http://localhost:5173"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
