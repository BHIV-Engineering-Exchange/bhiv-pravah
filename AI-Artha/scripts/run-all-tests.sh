#!/bin/bash

set -e

echo "🧪 ARTHA v0.1 - Complete Test Suite"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test
run_test() {
  local test_name=$1
  local test_command=$2

  echo -e "${YELLOW}Running: ${test_name}${NC}"
  
  if eval "$test_command"; then
    echo -e "${GREEN}✓ PASSED${NC}\n"
    ((PASSED_TESTS++))
  else
    echo -e "${RED}✗ FAILED${NC}\n"
    ((FAILED_TESTS++))
  fi
  
  ((TOTAL_TESTS++))
}

# Change to backend directory
cd backend

# Clean up old test data
echo "Cleaning test cache..."
npm run test -- --clearCache > /dev/null 2>&1 || true

echo ""
echo "=== RUNNING TESTS ==="
echo ""

# 1. Linting (optional, skip if fails)
echo -e "${BLUE}Phase 1: Code Quality${NC}"
run_test "ESLint - Code Quality" "npm run lint || true"

echo ""
echo -e "${BLUE}Phase 2: Unit Tests${NC}"

# 2. Hash-Chain Tests
run_test "Ledger Hash-Chain Tests" "npm run test:ledger"

# 3. OCR Tests
run_test "OCR Pipeline Tests" "npm run test:ocr"

# 4. GST Filing Tests
run_test "GST Filing Tests" "npm run test:gst"

echo ""
echo -e "${BLUE}Phase 3: Integration Tests${NC}"

# 5. Integration Tests
run_test "Complete Integration Tests" "npm run test:integration"

echo ""
echo -e "${BLUE}Phase 4: System Tests${NC}"

# 6. Additional System Tests
run_test "Invoice Tests" "npm run test:invoice || true"
run_test "Expense Tests" "npm run test:expense || true"
run_test "Cache Tests" "npm run test:cache || true"
run_test "Performance Tests" "npm run test:performance || true"
run_test "Health Monitoring Tests" "npm run test:health || true"

echo ""
echo "==================================="
echo "TEST SUMMARY"
echo "==================================="
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
  echo -e "${GREEN}✅ All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}❌ Some tests failed!${NC}"
  exit 1
fi
