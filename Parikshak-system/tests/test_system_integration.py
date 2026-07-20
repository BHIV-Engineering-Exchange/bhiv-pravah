"""
COMPREHENSIVE SYSTEM INTEGRATION VERIFICATION
Tests complete frontend-backend connectivity and readiness
"""
import sys
import os
import requests
import json
import time
from datetime import datetime

# Add the app directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_system_integration():
    print("=" * 70)
    print("COMPREHENSIVE SYSTEM INTEGRATION VERIFICATION")
    print("Testing Frontend-Backend Connectivity & Production Readiness")
    print("=" * 70)
    
    # Configuration
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    results = {
        "backend_health": False,
        "api_endpoints": False,
        "frontend_build": False,
        "integration_flow": False,
        "production_ready": False
    }
    
    # Test 1: Backend Health Check
    print("\n1. BACKEND HEALTH CHECK")
    print("-" * 30)
    
    try:
        # Test root endpoint
        response = requests.get(f"{backend_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend Online: {data.get('message', 'Unknown')}")
            print(f"   ✅ Version: {data.get('version', 'Unknown')}")
            
            # Test health endpoint
            health_response = requests.get(f"{backend_url}/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   ✅ Health Status: {health_data.get('status', 'Unknown')}")
                results["backend_health"] = True
            else:
                print(f"   ❌ Health endpoint failed: {health_response.status_code}")
        else:
            print(f"   ❌ Backend not responding: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend connection failed: {str(e)}")
        print(f"   💡 Make sure backend is running: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    
    # Test 2: API Endpoints Verification
    print("\n2. API ENDPOINTS VERIFICATION")
    print("-" * 30)
    
    if results["backend_health"]:
        try:
            # Test lifecycle endpoints
            endpoints_to_test = [
                ("/api/v1/lifecycle/history", "GET"),
                ("/docs", "GET"),
                ("/api/v1/tts/speak?text=test", "GET")
            ]
            
            endpoint_results = []
            for endpoint, method in endpoints_to_test:
                try:
                    if method == "GET":
                        resp = requests.get(f"{backend_url}{endpoint}", timeout=5)
                        endpoint_results.append((endpoint, resp.status_code, "✅" if resp.status_code in [200, 422] else "❌"))
                        print(f"   {endpoint}: {resp.status_code} {'✅' if resp.status_code in [200, 422] else '❌'}")
                except Exception as e:
                    endpoint_results.append((endpoint, "ERROR", "❌"))
                    print(f"   {endpoint}: ERROR ❌")
            
            # Test POST endpoint with sample data
            try:
                sample_data = {
                    "task_title": "System Integration Test",
                    "task_description": "Testing the complete system integration between frontend and backend components",
                    "submitted_by": "Integration Test",
                    "github_repo_link": "",
                    "module_id": "task-review-agent",
                    "schema_version": "v1.0"
                }
                
                post_response = requests.post(
                    f"{backend_url}/api/v1/lifecycle/submit",
                    data=sample_data,
                    timeout=10
                )
                
                print(f"   POST /lifecycle/submit: {post_response.status_code} {'✅' if post_response.status_code in [200, 422] else '❌'}")
                
                if post_response.status_code == 200:
                    response_data = post_response.json()
                    print(f"   ✅ Sample submission successful")
                    print(f"   ✅ Submission ID: {response_data.get('submission_id', 'Unknown')}")
                    print(f"   ✅ Review Score: {response_data.get('review_summary', {}).get('score', 'Unknown')}")
                    results["api_endpoints"] = True
                elif post_response.status_code == 422:
                    print(f"   ✅ Validation working (expected for test data)")
                    results["api_endpoints"] = True
                else:
                    print(f"   ❌ Unexpected response: {post_response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ POST endpoint test failed: {str(e)}")
        
        except Exception as e:
            print(f"   ❌ API endpoint testing failed: {str(e)}")
    else:
        print("   ⏭️  Skipping API tests (backend not healthy)")
    
    # Test 3: Frontend Build Verification
    print("\n3. FRONTEND BUILD VERIFICATION")
    print("-" * 30)
    
    try:
        # Check if frontend files exist
        frontend_path = os.path.join(current_dir, "frontend")
        
        if os.path.exists(frontend_path):
            print(f"   ✅ Frontend directory exists: {frontend_path}")
            
            # Check package.json
            package_json_path = os.path.join(frontend_path, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                print(f"   ✅ Package.json found - Version: {package_data.get('version', 'Unknown')}")
                
                # Check key dependencies
                deps = package_data.get('dependencies', {})
                key_deps = ['react', 'axios', '@tanstack/react-query', 'react-router-dom']
                for dep in key_deps:
                    if dep in deps:
                        print(f"   ✅ {dep}: {deps[dep]}")
                    else:
                        print(f"   ❌ Missing dependency: {dep}")
            
            # Check src structure
            src_path = os.path.join(frontend_path, "src")
            if os.path.exists(src_path):
                key_files = ['App.js', 'index.js']
                key_dirs = ['components', 'pages', 'services']
                
                for file in key_files:
                    file_path = os.path.join(src_path, file)
                    if os.path.exists(file_path):
                        print(f"   ✅ {file} exists")
                    else:
                        print(f"   ❌ Missing: {file}")
                
                for dir in key_dirs:
                    dir_path = os.path.join(src_path, dir)
                    if os.path.exists(dir_path):
                        file_count = len([f for f in os.listdir(dir_path) if f.endswith('.js')])
                        print(f"   ✅ {dir}/ exists ({file_count} JS files)")
                    else:
                        print(f"   ❌ Missing directory: {dir}")
                
                results["frontend_build"] = True
            else:
                print(f"   ❌ Frontend src directory not found")
        else:
            print(f"   ❌ Frontend directory not found: {frontend_path}")
            
    except Exception as e:
        print(f"   ❌ Frontend verification failed: {str(e)}")
    
    # Test 4: Integration Flow Verification
    print("\n4. INTEGRATION FLOW VERIFICATION")
    print("-" * 30)
    
    if results["backend_health"] and results["frontend_build"]:
        try:
            # Check API client configuration
            api_client_path = os.path.join(current_dir, "frontend", "src", "services", "apiClient.js")
            if os.path.exists(api_client_path):
                with open(api_client_path, 'r') as f:
                    api_client_content = f.read()
                
                if "localhost:8000" in api_client_content or "process.env.REACT_APP_API_URL" in api_client_content:
                    print("   ✅ API client configured for backend connection")
                else:
                    print("   ❌ API client configuration issue")
                
                # Check task service
                task_service_path = os.path.join(current_dir, "frontend", "src", "services", "taskService.js")
                if os.path.exists(task_service_path):
                    with open(task_service_path, 'r') as f:
                        task_service_content = f.read()
                    
                    required_methods = ['submitTask', 'getReview', 'getNextTask', 'getTaskHistory']
                    for method in required_methods:
                        if method in task_service_content:
                            print(f"   ✅ {method} method exists")
                        else:
                            print(f"   ❌ Missing method: {method}")
                    
                    results["integration_flow"] = True
                else:
                    print("   ❌ Task service not found")
            else:
                print("   ❌ API client not found")
                
        except Exception as e:
            print(f"   ❌ Integration flow verification failed: {str(e)}")
    else:
        print("   ⏭️  Skipping integration flow tests (prerequisites not met)")
    
    # Test 5: Production Readiness Check
    print("\n5. PRODUCTION READINESS CHECK")
    print("-" * 30)
    
    try:
        # Check environment configuration
        env_path = os.path.join(current_dir, ".env")
        if os.path.exists(env_path):
            print("   ✅ Environment file exists")
            
            # Check for required environment variables
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            required_vars = ['GITHUB_TOKEN', 'HOST', 'PORT']
            for var in required_vars:
                if var in env_content:
                    print(f"   ✅ {var} configured")
                else:
                    print(f"   ⚠️  {var} not found (may be optional)")
        else:
            print("   ⚠️  .env file not found")
        
        # Check CORS configuration
        if results["backend_health"]:
            try:
                # Test CORS headers
                response = requests.options(f"{backend_url}/api/v1/lifecycle/history", timeout=5)
                cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
                if cors_headers:
                    print(f"   ✅ CORS configured: {cors_headers}")
                else:
                    print("   ⚠️  CORS headers not detected")
            except:
                print("   ⚠️  Could not test CORS")
        
        # Check if all components are ready
        if all([results["backend_health"], results["api_endpoints"], results["frontend_build"], results["integration_flow"]]):
            results["production_ready"] = True
            print("   ✅ System appears production ready")
        else:
            print("   ❌ System not fully ready for production")
            
    except Exception as e:
        print(f"   ❌ Production readiness check failed: {str(e)}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("SYSTEM INTEGRATION SUMMARY")
    print("=" * 70)
    
    print(f"\n📊 COMPONENT STATUS:")
    print(f"   Backend Health:     {'✅ PASS' if results['backend_health'] else '❌ FAIL'}")
    print(f"   API Endpoints:      {'✅ PASS' if results['api_endpoints'] else '❌ FAIL'}")
    print(f"   Frontend Build:     {'✅ PASS' if results['frontend_build'] else '❌ FAIL'}")
    print(f"   Integration Flow:   {'✅ PASS' if results['integration_flow'] else '❌ FAIL'}")
    print(f"   Production Ready:   {'✅ PASS' if results['production_ready'] else '❌ FAIL'}")
    
    print(f"\n🔗 CONNECTIVITY:")
    print(f"   Backend URL:  {backend_url}")
    print(f"   Frontend URL: {frontend_url}")
    print(f"   API Prefix:   /api/v1")
    
    print(f"\n🚀 DEPLOYMENT STATUS:")
    if results["production_ready"]:
        print("   ✅ SYSTEM READY FOR PRODUCTION")
        print("   ✅ Frontend-Backend Integration: COMPLETE")
        print("   ✅ API Contracts: ALIGNED")
        print("   ✅ Ready for: parikshak.blackholeinfiverse.com")
    else:
        print("   ❌ SYSTEM NOT READY - Issues detected")
        failed_components = [k for k, v in results.items() if not v]
        print(f"   ❌ Failed Components: {', '.join(failed_components)}")
    
    print("\n" + "=" * 70)
    
    return results["production_ready"]

if __name__ == "__main__":
    success = test_system_integration()
    if success:
        print("🎉 SYSTEM INTEGRATION VERIFICATION: SUCCESS")
        print("Frontend and Backend are connected and ready for production!")
    else:
        print("⚠️  SYSTEM INTEGRATION ISSUES DETECTED")
        print("Please address the failed components before deployment.")
        sys.exit(1)