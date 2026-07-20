#!/usr/bin/env python3
"""
HR AI System Startup Script
Validates system integrity before starting the application
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('system.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def validate_system():
    """Validate system requirements and data integrity"""
    logger = setup_logging()
    
    try:
        # Import and run data validation
        from app.utils.data_validator import DataValidator
        
        logger.info("Starting HR AI System validation...")
        
        # Validate data files
        validation_result = DataValidator.validate_data_files()
        
        if validation_result["status"] == "error":
            logger.error("Data validation failed:")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
            return False
        
        if validation_result["created_files"]:
            logger.info("Created missing files:")
            for file_path in validation_result["created_files"]:
                logger.info(f"  - {file_path}")
        
        # Check system status
        system_status = DataValidator.get_system_status()
        
        # Check permissions
        failed_permissions = [dir_path for dir_path, has_permission in system_status["permissions"].items() if not has_permission]
        if failed_permissions:
            logger.warning("Permission issues detected:")
            for dir_path in failed_permissions:
                logger.warning(f"  - No write permission for: {dir_path}")
        
        logger.info("System validation completed successfully")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Please ensure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"System validation failed: {e}")
        return False

def start_dashboard():
    """Start the Streamlit dashboard"""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting HR AI System Dashboard...")
        logger.info("Dashboard URL: http://localhost:8501")
        
        # Start Streamlit in a separate process
        import subprocess
        subprocess.Popen(
            ["streamlit", "run", "dashboard/app.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            shell=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        return False

def start_fastapi():
    """Start the FastAPI server"""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        
        logger.info("Starting HR AI System FastAPI server...")
        logger.info("API Documentation: http://localhost:5000/docs")
        logger.info("Health Check: http://localhost:5000/health")
        logger.info("System Status: http://localhost:5000/system/status")
        logger.info("-" * 50)
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=5000,
            reload=False,
            reload_excludes=["logs/*", "data/*", "backups/*", "system.log", "*.log", "*.csv", "*.json"],
            log_level="info"
        )
        
    except ImportError:
        logger.error("uvicorn not installed. Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False

def main():
    """Main startup function"""
    print("=" * 60)
    print("HR AI System - Startup Validation")
    print("=" * 60)
    
    # Validate system
    if not validate_system():
        print("\nSystem validation failed. Please check the logs and fix the issues.")
        sys.exit(1)
    
    print("\nSystem validation passed. Starting server...")
    
    # Start Dashboard
    if not start_dashboard():
        print("\nFailed to start dashboard. Please check the logs.")
    
    # Start FastAPI server
    if not start_fastapi():
        print("\nFailed to start server. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()