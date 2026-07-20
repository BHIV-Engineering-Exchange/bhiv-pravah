#!/usr/bin/env python3
"""
Unified Dashboard Launcher
Starts the single unified dashboard that replaces all separate dashboards
"""

import subprocess
import sys
import os
from datetime import datetime

def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("🚀 AI AGENT UNIFIED DASHBOARD LAUNCHER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Launching unified dashboard that combines all functionality...")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("[CHECK] Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly',
        'sqlalchemy',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[ERROR] {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n[WARN] Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("[OK] All dependencies satisfied")
    return True

def initialize_database():
    """Initialize the database"""
    print("\n[DB] Initializing database...")
    
    try:
        from database.models import init_database
        init_database()
        print("[OK] Database initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False

def start_unified_dashboard():
    """Start the unified dashboard"""
    print("\n[DASH] Starting Unified Dashboard...")
    
    try:
        # Start Streamlit dashboard on port 8500
        process = subprocess.Popen([
            'streamlit', 'run', 'unified_dashboard.py',
            '--server.port=8500',
            '--server.headless=false',
            '--browser.gatherUsageStats=false'
        ])
        
        print("[OK] Unified Dashboard started successfully!")
        print()
        print("=" * 80)
        print("🎯 UNIFIED DASHBOARD ACCESS")
        print("=" * 80)
        print("🚀 Main Dashboard: http://localhost:8500")
        print()
        print("📋 Features Available:")
        print("   ✅ CRM Management (Accounts, Leads, Opportunities)")
        print("   ✅ Logistics & Inventory Management")
        print("   ✅ Supplier Management & Showcase")
        print("   ✅ Product Catalog with Image Management")
        print("   ✅ AI Agent Controls & Monitoring")
        print("   ✅ Analytics & Reporting")
        print("   ✅ Natural Language Queries")
        print()
        print("🧭 Navigation:")
        print("   • Use the sidebar to switch between different modules")
        print("   • All functionality from 5 separate dashboards now in one place")
        print("   • No need to visit multiple ports anymore!")
        print()
        print("=" * 80)
        print("Press Ctrl+C to stop the dashboard")
        print("=" * 80)
        
        # Wait for process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down unified dashboard...")
        process.terminate()
        print("[OK] Dashboard stopped")
    except Exception as e:
        print(f"[ERROR] Failed to start unified dashboard: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("[ERROR] Dependency check failed. Please install missing packages.")
        return False
    
    # Initialize database
    if not initialize_database():
        print("[ERROR] Database initialization failed.")
        return False
    
    # Start unified dashboard
    if not start_unified_dashboard():
        print("[ERROR] Failed to start unified dashboard.")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Launcher failed: {e}")
        sys.exit(1)