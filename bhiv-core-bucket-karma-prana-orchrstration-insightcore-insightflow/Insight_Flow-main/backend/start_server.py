#!/usr/bin/env python3
"""
Simple server startup script with error handling
"""

import uvicorn
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_server():
    """Start the FastAPI server with error handling"""
    
    try:
        logger.info("🚀 Starting InsightFlow API Server...")
        
        # Import and validate configuration
        from app.core.config import settings
        logger.info(f"📋 Environment: {settings.ENVIRONMENT}")
        logger.info(f"📋 Debug Mode: {settings.DEBUG}")
        logger.info(f"📋 STP Enabled: {settings.STP_ENABLED}")
        logger.info(f"📋 Karma Enabled: {settings.KARMA_ENABLED}")
        logger.info(f"📋 Sovereign Core: {settings.USE_SOVEREIGN_CORE}")
        
        # Start server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            log_level="info" if settings.DEBUG else "warning"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        logger.error("💡 Check configuration and dependencies")
        sys.exit(1)

if __name__ == "__main__":
    start_server()