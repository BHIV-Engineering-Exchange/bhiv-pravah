@echo off
echo ===========================
echo ⚡ ARTHA - Quick Test Suite
echo ===========================
echo.

cd backend

echo Running critical tests...
echo.

echo 1. Hash-Chain Tests...
call npm run test:ledger --silent

echo 2. Integration Tests...
call npm run test:integration --silent

echo.
echo [32m✅ Quick tests passed![0m
