#!/usr/bin/env python3
"""
Service Fix Script
Restarts problematic services and applies fixes
"""

import subprocess
import time
import sys
import os

def run_command(command: str, description: str):
    """Run a command and show the result"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} failed with exception: {str(e)}")
        return False

def main():
    """Main fix function"""
    print("🔧 BHIV HR Platform - Service Fix Script")
    print("=" * 50)
    
    # Check if Docker is running
    if not run_command("docker --version", "Checking Docker"):
        print("❌ Docker is not available. Please install Docker first.")
        sys.exit(1)
    
    # Stop all services
    run_command("docker-compose -f docker-compose.production.yml down", "Stopping all services")
    
    # Wait a moment
    print("⏳ Waiting 5 seconds...")
    time.sleep(5)
    
    # Remove any orphaned containers
    run_command("docker-compose -f docker-compose.production.yml down --remove-orphans", "Removing orphaned containers")
    
    # Rebuild LangGraph service (most problematic)
    run_command("docker-compose -f docker-compose.production.yml build langgraph", "Rebuilding LangGraph service")
    
    # Start database first
    run_command("docker-compose -f docker-compose.production.yml up -d db", "Starting database")
    
    # Wait for database
    print("⏳ Waiting 15 seconds for database to initialize...")
    time.sleep(15)
    
    # Start core services
    run_command("docker-compose -f docker-compose.production.yml up -d gateway agent", "Starting Gateway and Agent")
    
    # Wait for core services
    print("⏳ Waiting 10 seconds for core services...")
    time.sleep(10)
    
    # Start LangGraph
    run_command("docker-compose -f docker-compose.production.yml up -d langgraph", "Starting LangGraph service")
    
    # Wait for LangGraph
    print("⏳ Waiting 15 seconds for LangGraph to initialize...")
    time.sleep(15)
    
    # Start portals
    run_command("docker-compose -f docker-compose.production.yml up -d portal client_portal candidate_portal", "Starting all portals")
    
    # Final status check
    print("\n📊 Final Status Check:")
    run_command("docker-compose -f docker-compose.production.yml ps", "Checking service status")
    
    print("\n✅ Service fix completed!")
    print("\n💡 Next steps:")
    print("1. Wait 2-3 minutes for all services to fully start")
    print("2. Run: python test_services.py")
    print("3. Check HR Portal at: http://localhost:8501")
    print("4. Test communication in HR Portal -> Communication Testing")

if __name__ == "__main__":
    main()