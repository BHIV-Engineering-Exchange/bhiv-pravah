#!/usr/bin/env python3
"""
Start Local LangGraph Service for Testing
"""

import subprocess
import sys
import os
import time

def start_local_service():
    """Start local LangGraph service with real credentials"""
    
    print("Starting local LangGraph service...")
    
    # Change to LangGraph directory
    langgraph_dir = "services/langgraph"
    
    try:
        # Start the service
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "9001",
            "--reload"
        ], cwd=langgraph_dir)
        
        print("LangGraph service starting on http://localhost:9001")
        print("Wait 5 seconds for service to start...")
        time.sleep(5)
        
        return process
        
    except Exception as e:
        print(f"Error starting service: {e}")
        return None

if __name__ == "__main__":
    process = start_local_service()
    if process:
        print("Service started! Press Ctrl+C to stop")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("Stopping service...")
            process.terminate()