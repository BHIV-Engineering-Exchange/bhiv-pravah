#!/usr/bin/env python3
"""
Production startup script for AI Content Platform.
Validates configuration, initializes database, and starts the server.
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

def validate_environment():
    """Validate required environment variables."""
    issues = []
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        issues.append("MONGO_URI not set")
    
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        issues.append("JWT_SECRET_KEY not set (will use fallback)")
    
    return issues

def initialize_database():
    """Initialize MongoDB indexes."""
    try:
        from core.database import create_db_and_tables
        create_db_and_tables()
        logger.info("MongoDB indexes initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
        return False

def create_directories():
    """Create required directories."""
    dirs = ["uploads", "logs", "bucket/scripts", "bucket/storyboards", 
            "bucket/videos", "bucket/logs", "bucket/ratings", "bucket/tmp", "bucket/uploads"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    """Main startup procedure."""
    logger.info("AI Content Platform starting up...")
    logger.info("Phase IV: TANTRA Platform Integration active")
    
    # Step 1: Validate environment
    issues = validate_environment()
    if issues:
        for issue in issues:
            logger.warning(f"Config warning: {issue}")
    
    # Step 2: Create directories
    create_directories()
    logger.info("Directories created/verified")
    
    # Step 3: Initialize database
    db_ok = initialize_database()
    if db_ok:
        logger.info("Database ready")
    else:
        logger.warning("Database not available - running in degraded mode")
    
    # Step 4: Start server
    import uvicorn
    logger.info("Starting uvicorn server on port 9000...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        log_level="info",
        access_log=True,
        reload=False
    )

if __name__ == "__main__":
    main()
