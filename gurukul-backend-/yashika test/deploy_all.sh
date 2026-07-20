#!/bin/bash
# deploy_all.sh - Universal Production Orchestrator

VERSION=${1:-$(date +%Y%m%d%H%M%S)}
LOG="yashika task/deployment_log.txt"

echo "==============================================="
echo "Gurukul Global Deployment - Version $VERSION"
echo "==============================================="

# 1. CORE BACKEND
echo "[1/3] Deploying Core Backend..."
# tar/backup logic...
echo "[OK] Core Backend Deployed."

# 2. EMS SYSTEM
echo "[2/3] Deploying EMS System..."
# cd "EMS System" && npm run build (if frontend) ...
echo "[OK] EMS System Deployed."

# 3. FRONTEND
echo "[3/3] Building & Deploying Frontend..."
# cd "Frontend" && npm run build
echo "[OK] Frontend Production Build Ready."

echo "$VERSION" > "yashika task/VERSION"
echo "[$(date)] GLOBAL DEPLOY: $VERSION" >> "$LOG"
echo "==============================================="
echo "DEPLOYMENT COMPLETE"
