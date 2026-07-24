"""
BHIV Core ↔ Bucket System Startup Script
Automatically starts both Core and Bucket with proper sequencing
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def check_port(port, service_name):
    """Check if a service is running on the specified port"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_bucket():
    """Start the Bucket service"""
    print("🗄️  Starting BHIV Bucket...")
    bucket_dir = Path("BHIV_Central_Depository-main")
    
    if not bucket_dir.exists():
        print("❌ Bucket directory not found!")
        return None
    
    # Start Bucket
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=bucket_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for Bucket to start
    print("   Waiting for Bucket to initialize...")
    for i in range(30):  # Wait up to 30 seconds
        if check_port(8001, "Bucket"):
            print("✅ Bucket started successfully on http://localhost:8001")
            return process
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")
    
    print("❌ Bucket failed to start within 30 seconds")
    return None

def start_core():
    """Start the Core service"""
    print("🧠 Starting BHIV Core...")
    core_dir = Path("v1-BHIV_CORE-main")
    
    if not core_dir.exists():
        print("❌ Core directory not found!")
        return None
    
    # Start Core
    process = subprocess.Popen(
        [sys.executable, "mcp_bridge.py"],
        cwd=core_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for Core to start
    print("   Waiting for Core to initialize...")
    for i in range(30):  # Wait up to 30 seconds
        if check_port(8002, "Core"):
            print("✅ Core started successfully on http://localhost:8002")
            return process
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")
    
    print("❌ Core failed to start within 30 seconds")
    return None

def test_integration():
    """Test the integration between Core and Bucket"""
    print("🔗 Testing Core ↔ Bucket integration...")
    
    try:
        # Test Bucket health
        bucket_response = requests.get("http://localhost:8001/health", timeout=5)
        if bucket_response.status_code == 200:
            data = bucket_response.json()
            if 'core_integration' in data:
                print("✅ Bucket integration ready")
            else:
                print("⚠️  Bucket running but integration not detected")
        
        # Test Core health
        core_response = requests.get("http://localhost:8002/health", timeout=5)
        if core_response.status_code == 200:
            print("✅ Core integration ready")
        
        # Test a simple task
        task_response = requests.post(
            "http://localhost:8002/handle_task",
            json={
                "agent": "edumentor_agent",
                "input": "Integration test",
                "input_type": "text"
            },
            timeout=10
        )
        
        if task_response.status_code == 200:
            print("✅ Integration test successful!")
            
            # Check if event was received by Bucket
            time.sleep(1)  # Give time for event to be processed
            events_response = requests.get("http://localhost:8001/core/events", timeout=5)
            if events_response.status_code == 200:
                events = events_response.json()
                if events.get("count", 0) > 0:
                    print("✅ Core events successfully received by Bucket")
                else:
                    print("⚠️  No events received by Bucket yet")
        else:
            print("⚠️  Integration test failed")
            
    except Exception as e:
        print(f"⚠️  Integration test error: {e}")

def main():
    """Main startup sequence"""
    print("🚀 BHIV Core ↔ Bucket Integration System")
    print("=" * 50)
    
    # Check if services are already running
    if check_port(8001, "Bucket"):
        print("ℹ️  Bucket already running on port 8001")
        bucket_process = None
    else:
        bucket_process = start_bucket()
        if not bucket_process:
            print("❌ Failed to start Bucket. Exiting.")
            return
    
    if check_port(8002, "Core"):
        print("ℹ️  Core already running on port 8002")
        core_process = None
    else:
        core_process = start_core()
        if not core_process:
            print("❌ Failed to start Core. Exiting.")
            if bucket_process:
                bucket_process.terminate()
            return
    
    print("\n" + "=" * 50)
    print("🎉 System startup complete!")
    print("\n📊 Service URLs:")
    print("   • Bucket API: http://localhost:8001")
    print("   • Core API:   http://localhost:8002")
    print("   • Bucket Health: http://localhost:8001/health")
    print("   • Core Health:   http://localhost:8002/health")
    
    # Test integration
    print("\n" + "=" * 50)
    test_integration()
    
    print("\n" + "=" * 50)
    print("🎯 Ready to use!")
    print("\n📝 Quick test commands:")
    print('   curl -X POST "http://localhost:8002/handle_task" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"agent": "edumentor_agent", "input": "Hello", "input_type": "text"}\'')
    print("\n📊 Monitor integration:")
    print("   curl http://localhost:8000/core/stats")
    print("   curl http://localhost:8000/core/events")
    
    print("\n⚠️  Press Ctrl+C to stop all services")
    
    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        if bucket_process:
            bucket_process.terminate()
            print("✅ Bucket stopped")
        if core_process:
            core_process.terminate()
            print("✅ Core stopped")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()