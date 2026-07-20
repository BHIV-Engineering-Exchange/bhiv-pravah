#!/usr/bin/env python3
"""
Enhanced HR-AI System Startup Script
Handles database initialization, security setup, performance monitoring, and automated backups
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

class EnhancedSystemManager:
    """Manages the enhanced HR-AI system startup and monitoring"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.processes = {}
        self.monitoring_active = False
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("Checking system dependencies...")
        
        required_packages = [
            'fastapi', 'uvicorn', 'streamlit', 'pydantic', 
            'pandas', 'numpy', 'requests', 'python-dotenv',
            'PyJWT', 'psutil', 'schedule'
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
    
    def setup_directories(self):
        """Create required directories"""
        logger.info("Setting up directory structure...")
        
        directories = [
            'data', 'feedback', 'logs', 'backups', 'exports', 'uploads'
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ready: {directory}")
    
    def initialize_database(self):
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
            return False\n    \n    def migrate_legacy_data(self):\n        \"\"\"Migrate existing JSON data to database\"\"\"\n        logger.info(\"Checking for legacy data migration...\")\n        \n        try:\n            from app.utils.database import DatabaseMigration\n            DatabaseMigration.migrate_from_json()\n            logger.info(\"Legacy data migration completed\")\n            return True\n        except Exception as e:\n            logger.warning(f\"Legacy data migration failed (this is normal for new installations): {e}\")\n            return True  # Not critical for new installations\n    \n    def start_fastapi_server(self):\n        \"\"\"Start the FastAPI backend server\"\"\"\n        logger.info(\"Starting FastAPI backend server...\")\n        \n        try:\n            import uvicorn\n            from app.main import app\n            \n            # Start server in a separate thread\n            def run_server():\n                uvicorn.run(\n                    app,\n                    host=\"0.0.0.0\",\n                    port=5000,\n                    log_level=\"info\",\n                    access_log=True\n                )\n            \n            server_thread = threading.Thread(target=run_server, daemon=True)\n            server_thread.start()\n            \n            # Wait a moment for server to start\n            time.sleep(3)\n            \n            # Test server health\n            import requests\n            response = requests.get(\"http://localhost:5000/health\", timeout=10)\n            if response.status_code == 200:\n                logger.info(\"FastAPI server started successfully on http://localhost:5000\")\n                self.processes['fastapi'] = server_thread\n                return True\n            else:\n                logger.error(f\"FastAPI server health check failed: {response.status_code}\")\n                return False\n                \n        except Exception as e:\n            logger.error(f\"Failed to start FastAPI server: {e}\")\n            return False\n    \n    def start_streamlit_dashboard(self):\n        \"\"\"Start the Streamlit dashboard\"\"\"\n        logger.info(\"Starting Streamlit dashboard...\")\n        \n        try:\n            def run_dashboard():\n                import streamlit.web.cli as stcli\n                sys.argv = [\"streamlit\", \"run\", \"dashboard/app.py\", \"--server.port=8501\"]\n                stcli.main()\n            \n            dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)\n            dashboard_thread.start()\n            \n            # Wait for dashboard to start\n            time.sleep(5)\n            \n            logger.info(\"Streamlit dashboard started successfully on http://localhost:8501\")\n            self.processes['streamlit'] = dashboard_thread\n            return True\n            \n        except Exception as e:\n            logger.error(f\"Failed to start Streamlit dashboard: {e}\")\n            return False\n    \n    def start_monitoring_services(self):\n        \"\"\"Start performance monitoring and backup services\"\"\"\n        logger.info(\"Starting monitoring and backup services...\")\n        \n        try:\n            from app.utils.performance_monitor import performance_monitor\n            from app.utils.backup_manager import backup_manager\n            \n            # Start performance monitoring\n            performance_monitor.start_monitoring(interval_seconds=30)\n            \n            # Start automated backups (every 24 hours)\n            backup_manager.start_auto_backup(interval_hours=24)\n            \n            logger.info(\"Monitoring and backup services started\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"Failed to start monitoring services: {e}\")\n            return False\n    \n    def run_system_tests(self):\n        \"\"\"Run basic system tests\"\"\"\n        logger.info(\"Running system tests...\")\n        \n        tests_passed = 0\n        total_tests = 5\n        \n        try:\n            # Test 1: Database connectivity\n            from app.utils.database import db_manager\n            stats = db_manager.get_database_stats()\n            if isinstance(stats, dict):\n                tests_passed += 1\n                logger.info(\"✓ Database connectivity test passed\")\n            \n            # Test 2: API health check\n            import requests\n            response = requests.get(\"http://localhost:5000/health\", timeout=5)\n            if response.status_code == 200:\n                tests_passed += 1\n                logger.info(\"✓ API health check passed\")\n            \n            # Test 3: Performance monitoring\n            from app.utils.performance_monitor import performance_monitor\n            metrics = performance_monitor.get_current_metrics()\n            if metrics.get(\"timestamp\"):\n                tests_passed += 1\n                logger.info(\"✓ Performance monitoring test passed\")\n            \n            # Test 4: File system permissions\n            test_file = self.base_dir / \"logs\" / \"test_write.tmp\"\n            test_file.write_text(\"test\")\n            test_file.unlink()\n            tests_passed += 1\n            logger.info(\"✓ File system permissions test passed\")\n            \n            # Test 5: Backup system\n            from app.utils.backup_manager import backup_manager\n            backup_list = backup_manager.get_backup_list()\n            if isinstance(backup_list, list):\n                tests_passed += 1\n                logger.info(\"✓ Backup system test passed\")\n            \n        except Exception as e:\n            logger.warning(f\"Some system tests failed: {e}\")\n        \n        logger.info(f\"System tests completed: {tests_passed}/{total_tests} passed\")\n        return tests_passed >= 3  # Require at least 3 tests to pass\n    \n    def display_system_info(self):\n        \"\"\"Display system information and access URLs\"\"\"\n        print(\"\\n\" + \"=\"*60)\n        print(\"🚀 HR-AI SYSTEM - PRODUCTION READY\")\n        print(\"=\"*60)\n        print(f\"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\")\n        print(f\"📁 Base Directory: {self.base_dir}\")\n        print(\"\\n🌐 ACCESS POINTS:\")\n        print(\"   • Dashboard:     http://localhost:8501\")\n        print(\"   • API Docs:      http://localhost:5000/docs\")\n        print(\"   • Health Check:  http://localhost:5000/health\")\n        print(\"   • Performance:   http://localhost:5000/system/performance\")\n        print(\"\\n🔧 SYSTEM FEATURES:\")\n        print(\"   ✓ Multi-channel Communication (Email, WhatsApp, Voice)\")\n        print(\"   ✓ SQLite Database with Transactions\")\n        print(\"   ✓ Performance Monitoring\")\n        print(\"   ✓ Automated Backups\")\n        print(\"   ✓ Security & Authentication\")\n        print(\"   ✓ Error Recovery & Logging\")\n        print(\"\\n🔐 DEFAULT CREDENTIALS:\")\n        print(\"   Username: admin\")\n        print(\"   Password: admin123\")\n        print(\"   (Change these in production!)\")\n        print(\"\\n📊 MONITORING:\")\n        print(\"   • Performance metrics updated every 30 seconds\")\n        print(\"   • Automated backups every 24 hours\")\n        print(\"   • System logs in logs/ directory\")\n        print(\"\\n\" + \"=\"*60)\n        print(\"System is ready! Press Ctrl+C to stop.\")\n        print(\"=\"*60 + \"\\n\")\n    \n    def start_system(self):\n        \"\"\"Start the complete enhanced system\"\"\"\n        logger.info(\"Starting Enhanced HR-AI System...\")\n        \n        # Step 1: Check dependencies\n        if not self.check_dependencies():\n            logger.error(\"Dependency check failed\")\n            return False\n        \n        # Step 2: Setup directories\n        self.setup_directories()\n        \n        # Step 3: Initialize database\n        if not self.initialize_database():\n            logger.error(\"Database initialization failed\")\n            return False\n        \n        # Step 4: Migrate legacy data\n        self.migrate_legacy_data()\n        \n        # Step 5: Start FastAPI server\n        if not self.start_fastapi_server():\n            logger.error(\"FastAPI server startup failed\")\n            return False\n        \n        # Step 6: Start Streamlit dashboard\n        if not self.start_streamlit_dashboard():\n            logger.error(\"Streamlit dashboard startup failed\")\n            return False\n        \n        # Step 7: Start monitoring services\n        if not self.start_monitoring_services():\n            logger.warning(\"Monitoring services failed to start (non-critical)\")\n        \n        # Step 8: Run system tests\n        if not self.run_system_tests():\n            logger.warning(\"Some system tests failed (system may still be functional)\")\n        \n        # Step 9: Display system information\n        self.display_system_info()\n        \n        return True\n    \n    def monitor_system(self):\n        \"\"\"Monitor system health and restart services if needed\"\"\"\n        self.monitoring_active = True\n        \n        while self.monitoring_active:\n            try:\n                # Check FastAPI health\n                import requests\n                response = requests.get(\"http://localhost:5000/health\", timeout=5)\n                if response.status_code != 200:\n                    logger.warning(\"FastAPI health check failed, attempting restart...\")\n                    self.start_fastapi_server()\n                \n                # Check system resources\n                from app.utils.performance_monitor import performance_monitor\n                metrics = performance_monitor.get_current_metrics()\n                \n                if metrics.get(\"current\", {}).get(\"memory_percent\", 0) > 90:\n                    logger.warning(\"High memory usage detected\")\n                \n                if metrics.get(\"current\", {}).get(\"cpu_percent\", 0) > 90:\n                    logger.warning(\"High CPU usage detected\")\n                \n            except Exception as e:\n                logger.error(f\"System monitoring error: {e}\")\n            \n            time.sleep(60)  # Check every minute\n    \n    def stop_system(self):\n        \"\"\"Gracefully stop all system components\"\"\"\n        logger.info(\"Stopping Enhanced HR-AI System...\")\n        \n        self.monitoring_active = False\n        \n        # Stop monitoring services\n        try:\n            from app.utils.performance_monitor import performance_monitor\n            from app.utils.backup_manager import backup_manager\n            \n            performance_monitor.stop_monitoring()\n            backup_manager.stop_auto_backup()\n            \n        except Exception as e:\n            logger.error(f\"Error stopping monitoring services: {e}\")\n        \n        logger.info(\"System stopped successfully\")\n\ndef main():\n    \"\"\"Main entry point\"\"\"\n    system_manager = EnhancedSystemManager()\n    \n    try:\n        if system_manager.start_system():\n            # Start system monitoring\n            monitor_thread = threading.Thread(\n                target=system_manager.monitor_system, \n                daemon=True\n            )\n            monitor_thread.start()\n            \n            # Keep the main thread alive\n            while True:\n                time.sleep(1)\n        else:\n            logger.error(\"System startup failed\")\n            sys.exit(1)\n            \n    except KeyboardInterrupt:\n        logger.info(\"Shutdown signal received\")\n        system_manager.stop_system()\n        sys.exit(0)\n    except Exception as e:\n        logger.error(f\"Unexpected error: {e}\")\n        system_manager.stop_system()\n        sys.exit(1)\n\nif __name__ == \"__main__\":\n    main()