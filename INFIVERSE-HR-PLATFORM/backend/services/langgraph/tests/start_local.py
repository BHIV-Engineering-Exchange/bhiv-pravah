#!/usr/bin/env python3
"""
Local development startup script for BHIV LangGraph Service
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Start LangGraph service locally"""
    
    # Check for .env file
    env_file = current_dir / ".env"
    if not env_file.exists():
        print("WARNING: .env file not found. Creating from template...")
        example_file = current_dir / ".env.example"
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print(f"SUCCESS: Created .env from .env.example")
            print("NOTE: Please edit .env with your configuration")
        else:
            print("ERROR: .env.example not found")
            return
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    print("Starting BHIV LangGraph Service...")
    print(f"Working directory: {current_dir}")
    print(f"Service will be available at: http://localhost:9001")
    print(f"Health check: http://localhost:9001/health")
    print(f"API docs: http://localhost:9001/docs")
    
    # Start the service
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()