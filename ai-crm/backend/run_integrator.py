#!/usr/bin/env python3
"""
Run BHIV Integrator Core on port 8006
"""

import os
import sys
sys.path.append('BHIV_Integrator_Core')

from BHIV_Integrator_Core.simple_app import app
import uvicorn

if __name__ == "__main__":
    print("Starting BHIV Integrator Core on port 8006...")
    print("API Gateway: http://localhost:8006")
    print("API Documentation: http://localhost:8006/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8006)