"""
Core Integrator Deployment Script
==================================
Deploy BHIV Core Integrator independently with all dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title: str):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("CHECKING DEPENDENCIES")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "requests",
        "sqlite3"
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == "sqlite3":
                import sqlite3
            else:
                __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            missing.append(package)
    
    if missing:
        print("\nInstalling missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    return True

def create_env_file():
    """Create environment file for Core Integrator"""
    print_header("CREATING ENVIRONMENT FILE")
    
    env_content = """# Core Integrator Configuration
# Generated for standalone deployment

# Server Configuration
PORT=8001
HOST=0.0.0.0

# Database Configuration (SQLite - Local)
USE_MONGODB=false
DB_PATH=data/context.db

# Optional: MongoDB (Cloud Database)
# USE_MONGODB=true
# MONGODB_CONNECTION_STRING=mongodb+srv://user:password@cluster.mongodb.net
# MONGODB_DATABASE_NAME=bhiv_production

# Optional: Noopur Integration
INTEGRATOR_USE_NOOPUR=false
NOOPUR_BASE_URL=http://localhost:5001

# Security
SSPL_ENABLED=false

# Logging
LOG_LEVEL=INFO
"""
    
    env_path = Path(__file__).parent / ".env.core"
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"  [OK] Created {env_path}")
    print("\n  Environment file created. Edit .env.core to customize:")
    print(f"    - Change PORT if needed")
    print(f"    - Enable MongoDB for cloud database")
    print(f"    - Configure Noopur if using remote service")
    
    return env_path

def create_data_directories():
    """Create required data directories"""
    print_header("CREATING DATA DIRECTORIES")
    
    directories = [
        "data",
        "data/artifacts",
        "logs",
        "logs/bridge"
    ]
    
    for dir_path in directories:
        path = Path(__file__).parent / dir_path
        path.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {dir_path}/")
    
    return True

def test_core_integrator():
    """Test if Core Integrator can start"""
    print_header("TESTING CORE INTEGRATOR")
    
    print("\n  Attempting to start Core Integrator...")
    print("  This will test if all imports work correctly.\n")
    
    try:
        # Test imports
        print("  Testing imports...")
        from fastapi import FastAPI
        from src.core.gateway import Gateway
        from src.db.memory import ContextMemory
        from config.config import DB_PATH
        print("  [OK] All imports successful\n")
        
        # Test database
        print("  Testing database...")
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        print(f"  [OK] Database ready at {DB_PATH}\n")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def start_server():
    """Start the Core Integrator server"""
    print_header("STARTING CORE INTEGRATOR")
    
    port = os.getenv("PORT", "8001")
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n  Starting server on {host}:{port}")
    print("  Press Ctrl+C to stop\n")
    print("="*70)
    print("\n  ENDPOINTS:")
    print(f"    Root:            http://localhost:{port}/")
    print(f"    Health:          http://localhost:{port}/system/health")
    print(f"    Core (POST):     http://localhost:{port}/core")
    print(f"    Diagnostics:     http://localhost:{port}/system/diagnostics")
    print(f"    API Docs:        http://localhost:{port}/docs")
    print("\n  TEST COMMANDS:")
    print(f"    curl http://localhost:{port}/")
    print(f"    curl http://localhost:{port}/system/health")
    print("\n" + "="*70 + "\n")
    
    # Start server
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", port])

def main():
    print("\n" + "="*70)
    print("  CORE INTEGRATOR - STANDALONE DEPLOYMENT")
    print("="*70)
    
    print("\nThis script will help you deploy Core Integrator independently.")
    print("The service will run on its own and can be accessed via HTTP endpoints.\n")
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n[ERROR] Dependency check failed")
        return
    
    # Step 2: Create environment file
    env_path = create_env_file()
    
    # Step 3: Create directories
    if not create_data_directories():
        print("\n[ERROR] Failed to create directories")
        return
    
    # Step 4: Test
    if not test_core_integrator():
        print("\n[ERROR] Core Integrator test failed")
        return
    
    # Step 5: Ask to start
    print_header("DEPLOYMENT READY")
    print("\n  Core Integrator is ready to deploy!")
    print(f"  Environment file: {env_path}")
    print("\n  Options:")
    print("    1. Start now")
    print("    2. Start manually later")
    print("    3. Exit")
    
    choice = input("\n  Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        # Load environment
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        start_server()
    elif choice == "2":
        print("\n  To start manually:")
        print(f"    python main.py")
        print("    OR")
        print(f"    uvicorn main:app --host 0.0.0.0 --port 8001")
    else:
        print("\n  Deployment prepared. Run when ready!")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
