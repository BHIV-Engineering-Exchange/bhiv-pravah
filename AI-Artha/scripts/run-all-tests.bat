@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 🧪 ARTHA v0.1 - Complete Test Suite
echo ========================================
echo.

set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

cd backend

echo Cleaning test cache...
call npm run test -- --clearCache >nul 2>&1

echo.
echo === RUNNING TESTS ===
echo.

echo Phase 1: Code Quality
echo.

echo Running: ESLint - Code Quality
call npm run lint >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Phase 2: Unit Tests
echo.

echo Running: Ledger Hash-Chain Tests
call npm run test:ledger
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: OCR Pipeline Tests
call npm run test:ocr
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: GST Filing Tests
call npm run test:gst
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Phase 3: Integration Tests
echo.

echo Running: Complete Integration Tests
call npm run test:integration
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Phase 4: System Tests
echo.

echo Running: Invoice Tests
call npm run test:invoice >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: Expense Tests
call npm run test:expense >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: Cache Tests
call npm run test:cache >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: Performance Tests
call npm run test:performance >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo Running: Health Monitoring Tests
call npm run test:health >nul 2>&1
if %errorlevel% equ 0 (
    echo [32m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [31m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
set /a TOTAL_TESTS+=1
echo.

echo ===================================
echo TEST SUMMARY
echo ===================================
echo Total Tests: %TOTAL_TESTS%
echo [32mPassed: %PASSED_TESTS%[0m
echo [31mFailed: %FAILED_TESTS%[0m
echo.

if %FAILED_TESTS% equ 0 (
    echo [32m✅ All tests passed![0m
    exit /b 0
) else (
    echo [31m❌ Some tests failed![0m
    exit /b 1
)
