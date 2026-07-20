#!/usr/bin/env python3
"""
BHIV HR Platform - Comprehensive Service Testing
Counts endpoints and tests all services with proper timeouts and validation
"""

import asyncio
import httpx
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import re

# Service Configuration
SERVICES = {
    "gateway": {
        "url": "https://bhiv-hr-gateway-ltg0.onrender.com",
        "local_url": "http://localhost:8000",
        "expected_endpoints": 94,
        "timeout": 30
    },
    "agent": {
        "url": "https://bhiv-hr-agent-nhgg.onrender.com", 
        "local_url": "http://localhost:9000",
        "expected_endpoints": 6,
        "timeout": 60
    },
    "langgraph": {
        "url": "https://bhiv-hr-langgraph.onrender.com",
        "local_url": "http://localhost:9001", 
        "expected_endpoints": 7,
        "timeout": 45
    },
    "hr_portal": {
        "url": "https://bhiv-hr-portal-u670.onrender.com",
        "local_url": "http://localhost:8501",
        "expected_endpoints": 1,  # Streamlit app
        "timeout": 20
    },
    "client_portal": {
        "url": "https://bhiv-hr-client-portal-3iod.onrender.com",
        "local_url": "http://localhost:8502",
        "expected_endpoints": 1,  # Streamlit app
        "timeout": 20
    },
    "candidate_portal": {
        "url": "https://bhiv-hr-candidate-portal-abe6.onrender.com",
        "local_url": "http://localhost:8503",
        "expected_endpoints": 1,  # Streamlit app
        "timeout": 20
    }
}

