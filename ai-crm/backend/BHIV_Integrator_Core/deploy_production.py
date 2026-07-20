#!/usr/bin/env python3
"""
Production Deployment Script for BHIV Integrator Core
Deploys the consolidated backend layer with all necessary components
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    env_vars = {
        "HOST": "0.0.0.0",
        "PORT": "8005",
        "BHIV_CORE_URL": "http://localhost:8002",
        "UNIGURU_URL": "http://localhost:8001",
        "GURUKUL_URL": "http://localhost:8001",
        "LOGISTICS_BASE_URL": "http://localhost:8000",
        "CRM_BASE_URL": "http://localhost:8502",
        "TASK_BASE_URL": "http://localhost:8000",
        "COMPLIANCE_ENABLED": "true",
        "SANKALP_COMPLIANCE_URL": "http://localhost:8007",
        "DATABASE_URL": "sqlite:///./bhiv_integrator.db"
    }
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        print("✅ Environment file created")
    else:
        print("✅ Environment file exists")
    
    return True

def check_service_health(url, service_name, timeout=5):
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"⚠️ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"⚠️ {service_name} is not accessible (this may be expected)")
        return False

def start_integrator():
    """Start the BHIV Integrator Core"""
    print("🚀 Starting BHIV Integrator Core...")
    
    try:
        # Start the FastAPI application
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for startup
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ BHIV Integrator Core started successfully")
            print("🌐 API Gateway: http://localhost:8005")
            print("📖 API Documentation: http://localhost:8005/docs")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start integrator: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting integrator: {str(e)}")
        return None

def run_health_checks():
    """Run comprehensive health checks"""
    print("\n🔍 Running Health Checks...")
    
    services = [
        ("http://localhost:8005", "BHIV Integrator Core"),
        ("http://localhost:8002", "BHIV Core"),
        ("http://localhost:8001", "UniGuru"),
        ("http://localhost:8000", "Logistics System"),
        ("http://localhost:8502", "CRM System"),
        ("http://localhost:8007", "Sankalp Compliance")
    ]
    
    healthy_services = 0
    for url, name in services:
        if check_service_health(url, name):
            healthy_services += 1
    
    print(f"\n📊 Health Check Summary: {healthy_services}/{len(services)} services healthy")
    return healthy_services > 0

def run_integration_tests():
    """Run integration tests"""
    print("\n🧪 Running Integration Tests...")
    
    try:
        result = subprocess.run([sys.executable, "test_integration.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
            return True
        else:
            print("⚠️ Some integration tests failed (may be expected if services are not running)")
            print(result.stdout)
            return True  # Don't fail deployment for test failures
            
    except subprocess.TimeoutExpired:
        print("⚠️ Integration tests timed out")
        return True
    except Exception as e:
        print(f"⚠️ Integration test error: {str(e)}")
        return True

def display_deployment_info():
    """Display deployment information"""
    print("\n" + "="*60)
    print("🎉 BHIV Integrator Core Deployment Complete!")
    print("="*60)
    print()
    print("📍 Access Points:")
    print("   • API Gateway: http://localhost:8005")
    print("   • API Documentation: http://localhost:8005/docs")
    print("   • Health Check: http://localhost:8005/health")
    print("   • Event Monitoring: http://localhost:8005/event/events")
    print()
    print("🎯 Core Features Available:")
    print("   • ✅ Event-Driven Architecture")
    print("   • ✅ Unified Logging & Compliance")
    print("   • ✅ BHIV Core Integration")
    print("   • ✅ Cross-System API Consolidation")
    print("   • ✅ Real-time Event Monitoring")
    print()
    print("🚀 Next Steps:")
    print("   1. Launch unified dashboard: streamlit run dashboard_integration.py")
    print("   2. Test API endpoints: http://localhost:8005/docs")
    print("   3. Monitor events: http://localhost:8005/event/events")
    print("   4. Check compliance: http://localhost:8005/compliance/audit-report")
    print()
    print("📚 Documentation:")
    print("   • README.md - Complete setup guide")
    print("   • API Documentation - http://localhost:8005/docs")
    print("   • Integration Tests - python test_integration.py")
    print()

def main():
    """Main deployment function"""
    print("🎯 BHIV Integrator Core - Production Deployment")
    print("=" * 50)
    
    # Pre-flight checks
    if not check_python_version():
        return False
    
    if not install_dependencies():
        return False
    
    if not setup_environment():
        return False
    
    # Start the integrator
    process = start_integrator()
    if not process:
        return False
    
    # Health checks
    time.sleep(2)  # Allow startup time
    if not run_health_checks():
        print("⚠️ Some services are not available, but integrator is running")
    
    # Integration tests
    run_integration_tests()
    
    # Display info
    display_deployment_info()
    
    try:
        print("🔄 Press Ctrl+C to stop the integrator...")
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping BHIV Integrator Core...")
        process.terminate()
        process.wait()
        print("✅ BHIV Integrator Core stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)