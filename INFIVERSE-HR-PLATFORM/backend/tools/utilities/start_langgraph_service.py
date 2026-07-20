#!/usr/bin/env python3
"""
Start LangGraph Service for Testing
"""

import subprocess
import sys
import os
import time

def start_service():
    """Start LangGraph service on localhost:9001"""
    
    print("Starting LangGraph service on localhost:9001...")
    
    # Change to LangGraph directory
    os.chdir("services/langgraph")
    
    # Start uvicorn server
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9001"]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Service starting... Wait 10 seconds for initialization")
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is None:
            print("LangGraph service is running on http://localhost:9001")
            print("You can now run: python test_all_langgraph_endpoints.py")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"Service failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Error starting service: {e}")
        return None

if __name__ == "__main__":
    process = start_service()
    if process:
        try:
            # Keep service running
            input("Press Enter to stop the service...")
        except KeyboardInterrupt:
            pass
        finally:
            print("Stopping service...")
            process.terminate()
            process.wait()