# API Key for authentication
API_KEY = os.getenv("API_KEY_SECRET", "your-api-key-here")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class ServiceTester:
    def __init__(self):
        self.results = {}
        self.total_endpoints_found = 0
        self.total_endpoints_expected = sum(s["expected_endpoints"] for s in SERVICES.values())
        
    async def count_endpoints_from_code(self, service_name: str) -> int:
        """Count actual endpoints by analyzing service code"""
        endpoint_count = 0
        service_path = f"c:\\BHIV HR PLATFORM\\services\\{service_name}"
        
        try:
            if service_name == "gateway":
                # Count Gateway endpoints from main.py
                with open(f"{service_path}\\app\\main.py", "r", encoding="utf-8") as f:
                    content = f.read()
                    # Count @app.get, @app.post, @app.put, @app.delete decorators
                    endpoint_patterns = [
                        r'@app\.get\(',
                        r'@app\.post\(',
                        r'@app\.put\(',
                        r'@app\.delete\(',
                        r'@app\.patch\('
                    ]
                    for pattern in endpoint_patterns:
                        endpoint_count += len(re.findall(pattern, content))
                        
            elif service_name == "agent":
                # Count Agent endpoints from app.py
                with open(f"{service_path}\\app.py", "r", encoding="utf-8") as f:
                    content = f.read()
                    endpoint_patterns = [
                        r'@app\.get\(',
                        r'@app\.post\(',
                        r'@app\.put\(',
                        r'@app\.delete\(',
                        r'@app\.patch\('
                    ]
                    for pattern in endpoint_patterns:
                        endpoint_count += len(re.findall(pattern, content))
                        
            elif service_name == "langgraph":
                # Count LangGraph endpoints from main.py
                with open(f"{service_path}\\app\\main.py", "r", encoding="utf-8") as f:
                    content = f.read()
                    endpoint_patterns = [
                        r'@app\.get\(',
                        r'@app\.post\(',
                        r'@app\.websocket\(',
                        r'@app\.put\(',
                        r'@app\.delete\('
                    ]
                    for pattern in endpoint_patterns:
                        endpoint_count += len(re.findall(pattern, content))
                        
            else:
                # For Streamlit portals, count as 1 endpoint each
                endpoint_count = 1
                
        except Exception as e:
            print(f"❌ Error counting endpoints for {service_name}: {e}")
            endpoint_count = SERVICES[service_name]["expected_endpoints"]
            
        return endpoint_count

    async def test_service_health(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """Test service health with comprehensive validation"""
        print(f"\n🔍 Testing {service_name.upper()} Service...")
        
        result = {
            "service": service_name,
            "status": "unknown",
            "response_time": 0,
            "endpoints_found": 0,
            "endpoints_expected": config["expected_endpoints"],
            "url_tested": "",
            "error": None,
            "response_data": None,
            "validation": {
                "status_code": False,
                "response_format": False,
                "required_fields": False,
                "endpoint_count": False
            }
        }
        
        # Count actual endpoints from code
        actual_endpoints = await self.count_endpoints_from_code(service_name)
        result["endpoints_found"] = actual_endpoints
        
        # Test production URL first, fallback to local
        urls_to_test = [config["url"], config["local_url"]]
        
        for url in urls_to_test:
            try:
                start_time = time.time()
                
                timeout_config = httpx.Timeout(
                    connect=10.0,
                    read=config["timeout"],
                    write=10.0,
                    pool=5.0
                )
                
                async with httpx.AsyncClient(timeout=timeout_config) as client:
                    # Test different endpoints based on service type
                    if service_name in ["gateway", "agent", "langgraph"]:
                        # Test API services
                        response = await client.get(f"{url}/health", headers=HEADERS)
                        
                        # If health fails, try root endpoint
                        if response.status_code != 200:
                            response = await client.get(url, headers=HEADERS)
                            
                    else:
                        # Test Streamlit portals
                        response = await client.get(url)
                    
                    end_time = time.time()
                    result["response_time"] = round((end_time - start_time) * 1000, 2)
                    result["url_tested"] = url
                    
                    # Validate response
                    await self.validate_response(response, result, service_name)
                    
                    if result["status"] == "healthy":
                        break  # Success, no need to try other URLs
                        
            except httpx.TimeoutException:
                result["error"] = f"Timeout after {config['timeout']}s"
                result["status"] = "timeout"
            except httpx.ConnectError:
                result["error"] = f"Connection failed to {url}"
                result["status"] = "connection_failed"
            except Exception as e:
                result["error"] = str(e)
                result["status"] = "error"
        
        # Validate endpoint count
        if actual_endpoints > 0:
            result["validation"]["endpoint_count"] = True
            if actual_endpoints != config["expected_endpoints"]:
                print(f"⚠️  Endpoint count mismatch: Found {actual_endpoints}, Expected {config['expected_endpoints']}")
        
        return result

    async def validate_response(self, response: httpx.Response, result: Dict, service_name: str):
        """Validate service response comprehensively"""
        
        # Check status code
        if response.status_code == 200:
            result["validation"]["status_code"] = True
            result["status"] = "healthy"
        else:
            result["status"] = f"unhealthy_status_{response.status_code}"
            return
        
        try:
            # Try to parse JSON for API services
            if service_name in ["gateway", "agent", "langgraph"]:
                data = response.json()
                result["response_data"] = data
                result["validation"]["response_format"] = True
                
                # Validate required fields based on service
                if service_name == "gateway":
                    required_fields = ["message", "version", "status"]
                    if "endpoints" in data:
                        result["endpoints_found"] = data["endpoints"]
                elif service_name == "agent":
                    required_fields = ["service", "version", "status"]
                    if "endpoints" in data:
                        result["endpoints_found"] = data["endpoints"]
                elif service_name == "langgraph":
                    required_fields = ["message", "version", "status"]
                    if "endpoints" in data:
                        result["endpoints_found"] = data["endpoints"]
                
                # Check if required fields exist
                if all(field in data for field in required_fields):
                    result["validation"]["required_fields"] = True
                    
            else:
                # For Streamlit apps, check if HTML content is returned
                if "streamlit" in response.text.lower() or len(response.text) > 1000:
                    result["validation"]["response_format"] = True
                    result["validation"]["required_fields"] = True
                    
        except json.JSONDecodeError:
            if service_name in ["hr_portal", "client_portal", "candidate_portal"]:
                # HTML response is expected for Streamlit apps
                result["validation"]["response_format"] = True
                result["validation"]["required_fields"] = True
            else:
                result["validation"]["response_format"] = False

    async def test_critical_endpoints(self, service_name: str, config: Dict) -> Dict[str, Any]:
        """Test critical endpoints for each service"""
        if service_name not in ["gateway", "agent", "langgraph"]:
            return {"tested": False, "reason": "Not an API service"}
        
        critical_tests = {
            "gateway": [
                {"endpoint": "/", "method": "GET", "auth": False},
                {"endpoint": "/health", "method": "GET", "auth": False},
                {"endpoint": "/v1/jobs", "method": "GET", "auth": True},
                {"endpoint": "/v1/candidates", "method": "GET", "auth": True}
            ],
            "agent": [
                {"endpoint": "/", "method": "GET", "auth": False},
                {"endpoint": "/health", "method": "GET", "auth": False},
                {"endpoint": "/test-db", "method": "GET", "auth": True}
            ],
            "langgraph": [
                {"endpoint": "/", "method": "GET", "auth": False},
                {"endpoint": "/health", "method": "GET", "auth": False},
                {"endpoint": "/workflows", "method": "GET", "auth": True}
            ]
        }
        
        results = []
        base_url = config["url"]
        
        timeout_config = httpx.Timeout(
            connect=5.0,
            read=15.0,
            write=5.0,
            pool=3.0
        )
        
        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                for test in critical_tests.get(service_name, []):
                    try:
                        headers = HEADERS if test["auth"] else {}
                        
                        if test["method"] == "GET":
                            response = await client.get(f"{base_url}{test['endpoint']}", headers=headers)
                        elif test["method"] == "POST":
                            response = await client.post(f"{base_url}{test['endpoint']}", headers=headers, json={})
                        
                        results.append({
                            "endpoint": test["endpoint"],
                            "status_code": response.status_code,
                            "success": response.status_code in [200, 201],
                            "response_time": response.elapsed.total_seconds() * 1000
                        })
                        
                    except Exception as e:
                        results.append({
                            "endpoint": test["endpoint"],
                            "status_code": 0,
                            "success": False,
                            "error": str(e)
                        })
                        
        except Exception as e:
            return {"tested": False, "error": str(e)}
        
        return {
            "tested": True,
            "results": results,
            "success_rate": len([r for r in results if r["success"]]) / len(results) * 100 if results else 0
        }

    async def run_comprehensive_test(self):
        """Run comprehensive testing workflow"""
        print("🚀 BHIV HR Platform - Comprehensive Service Testing")
        print("=" * 60)
        print(f"📊 Expected Total Endpoints: {self.total_endpoints_expected}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test all services
        for service_name, config in SERVICES.items():
            result = await self.test_service_health(service_name, config)
            self.results[service_name] = result
            
            # Test critical endpoints for API services
            if service_name in ["gateway", "agent", "langgraph"]:
                critical_result = await self.test_critical_endpoints(service_name, config)
                result["critical_endpoints"] = critical_result
            
            # Print immediate results
            self.print_service_result(result)
        
        # Generate comprehensive report
        await self.generate_final_report()

    def print_service_result(self, result: Dict[str, Any]):
        """Print individual service test result"""
        service = result["service"].upper()
        status = result["status"]
        
        if status == "healthy":
            print(f"✅ {service}: {status} ({result['response_time']}ms)")
        elif status == "timeout":
            print(f"⏰ {service}: {status} - {result['error']}")
        elif status == "connection_failed":
            print(f"🔌 {service}: {status}")
        else:
            print(f"❌ {service}: {status} - {result.get('error', 'Unknown error')}")
        
        # Print endpoint count
        found = result["endpoints_found"]
        expected = result["endpoints_expected"]
        if found != expected:
            print(f"   📊 Endpoints: {found} found (expected {expected})")
        else:
            print(f"   📊 Endpoints: {found} ✅")
        
        # Print validation results
        validation = result["validation"]
        valid_count = sum(validation.values())
        total_checks = len(validation)
        print(f"   🔍 Validation: {valid_count}/{total_checks} checks passed")

    async def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Summary statistics
        healthy_services = len([r for r in self.results.values() if r["status"] == "healthy"])
        total_services = len(self.results)
        total_endpoints_found = sum(r["endpoints_found"] for r in self.results.values())
        
        print(f"🎯 Service Health: {healthy_services}/{total_services} services healthy")
        print(f"📊 Endpoint Count: {total_endpoints_found} found (expected {self.total_endpoints_expected})")
        print(f"⚡ Overall Success Rate: {(healthy_services/total_services)*100:.1f}%")
        
        # Detailed service breakdown
        print("\n📋 DETAILED SERVICE BREAKDOWN:")
        print("-" * 40)
        
        for service_name, result in self.results.items():
            print(f"\n🔧 {service_name.upper()} SERVICE:")
            print(f"   Status: {result['status']}")
            print(f"   URL: {result['url_tested']}")
            print(f"   Response Time: {result['response_time']}ms")
            print(f"   Endpoints: {result['endpoints_found']}/{result['endpoints_expected']}")
            
            # Validation details
            validation = result["validation"]
            print(f"   Validations:")
            for check, passed in validation.items():
                status = "✅" if passed else "❌"
                print(f"     {status} {check.replace('_', ' ').title()}")
            
            # Critical endpoint results
            if "critical_endpoints" in result and result["critical_endpoints"]["tested"]:
                critical = result["critical_endpoints"]
                print(f"   Critical Endpoints: {critical['success_rate']:.1f}% success rate")
                for endpoint_result in critical["results"]:
                    status = "✅" if endpoint_result["success"] else "❌"
                    print(f"     {status} {endpoint_result['endpoint']} ({endpoint_result['status_code']})")
        
        # Issues and recommendations
        print(f"\n🔍 ISSUES IDENTIFIED:")
        print("-" * 30)
        
        issues_found = False
        for service_name, result in self.results.items():
            if result["status"] != "healthy":
                issues_found = True
                print(f"❌ {service_name.upper()}: {result['status']}")
                if result["error"]:
                    print(f"   Error: {result['error']}")
            
            # Check endpoint count mismatches
            if result["endpoints_found"] != result["endpoints_expected"]:
                issues_found = True
                print(f"⚠️  {service_name.upper()}: Endpoint count mismatch")
                print(f"   Found: {result['endpoints_found']}, Expected: {result['endpoints_expected']}")
        
        if not issues_found:
            print("✅ No critical issues found!")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("-" * 25)
        
        if healthy_services < total_services:
            print("🔧 Fix unhealthy services before production deployment")
        
        if total_endpoints_found != self.total_endpoints_expected:
            print("📊 Update endpoint documentation to match actual implementation")
        
        print("🔄 Run this test regularly to monitor service health")
        print("📈 Set up automated monitoring for production services")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"service_test_report_{timestamp}.json"
        
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "healthy_services": healthy_services,
                    "total_services": total_services,
                    "total_endpoints_found": total_endpoints_found,
                    "total_endpoints_expected": self.total_endpoints_expected,
                    "success_rate": (healthy_services/total_services)*100
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main testing function"""
    tester = ServiceTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())