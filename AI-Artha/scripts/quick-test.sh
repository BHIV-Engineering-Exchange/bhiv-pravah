#!/bin/bash

# Quick test script - runs only critical tests
set -e

echo "⚡ ARTHA - Quick Test Suite"
echo "==========================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd backend

echo -e "${YELLOW}Running critical tests...${NC}"
echo ""

# Run only the most important tests
echo "1. Hash-Chain Tests..."
npm run test:ledger --silent

echo "2. Integration Tests..."
npm run test:integration --silent

echo ""
echo -e "${GREEN}✅ Quick tests passed!${NC}"
