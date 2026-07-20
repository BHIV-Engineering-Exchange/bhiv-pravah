#!/bin/bash
# Complete Dashboard Launcher - Shell Version
# Starts all CRM, Product Image, and Supplier Management dashboards

echo "🚀 Starting Complete AI Agent Dashboard System..."
echo "=================================================="

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

# Install/check required packages
echo "🔍 Checking dependencies..."
pip install -r requirements.txt --quiet

# Create image directories
echo "📁 Creating image directories..."
mkdir -p static/images/products
mkdir -p static/images/thumbnails
mkdir -p static/images/gallery
mkdir -p static/images/temp

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f streamlit 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f "python.*crm_api" 2>/dev/null || true
pkill -f "python.*api_app" 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo ""
echo "🌐 Starting API servers..."

# Start CRM API server (port 8001)
echo "   Starting CRM API on port 8001..."
python3 crm_api.py &
CRM_API_PID=$!
sleep 2

# Start Main API server with image support (port 8000)
echo "   Starting Main API with image support on port 8000..."
uvicorn api_app:app --host 0.0.0.0 --port 8000 --reload &
MAIN_API_PID=$!
sleep 2

echo ""
echo "📊 Starting all dashboards..."

# Start CRM Dashboard (port 8501)
echo "   Starting CRM Dashboard on port 8501..."
streamlit run crm_dashboard.py --server.port=8501 --server.headless=true &
CRM_DASHBOARD_PID=$!
sleep 3

# Start Main Dashboard (port 8502)
echo "   Starting Main Dashboard on port 8502..."
streamlit run dashboard_app.py --server.port=8502 --server.headless=true &
MAIN_DASHBOARD_PID=$!
sleep 3

# Start Enhanced Supplier Dashboard (port 8503)
echo "   Starting Enhanced Supplier Dashboard on port 8503..."
streamlit run dashboard_with_supplier.py --server.port=8503 --server.headless=true &
SUPPLIER_DASHBOARD_PID=$!
sleep 3

# Start Product Catalog Management (port 8504)
echo "   Starting Product Catalog Management on port 8504..."
streamlit run product_catalog_dashboard.py --server.port=8504 --server.headless=true &
CATALOG_PID=$!
sleep 3

# Start Supplier Showcase Portal (port 8505)
echo "   Starting Supplier Showcase Portal on port 8505..."
streamlit run supplier_showcase.py --server.port=8505 --server.headless=true &
SHOWCASE_PID=$!

# Wait for all services to start
sleep 5

echo ""
echo "✅ ALL DASHBOARD SERVICES STARTED SUCCESSFULLY!"
echo "=================================================="
echo ""
echo "🌐 API Endpoints:"
echo "   • CRM API:                http://localhost:8001"
echo "   • CRM API Docs:           http://localhost:8001/docs"
echo "   • Main API (with Images): http://localhost:8000"
echo "   • Main API Docs:          http://localhost:8000/docs"
echo ""
echo "📊 All Dashboards:"
echo "   • CRM Dashboard:          http://localhost:8501"
echo "   • Main Dashboard:         http://localhost:8502"
echo "   • Enhanced Supplier:      http://localhost:8503"
echo "   • Product Catalog:        http://localhost:8504"
echo "   • Supplier Showcase:      http://localhost:8505"
echo ""
echo "🎯 QUICK ACCESS GUIDE:"
echo "   👤 CRM & Customer Management:  → http://localhost:8501"
echo "   📦 Product & Inventory:        → http://localhost:8504"
echo "   🏪 Supplier Management:        → http://localhost:8503"
echo "   🤖 AI Natural Language:        → http://localhost:8501 (NLP section)"
echo ""
echo "🎨 Features Available:"
echo "   ✅ Complete CRM System"
echo "   ✅ Product Image Management"
echo "   ✅ AI-Powered Queries"
echo "   ✅ Supplier Showcase"
echo "   ✅ Inventory Management"
echo "   ✅ Analytics & Reports"
echo ""
echo "📋 Process IDs:"
echo "   CRM API: $CRM_API_PID"
echo "   Main API: $MAIN_API_PID"
echo "   CRM Dashboard: $CRM_DASHBOARD_PID"
echo "   Main Dashboard: $MAIN_DASHBOARD_PID"
echo "   Supplier Dashboard: $SUPPLIER_DASHBOARD_PID"
echo "   Product Catalog: $CATALOG_PID"
echo "   Supplier Showcase: $SHOWCASE_PID"
echo ""
echo "🔄 All services are running. Press Ctrl+C to stop all services."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all dashboard services..."
    kill $CRM_API_PID $MAIN_API_PID $CRM_DASHBOARD_PID $MAIN_DASHBOARD_PID $SUPPLIER_DASHBOARD_PID $CATALOG_PID $SHOWCASE_PID 2>/dev/null
    
    # Also kill by process name as backup
    pkill -f streamlit 2>/dev/null || true
    pkill -f uvicorn 2>/dev/null || true
    pkill -f "python.*crm_api" 2>/dev/null || true
    
    echo "✅ All dashboard services stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user interrupt
echo "Services are running... Press Ctrl+C to stop all services."
wait