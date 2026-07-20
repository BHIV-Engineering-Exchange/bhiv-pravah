#!/usr/bin/env python3
"""
Enhanced HR-AI System Startup Script
"""

import os
import sys
import time
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    logger.info("Checking system dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'pydantic', 
        'pandas', 'numpy', 'requests', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        logger.info("Installing missing packages...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    logger.info("All dependencies are available")
    return True

def setup_directories():
    """Create required directories"""
    logger.info("Setting up directory structure...")
    
    directories = [
        'data', 'feedback', 'logs', 'backups', 'exports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ready: {directory}")

def initialize_database():
    """Initialize the database system"""
    logger.info("Initializing database system...")
    
    try:
        from app.utils.database import db_manager
        db_manager.init_database()
        
        # Create default admin user if not exists
        admin_user = db_manager.get_user_by_username('admin')
        if not admin_user:
            from app.utils.security import SecurityManager
            db_manager.create_user({
                'username': 'admin',
                'password_hash': SecurityManager.hash_password('admin123'),
                'role': 'admin',
                'permissions': ['read', 'write', 'admin']
            })
            logger.info("Default admin user created (username: admin, password: admin123)")
        
        logger.info("Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def start_fastapi_server():
    """Start the FastAPI backend server"""
    logger.info("Starting FastAPI backend server...")
    
    try:
        import uvicorn
        from app.main import app
        
        # Start server in a separate thread
        def run_server():
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=5000,
                log_level="info"
            )
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(3)
        
        # Test server health
        import requests
        try:
            response = requests.get("http://localhost:5000/health", timeout=10)
            if response.status_code == 200:
                logger.info("FastAPI server started successfully on http://localhost:5000")
                return True
            else:
                logger.error(f"FastAPI server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"FastAPI server connection failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        return False

def start_streamlit_dashboard():
    """Start the Streamlit dashboard"""
    logger.info("Starting Streamlit dashboard...")
    
    try:
        def run_dashboard():
            import streamlit.web.cli as stcli
            sys.argv = ["streamlit", "run", "dashboard/app.py", "--server.port=8501"]
            stcli.main()
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Wait for dashboard to start
        time.sleep(5)
        
        logger.info("Streamlit dashboard started successfully on http://localhost:8501")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start Streamlit dashboard: {e}")
        return False

def run_system_tests():
    """Run basic system tests"""
    logger.info("Running system tests...")
    
    tests_passed = 0
    total_tests = 3
    
    try:
        # Test 1: Database connectivity
        from app.utils.database import db_manager
        stats = db_manager.get_database_stats()
        if isinstance(stats, dict):
            tests_passed += 1
            logger.info("✓ Database connectivity test passed")
        
        # Test 2: API health check
        import requests
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                tests_passed += 1
                logger.info("✓ API health check passed")
        except:
            logger.warning("✗ API health check failed")
        
        # Test 3: File system permissions
        test_file = Path("logs/test_write.tmp")
        test_file.write_text("test")
        test_file.unlink()
        tests_passed += 1
        logger.info("✓ File system permissions test passed")
        
    except Exception as e:
        logger.warning(f"Some system tests failed: {e}")
    
    logger.info(f"System tests completed: {tests_passed}/{total_tests} passed")
    return tests_passed >= 2

def display_system_info():
    """Display system information and access URLs"""
    print("\n" + "="*60)
    print("🚀 HR-AI SYSTEM - PRODUCTION READY")
    print("="*60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🌐 ACCESS POINTS:")
    print("   • Dashboard:     http://localhost:8501")
    print("   • API Docs:      http://localhost:5000/docs")
    print("   • Health Check:  http://localhost:5000/health")
    print("\n🔧 SYSTEM FEATURES:")
    print("   ✓ Multi-channel Communication (Email, WhatsApp, Voice)")
    print("   ✓ SQLite Database with Transactions")
    print("   ✓ Performance Monitoring")
    print("   ✓ Security & Authentication")
    print("   ✓ Error Recovery & Logging")
    print("\n🔐 DEFAULT CREDENTIALS:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   (Change these in production!)")
    print("\n" + "="*60)
    print("System is ready! Press Ctrl+C to stop.")
    print("="*60 + "\n")

def main():
    """Main entry point"""
    logger.info("Starting Enhanced HR-AI System...")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        return False
    
    # Step 2: Setup directories
    setup_directories()
    
    # Step 3: Initialize database
    if not initialize_database():
        logger.error("Database initialization failed")
        return False
    
    # Step 4: Start FastAPI server
    if not start_fastapi_server():
        logger.error("FastAPI server startup failed")
        return False
    
    # Step 5: Start Streamlit dashboard
    if not start_streamlit_dashboard():
        logger.error("Streamlit dashboard startup failed")
        return False
    
    # Step 6: Run system tests
    if not run_system_tests():
        logger.warning("Some system tests failed (system may still be functional)")
    
    # Step 7: Display system information
    display_system_info()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        logger.info("System stopped successfully")
        return True

if __name__ == "__main__":
    main()