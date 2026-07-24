#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing Script

Tests all InsightFlow endpoints to verify functionality.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Base URL for the API
BASE_URL = "http://localhost:8000"

class EndpointTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None, 
        headers: Dict = None,
        expected_status: int = 200,
        description: str = ""
    ) -> Tuple[bool, str, Dict]:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, 
                url, 
                json=data, 
                headers=headers or {},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_data = {}
                try:
                    response_data = await response.json()
                except:
                    response_data = {"text": await response.text()}
                
                success = response.status == expected_status
                status_msg = f"✅ PASS" if success else f"❌ FAIL"
                
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status,
                    "expected_status": expected_status,
                    "success": success,
                    "response": response_data,
                    "description": description
                }
                
                self.results.append(result)
                
                print(f"{status_msg} {method} {endpoint} - {response.status} - {description}")
                
                return success, f"{response.status}", response_data
                
        except Exception as e:
            error_msg = f"❌ ERROR {method} {endpoint} - {str(e)} - {description}"
            print(error_msg)
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "expected_status": expected_status,
                "success": False,
                "error": str(e),
                "description": description
            }
            
            self.results.append(result)
            return False, str(e), {}
    
    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting comprehensive endpoint testing...")
        print("=" * 60)
        
        # 1. Basic Health Checks
        print("\n📋 1. BASIC HEALTH CHECKS")
        await self.test_endpoint("GET", "/", description="Root endpoint")
        await self.test_endpoint("GET", "/health", description="Health check")
        await self.test_endpoint("GET", "/test", description="Test endpoint")
        
        # 2. API Version Info
        print("\n📋 2. API VERSION INFO")
        await self.test_endpoint("GET", "/api/version", description="API version info")
        
        # 3. Core Endpoints (No Auth Required)
        print("\n📋 3. CORE ENDPOINTS")
        await self.test_endpoint("GET", "/api/feedback/metrics", description="Feedback metrics")
        await self.test_endpoint("GET", "/api/scoring/weights", description="Scoring weights")
        await self.test_endpoint("GET", "/api/route-agent/test", description="Route agent test")
        
        # 4. Routing Decision Logs
        print("\n📋 4. ROUTING LOGS")
        await self.test_endpoint("GET", "/api/routing/decisions", description="Routing decisions")
        await self.test_endpoint("GET", "/api/routing/statistics", description="Routing statistics")
        
        # 5. STP Endpoints
        print("\n📋 5. STP ENDPOINTS")
        await self.test_endpoint("GET", "/api/stp/metrics", description="STP metrics")
        
        # Test STP unwrap with sample data
        stp_test_data = {
            "stp_token": "test_token",
            "payload": {"test": "data"},
            "metadata": {"source": "test"}
        }
        await self.test_endpoint(
            "POST", "/api/stp/unwrap", 
            data=stp_test_data, 
            description="STP packet unwrap"
        )
        
        # 6. Karma Endpoints
        print("\n📋 6. KARMA ENDPOINTS")
        await self.test_endpoint("GET", "/api/karma/metrics", description="Karma metrics")
        await self.test_endpoint("GET", "/api/karma/score/test-agent", description="Agent Karma score")
        await self.test_endpoint(
            "POST", "/api/karma/toggle", 
            data={"enabled": True}, 
            description="Toggle Karma weighting"
        )
        
        # 7. Route Agent Endpoint (Core Functionality)
        print("\n📋 7. ROUTE AGENT ENDPOINT")
        route_agent_data = {
            "agent_type": "nlp",
            "context": {"priority": "normal"},
            "confidence_threshold": 0.5
        }
        await self.test_endpoint(
            "POST", "/api/v1/routing/route-agent",
            data=route_agent_data,
            expected_status=404,  # Expected since no agents in DB
            description="Route agent (no agents available)"
        )
        
        # 8. Admin Endpoints (May require auth)
        print("\n📋 8. ADMIN ENDPOINTS")
        await self.test_endpoint(
            "GET", "/admin/routing-logs", 
            expected_status=401,  # Expected auth error
            description="Admin routing logs (auth required)"
        )
        await self.test_endpoint(
            "GET", "/admin/routing-statistics",
            expected_status=401,  # Expected auth error
            description="Admin routing statistics (auth required)"
        )
        
        # 9. Karma Admin Endpoints
        print("\n📋 9. KARMA ADMIN ENDPOINTS")
        await self.test_endpoint(
            "POST", "/admin/karma/toggle?enabled=true",
            expected_status=401,  # Expected auth error
            description="Admin Karma toggle (auth required)"
        )
        await self.test_endpoint(
            "GET", "/admin/karma/metrics",
            expected_status=401,  # Expected auth error
            description="Admin Karma metrics (auth required)"
        )
        await self.test_endpoint(
            "DELETE", "/admin/karma/cache",
            expected_status=401,  # Expected auth error
            description="Admin Karma cache clear (auth required)"
        )
        
        # 10. Dashboard Endpoints
        print("\n📋 10. DASHBOARD ENDPOINTS")
        await self.test_endpoint(
            "GET", "/dashboard/metrics/performance",
            expected_status=401,  # Expected auth error
            description="Dashboard performance metrics (auth required)"
        )
        
        # 11. Migration Endpoints
        print("\n📋 11. MIGRATION ENDPOINTS")
        await self.test_endpoint(
            "GET", "/api/migration/status",
            expected_status=401,  # Expected auth error
            description="Migration status (auth required)"
        )
        
        # 12. WebSocket Health (Can't test WebSocket easily, but check if endpoint exists)
        print("\n📋 12. WEBSOCKET ENDPOINTS")
        await self.test_endpoint(
            "GET", "/ws/health",
            expected_status=404,  # WebSocket endpoints may not respond to GET
            description="WebSocket health check"
        )
        
        print("\n" + "=" * 60)
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    status = result.get("status_code", "ERROR")
                    print(f"  - {result['method']} {result['endpoint']} ({status}) - {result['description']}")
        
        print(f"\n📝 DETAILED RESULTS:")
        for result in self.results:
            status_icon = "✅" if result["success"] else "❌"
            status_code = result.get("status_code", "ERROR")
            print(f"  {status_icon} {result['method']} {result['endpoint']} ({status_code}) - {result['description']}")

async def main():
    """Main test runner"""
    print("InsightFlow Endpoint Testing Suite")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    
    async with EndpointTester(BASE_URL) as tester:
        await tester.run_all_tests()
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)