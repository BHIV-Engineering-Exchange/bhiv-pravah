#!/bin/bash
# Run AI Logistics System with Product Image Support

echo "🚀 Starting AI Logistics System with Product Image Support..."
echo "=========================================================="

# Activate virtual environment
source venv_new/bin/activate

# Install additional dependencies for image support
echo "📦 Installing image processing dependencies..."
pip install Pillow python-multipart

# Create image directories
echo "📁 Creating image directories..."
mkdir -p static/images/products
mkdir -p static/images/thumbnails
mkdir -p static/images/gallery
mkdir -p static/images/temp

# Start API server with image support (port 8002)
echo "🌐 Starting API Server with Image Support on port 8002..."
uvicorn api_app:app --host 0.0.0.0 --port 8002 --reload &
API_PID=$!

# Wait for API to start
sleep 3

# Start Enhanced Dashboard with Supplier Management (port 8503)
echo "📊 Starting Enhanced Dashboard on port 8503..."
streamlit run dashboard_with_supplier.py --server.port 8503 &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 3

# Start Product Catalog Management Dashboard (port 8504)
echo "📦 Starting Product Catalog Management on port 8504..."
streamlit run product_catalog_dashboard.py --server.port 8504 &
CATALOG_PID=$!

# Wait for catalog dashboard to start
sleep 3

# Start Supplier Showcase Portal (port 8505)
echo "🏪 Starting Supplier Showcase Portal on port 8505..."
streamlit run supplier_showcase.py --server.port 8505 &
SHOWCASE_PID=$!

# Wait a moment for all services to start
sleep 5

echo ""
echo "✅ All services started successfully!"
echo "=========================================================="
echo "🌐 API Server (with image upload):     http://localhost:8002"
echo "📖 API Documentation:                  http://localhost:8002/docs"
echo "📊 Enhanced Dashboard:                 http://localhost:8503"
echo "📦 Product Catalog Management:         http://localhost:8504"
echo "🏪 Supplier Showcase Portal:           http://localhost:8505"
echo "🖼️  Static Images:                      http://localhost:8002/static/images/"
echo "=========================================================="
echo ""
echo "🎯 Features Available:"
echo "  • Product image upload and management"
echo "  • Professional supplier showcase"
echo "  • Enhanced inventory with product images"
echo "  • Marketing content management"
echo "  • Image-enabled product catalog"
echo ""
echo "📋 To stop all services: Press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $API_PID $DASHBOARD_PID $CATALOG_PID $SHOWCASE_PID 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user interrupt
echo "Services are running... Press Ctrl+C to stop all services."
wait