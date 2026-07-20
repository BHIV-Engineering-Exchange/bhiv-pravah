#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Server Launcher for HR AI System
Run this instead of app.py to use FastAPI
"""

import uvicorn
import sys
import os

# Fix Windows encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting HR AI System with FastAPI...")
    print("API Documentation: http://localhost:5000/docs")
    print("Alternative docs: http://localhost:5000/redoc")
    print("Health check: http://localhost:5000/health")
    
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=5000,
        reload=True,
        log_level="info"
    )