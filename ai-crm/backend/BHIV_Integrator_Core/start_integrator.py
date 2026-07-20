#!/usr/bin/env python3
"""
BHIV Integrator Core Startup Script
Consolidates Logistics, CRM, and Task Manager systems
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Start the BHIV Integrator Core"""
    print("🚀 Starting BHIV Integrator Core...")
    print("📡 Consolidating Logistics, CRM, and Task Manager systems")
    print("🔗 Connecting to BHIV Core, UniGuru, and Gurukul pipelines")
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8005))
    
    print(f"🌐 Server will start on {host}:{port}")
    print("📊 Dashboard: http://localhost:8501")
    print("🔗 API: http://localhost:8005")
    print("📖 API Docs: http://localhost:8005/docs")
    
    # Start the FastAPI application
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()