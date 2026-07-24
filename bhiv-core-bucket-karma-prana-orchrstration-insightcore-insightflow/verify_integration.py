"""
BHIV Core ↔ Bucket Integration Verification Script
Tests all integration points and identifies gaps
"""

import requests
import json
import time
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def test_bucket_health():
    """Test Bucket service health"""
    print_header("1. Testing Bucket Health")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Bucket Status: {data.get('status')}")
            
            services = data.get('services', {})
            print(f"  MongoDB: {services.get('mongodb')}")
            print(f"  Redis: {services.get('redis')}")
            print(f"  Audit Middleware: {services.get('audit_middleware')}")
            
            if services.get('mongodb') == 'connected':
                print_success("MongoDB connected successfully")
            else:
                print_error("MongoDB not connected")
                
            if services.get('redis') == 'connected':
                print_success("Redis connected successfully")
            else:
                print_error("Redis not connected")
                
            return True
        else:
            print_error(f"Bucket health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to Bucket: {e}")
        print_warning("Make sure Bucket is running: cd BHIV_Central_Depository-main && python main.py")
        return False

def test_core_health():
    """Test Core service health"""
    print_header("2. Testing Core Health")
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Core Status: {data.get('status')}")
            
            services = data.get('services', {})
            print(f"  MongoDB: {services.get('mongodb')}")
            print(f"  Agent Registry: {services.get('agent_registry')}")
            
            metrics = data.get('metrics', {})
            print(f"  Total Requests: {metrics.get('total_requests', 0)}")
            print(f"  Success Rate: {metrics.get('success_rate_percent', 0)}%")
            
            return True
        else:
            print_error(f"Core health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to Core: {e}")
        print_warning("Make sure Core is running: cd v1-BHIV_CORE-main && python mcp_bridge.py")
        return False

def test_core_task_processing():
    """Test Core task processing"""
    print_header("3. Testing Core Task Processing")
    try:
        payload = {
            "agent": "edumentor_agent",
            "input": "Integration verification test",
            "input_type": "text"
        }
        
        print("Sending task to Core...")
        response = requests.post(
            "http://localhost:8002/handle_task",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("Core processed task successfully")
            print(f"  Task ID: {result.get('task_id')}")
            print(f"  Status: {result.get('status')}")
            return True
        else:
            print_error(f"Core task processing failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Core task processing error: {e}")
        return False

def test_bucket_agents():
    """Test Bucket agents endpoint"""
    print_header("4. Testing Bucket Agents")
    try:
        response = requests.get("http://localhost:8000/agents", timeout=5)
        if response.status_code == 200:
            agents = response.json()
            print_success(f"Found {len(agents)} agents in Bucket")
            if agents:
                print("  Sample agents:")
                for agent in agents[:3]:
                    print(f"    - {agent.get('name', 'Unknown')}")
            return True
        else:
            print_error(f"Bucket agents endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Bucket agents error: {e}")
        return False

def test_bucket_baskets():
    """Test Bucket baskets endpoint"""
    print_header("5. Testing Bucket Baskets")
    try:
        response = requests.get("http://localhost:8000/baskets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            baskets = data.get('baskets', [])
            print_success(f"Found {len(baskets)} baskets in Bucket")
            if baskets:
                print("  Sample baskets:")
                for basket in baskets[:3]:
                    print(f"    - {basket.get('basket_name', 'Unknown')}")
            return True
        else:
            print_error(f"Bucket baskets endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Bucket baskets error: {e}")
        return False

def test_redis_connection():
    """Test Redis connection in Bucket"""
    print_header("6. Testing Redis Connection")
    try:
        response = requests.get("http://localhost:8000/redis/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Redis Status: {data.get('status')}")
            stats = data.get('stats', {})
            print(f"  Connected: {stats.get('connected')}")
            return True
        else:
            print_error(f"Redis status check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Redis connection error: {e}")
        return False

def test_core_bucket_integration():
    """Test Core-Bucket integration endpoints"""
    print_header("7. Testing Core-Bucket Integration")
    
    # Check if Core integration endpoints exist in Bucket
    integration_tests = []
    
    # Test 1: Check if Bucket has Core stats endpoint
    try:
        response = requests.get("http://localhost:8000/core/stats", timeout=5)
        if response.status_code == 200:
            print_success("Core stats endpoint exists in Bucket")
            integration_tests.append(True)
        else:
            print_warning("Core stats endpoint not found (may need implementation)")
            integration_tests.append(False)
    except Exception as e:
        print_error(f"Core stats endpoint error: {e}")
        integration_tests.append(False)
    
    # Test 2: Check if Bucket has Core events endpoint
    try:
        response = requests.get("http://localhost:8000/core/events", timeout=5)
        if response.status_code == 200:
            print_success("Core events endpoint exists in Bucket")
            integration_tests.append(True)
        else:
            print_warning("Core events endpoint not found (may need implementation)")
            integration_tests.append(False)
    except Exception as e:
        print_error(f"Core events endpoint error: {e}")
        integration_tests.append(False)
    
    return all(integration_tests)

def test_governance_endpoints():
    """Test governance endpoints"""
    print_header("8. Testing Governance System")
    try:
        response = requests.get("http://localhost:8000/governance/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Governance system active")
            print(f"  Bucket Version: {data.get('bucket_version')}")
            print(f"  Owner: {data.get('owner')}")
            return True
        else:
            print_error(f"Governance endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Governance error: {e}")
        return False

def generate_report(results):
    """Generate final verification report"""
    print_header("INTEGRATION VERIFICATION REPORT")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    if failed_tests > 0:
        print_error(f"Failed: {failed_tests}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*60)
    if passed_tests == total_tests:
        print_success("🎉 ALL TESTS PASSED - Integration is working correctly!")
    elif passed_tests >= total_tests * 0.7:
        print_warning(f"⚠️  PARTIAL SUCCESS - {passed_tests}/{total_tests} tests passed")
        print("Some features may need configuration or implementation")
    else:
        print_error(f"❌ INTEGRATION ISSUES - Only {passed_tests}/{total_tests} tests passed")
        print("Please check the errors above and fix configuration")
    
    print("\nNext Steps:")
    if not results.get('Bucket Health'):
        print("  1. Start Bucket: cd BHIV_Central_Depository-main && python main.py")
    if not results.get('Core Health'):
        print("  2. Start Core: cd v1-BHIV_CORE-main && python mcp_bridge.py")
    if not results.get('MongoDB Connection'):
        print("  3. Check MongoDB credentials in .env files")
    if not results.get('Redis Connection'):
        print("  4. Check Redis credentials in .env files")
    if not results.get('Core-Bucket Integration'):
        print("  5. Verify integration endpoints are implemented")

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("BHIV Core ↔ Bucket Integration Verification")
    print(f"{'='*60}{Colors.END}\n")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # Run all tests
    results['Bucket Health'] = test_bucket_health()
    time.sleep(1)
    
    results['Core Health'] = test_core_health()
    time.sleep(1)
    
    results['Core Task Processing'] = test_core_task_processing()
    time.sleep(1)
    
    results['Bucket Agents'] = test_bucket_agents()
    time.sleep(1)
    
    results['Bucket Baskets'] = test_bucket_baskets()
    time.sleep(1)
    
    results['Redis Connection'] = test_redis_connection()
    time.sleep(1)
    
    results['Core-Bucket Integration'] = test_core_bucket_integration()
    time.sleep(1)
    
    results['Governance System'] = test_governance_endpoints()
    
    # Generate report
    generate_report(results)

if __name__ == "__main__":
    main()
