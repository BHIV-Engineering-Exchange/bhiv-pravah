#!/bin/bash

echo "========================================"
echo "Employee Activity Agent - Setup"
echo "========================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    echo ""
    exit 1
fi

echo "[1/5] Node.js found:"
node --version
echo ""

echo "[2/5] Checking npm..."
npm --version
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[3/5] Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "[!] IMPORTANT: Edit .env file and set your backend URL"
    echo "    Open .env and update AGENT_API_BASE_URL"
    echo ""
else
    echo "[3/5] .env file already exists"
    echo ""
fi

echo "[4/5] Installing dependencies..."
echo "This may take a few minutes..."
echo ""
npm install

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to install dependencies!"
    echo ""
    echo "Common fixes for macOS:"
    echo "- Install Xcode Command Line Tools: xcode-select --install"
    echo "- Try running with sudo: sudo npm install"
    echo "- Clear npm cache: npm cache clean --force"
    echo ""
    exit 1
fi

echo ""
echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo "1. Edit .env file with your backend URL"
echo "2. Run the app: npm start"
echo "3. Build for distribution: npm run build:mac"
echo ""
echo "IMPORTANT for macOS:"
echo "- Grant Accessibility permissions when prompted"
echo "- Grant Input Monitoring permissions when prompted"
echo "- These are required for activity tracking"
echo ""
echo "========================================"
echo ""
