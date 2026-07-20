#!/bin/bash

# Gurukul Service Orchestration Script (Production)
# ===============================================
# Starts services in deterministic order with dependency verification.

echo "=== Gurukul Production Startup ==="

# 1. Verify environment
if [ ! -f "backend/.env" ]; then
    echo "ERROR: backend/.env missing!"
    exit 1
fi

# 2. Set deterministic order
SERVICES=("vaani-engine" "backend")

# 3. Start Vaani Engine (ML Core)
echo "[1/2] Starting Vaani Engine..."
cd vaani-engine
python3 voice_service_api.py > ../logs/vaani.log 2>&1 &
VAANI_PID=$!
cd ..

# Wait for Vaani Health
echo "Waiting for Vaani to be healthy (Port 8008)..."
MAX_RETRIES=30
COUNT=0
until $(curl --output /dev/null --silent --head --fail http://localhost:8008/health); do
    printf '.'
    sleep 2
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Vaani failed to start."
        kill $VAANI_PID
        exit 1
    fi
done
echo " [OK]"

# 4. Start Gurukul Backend
echo "[2/2] Starting Gurukul Backend..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 3000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for Backend Health
echo "Waiting for Backend to be healthy (Port 3000)..."
until $(curl --output /dev/null --silent --head --fail http://localhost:3000/system/health); do
    printf '.'
    sleep 1
done
echo " [OK]"

echo "=== All Services Running Autonomously ==="
wait
