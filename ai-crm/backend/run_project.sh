#!/bin/bash

# AI Agent Logistics Project Startup Script
# This ensures consistent execution every time

echo "🚀 Starting AI Agent Logistics System..."
echo "================================================"

# Navigate to project directory
cd "/Users/rishabh/Desktop/Voice bot/ai-agent_project"

# Check if virtual environment exists
if [ ! -d "venv_new" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create virtual environment first:"
    echo "python3 -m venv venv_new"
    echo "source venv_new/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv_new/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import streamlit, pandas, plotly" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing requirements..."
    pip install -r requirements.txt
fi

# Kill any existing streamlit processes
echo "🧹 Cleaning up existing processes..."
pkill -f streamlit 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start API server in background
echo "🌐 Starting API server on port 8000..."
uvicorn api_app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to start
sleep 3

# Start main dashboard
echo "📊 Starting supplier dashboard on port 8502..."
streamlit run dashboard_with_supplier.py --server.port=8502 &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 3

echo ""
echo "✅ AI Agent Logistics System Started Successfully!"
echo "================================================"
echo "🌐 API Server:        http://localhost:8000"
echo "📊 Supplier Dashboard: http://localhost:8502"
echo ""
echo "📧 Email Notifications: Ready (configure .env for real emails)"
echo "🤖 Autonomous Agents:   Ready (Run Procurement/Delivery buttons)"
echo "📦 Inventory Management: Ready (Product selector in sidebar)"
echo "📞 Supplier Contact:    Ready (Send Alert functionality)"
echo ""
echo "🔄 To stop the system: pkill -f streamlit && pkill -f uvicorn"
echo "================================================"

# Keep script running and show process IDs
echo "📋 Process IDs:"
echo "   API Server PID: $API_PID"
echo "   Dashboard PID: $DASHBOARD_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user interrupt
trap 'echo "🛑 Stopping services..."; kill $API_PID $DASHBOARD_PID 2>/dev/null; exit' INT
wait