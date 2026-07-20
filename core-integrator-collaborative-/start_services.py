"""
BHIV Microservices Deployment Script
=====================================
Starts all microservices in correct dependency order
"""

import sys
import subprocess
import time
import requests
import os
from pathlib import Path

# Service configuration
SERVICES = [
    {
        "name": "BHIV Bucket",
        "port": 8005,
        "script": "bhiv_bucket.py",
        "health_url": "http://127.0.0.1:8005/bucket/stats"
    },
    {
        "name": "Creator Core",
        "port": 8000,
        "script": "creator-core/Core-Integrator-Sprint-1.1/main.py",
        "health_url": "http://127.0.0.1:8000/",
        "env_file": "creator-core/Core-Integrator-Sprint-1.1/.env.local"
    },
    {
        "name": "BHIV Core",
        "port": 8001,
        "script": "main.py",
        "health_url": "http://127.0.0.1:8001/"
    },
    {
        "name": "Integration Bridge",
        "port": 8004,
        "script": "integration_bridge_v2.py",
        "health_url": "http://127.0.0.1:8004/pipeline/health",
        "env_file": ".env.integration_bridge"
    }
]

processes = []

def load_env_file(env_path: str):
    """Load environment variables from file"""
    path = Path(__file__).parent / env_path
    if path.exists():
        print(f"   Loading env: {env_path}")
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lstrip('\ufeff')
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

def check_health(health_url: str, timeout: int = 10) -> bool:
    """Check if service is healthy"""
    try:
        response = requests.get(health_url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_service(service: dict) -> bool:
    """Start a single service"""
    print(f"\n[START] {service['name']} (Port {service['port']})")
    
    # Load env file if specified
    if 'env_file' in service:
        load_env_file(service['env_file'])
    
    # Set port
    os.environ['PORT'] = str(service['port'])
    
    # Start process
    script_path = Path(__file__).parent / service['script']
    if not script_path.exists():
        print(f"   [ERROR] Script not found: {script_path}")
        return False
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        processes.append(process)
        
        print(f"   Process started (PID: {process.pid})")
        
        # Wait for service to become healthy
        print(f"   Waiting for health check...", end=" ")
        for i in range(15):  # Wait up to 15 seconds
            time.sleep(1)
            if check_health(service['health_url'], timeout=2):
                print("[OK] Healthy!")
                return True
            print(".", end="", flush=True)
        
        print("\n   [WARNING] Health check timeout")
        
        # Check if process crashed
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"   [ERROR] Process crashed!")
            if stderr:
                print(f"   STDERR: {stderr[:500]}")
            return False
        
        return True  # Service started even if health check timed out
        
    except Exception as e:
        print(f"   [ERROR] Failed to start: {str(e)}")
        return False

def stop_all():
    """Stop all running services"""
    print("\n" + "="*70)
    print("STOPPING ALL SERVICES")
    print("="*70)
    
    for i, process in enumerate(processes):
        if process.poll() is None:
            print(f"Stopping service {i+1}...", end=" ")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("[OK]")
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                print("[KILLED]")
            except Exception as e:
                print(f"[ERROR] {str(e)}")
    
    print("\nAll services stopped")

def main():
    print("\n" + "="*70)
    print("BHIV MICROSERVICES DEPLOYMENT")
    print("="*70)
    print("\nStarting services in dependency order...")
    
    # Check if any services are already running
    print("\n[CHECK] Checking for existing services...")
    running = []
    for service in SERVICES:
        if check_health(service['health_url'], timeout=2):
            running.append(service['name'])
            print(f"   {service['name']}: Already running")
    
    if running:
        print(f"\n[WARNING] {len(running)} services are already running:")
        for name in running:
            print(f"   - {name}")
        print("\nProceeding with remaining services...")
    
    # Start services
    success_count = 0
    for service in SERVICES:
        if service['name'] not in running:
            if start_service(service):
                success_count += 1
    
    # Final status
    print("\n" + "="*70)
    print("DEPLOYMENT COMPLETE")
    print("="*70)
    
    print("\nService URLs:")
    for service in SERVICES:
        url = service['health_url'].rsplit('/', 1)[0] if '/' in service['health_url'] else service['health_url']
        status = "[OK]" if check_health(service['health_url'], timeout=2) else "[X]"
        print(f"  {status} {service['name']:20s} -> {url}")
    
    print("\n" + "="*70)
    
    # Monitor loop
    print("\nServices are running. Press Ctrl+C to stop all services.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping services...")
        stop_all()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        stop_all()
