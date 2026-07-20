#!/usr/bin/env python3
"""
Comprehensive Integration Test for LangGraph Service
Tests the complete workflow integration between LangGraph and Gateway services
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
GATEWAY_URL = "http://localhost:8000"
LANGGRAPH_URL = "http://localhost:9001"
API_KEY = "test-api-key-12345"

class IntegrationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_service_health(self):
        """Test both services are running"""
        print("\n🔍 Testing Service Health...")
        
        # Test Gateway
        try:
            async with self.session.get(f"{GATEWAY_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Gateway Health", True, f"Status: {data.get('status')}")
                else:
                    self.log_test("Gateway Health", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("Gateway Health", False, str(e))
        
        # Test LangGraph
        try:
            async with self.session.get(f"{LANGGRAPH_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("LangGraph Health", True, f"Status: {data.get('status')}")
                else:
                    self.log_test("LangGraph Health", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("LangGraph Health", False, str(e))
    
    async def test_gateway_endpoints(self):
        """Test key Gateway endpoints"""
        print("\n🔍 Testing Gateway Endpoints...")
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Test candidates endpoint
        try:
            async with self.session.get(f"{GATEWAY_URL}/v1/candidates", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    count = len(data) if isinstance(data, list) else data.get('count', 0)
                    self.log_test("Gateway Candidates", True, f"Found {count} candidates")
                else:
                    self.log_test("Gateway Candidates", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("Gateway Candidates", False, str(e))
        
        # Test jobs endpoint
        try:
            async with self.session.get(f"{GATEWAY_URL}/v1/jobs", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    count = len(data) if isinstance(data, list) else data.get('count', 0)
                    self.log_test("Gateway Jobs", True, f"Found {count} jobs")
                else:
                    self.log_test("Gateway Jobs", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("Gateway Jobs", False, str(e))
    
    async def test_langgraph_endpoints(self):
        """Test LangGraph service endpoints"""
        print("\n🔍 Testing LangGraph Endpoints...")
        
        # Test workflow status
        try:
            async with self.session.get(f"{LANGGRAPH_URL}/workflow/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("LangGraph Status", True, f"Active workflows: {data.get('active_workflows', 0)}")
                else:
                    self.log_test("LangGraph Status", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("LangGraph Status", False, str(e))
        
        # Test workflow list
        try:
            async with self.session.get(f"{LANGGRAPH_URL}/workflow/list") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    count = len(data.get('workflows', []))
                    self.log_test("LangGraph Workflows", True, f"Found {count} workflows")
                else:
                    self.log_test("LangGraph Workflows", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("LangGraph Workflows", False, str(e))
    
    async def test_workflow_execution(self):
        """Test complete workflow execution"""
        print("\n🔍 Testing Workflow Execution...")
        
        # Create test application data
        test_application = {
            "candidate_id": 1,
            "job_id": 1,
            "candidate_name": "Test Candidate",
            "candidate_email": "test@example.com",
            "candidate_phone": "+1234567890",
            "job_title": "Software Engineer"
        }
        
        try:
            # Start workflow
            async with self.session.post(
                f"{LANGGRAPH_URL}/workflow/start",
                json=test_application
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    workflow_id = data.get('workflow_id')
                    self.log_test("Workflow Start", True, f"ID: {workflow_id}")
                    
                    # Monitor workflow progress
                    await self.monitor_workflow(workflow_id)
                else:
                    self.log_test("Workflow Start", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_test("Workflow Start", False, str(e))
    
    async def monitor_workflow(self, workflow_id: str):
        """Monitor workflow execution"""
        print(f"\n📊 Monitoring Workflow {workflow_id}...")
        
        max_attempts = 30  # 30 seconds timeout
        attempt = 0
        
        while attempt < max_attempts:
            try:
                async with self.session.get(f"{LANGGRAPH_URL}/workflow/{workflow_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get('status')
                        stage = data.get('current_stage', 'unknown')
                        
                        print(f"  Status: {status}, Stage: {stage}")
                        
                        if status == 'completed':
                            self.log_test("Workflow Completion", True, f"Completed in stage: {stage}")
                            await self.verify_workflow_results(workflow_id, data)
                            break
                        elif status == 'failed':
                            error = data.get('error', 'Unknown error')
                            self.log_test("Workflow Completion", False, f"Failed: {error}")
                            break
                        
                        await asyncio.sleep(1)
                        attempt += 1
                    else:
                        self.log_test("Workflow Monitoring", False, f"HTTP {resp.status}")
                        break
            except Exception as e:
                self.log_test("Workflow Monitoring", False, str(e))
                break
        
        if attempt >= max_attempts:
            self.log_test("Workflow Timeout", False, "Workflow did not complete in 30 seconds")
    
    async def verify_workflow_results(self, workflow_id: str, workflow_data: Dict[Any, Any]):
        """Verify workflow produced expected results"""
        print(f"\n✅ Verifying Workflow Results for {workflow_id}...")
        
        # Check for expected fields
        expected_fields = ['application_status', 'matching_score', 'notifications_sent']
        
        for field in expected_fields:
            if field in workflow_data:
                value = workflow_data[field]
                self.log_test(f"Result Field: {field}", True, f"Value: {value}")
            else:
                self.log_test(f"Result Field: {field}", False, "Missing from results")
        
        # Verify application status is valid
        status = workflow_data.get('application_status')
        valid_statuses = ['shortlisted', 'rejected', 'pending']
        if status in valid_statuses:
            self.log_test("Valid Status", True, f"Status: {status}")
        else:
            self.log_test("Valid Status", False, f"Invalid status: {status}")
        
        # Verify matching score is reasonable
        score = workflow_data.get('matching_score')
        if isinstance(score, (int, float)) and 0 <= score <= 100:
            self.log_test("Valid Score", True, f"Score: {score}")
        else:
            self.log_test("Valid Score", False, f"Invalid score: {score}")
    
    async def test_gateway_langgraph_integration(self):
        """Test integration between Gateway and LangGraph"""
        print("\n🔍 Testing Gateway-LangGraph Integration...")
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Test if Gateway can trigger LangGraph workflow
        test_data = {
            "candidate_id": 1,
            "job_id": 1
        }
        
        try:
            async with self.session.post(
                f"{GATEWAY_URL}/v1/workflow/trigger",
                json=test_data,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test("Gateway-LangGraph Trigger", True, f"Response: {data}")
                else:
                    # This endpoint might not exist yet, so we'll test direct communication
                    self.log_test("Gateway-LangGraph Trigger", False, f"HTTP {resp.status} (endpoint may not exist)")
        except Exception as e:
            self.log_test("Gateway-LangGraph Trigger", False, str(e))
    
    async def test_error_handling(self):
        """Test error handling in both services"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid workflow data
        try:
            async with self.session.post(
                f"{LANGGRAPH_URL}/workflow/start",
                json={"invalid": "data"}
            ) as resp:
                if resp.status in [400, 422]:  # Expected error codes
                    self.log_test("Error Handling", True, f"Properly rejected invalid data: HTTP {resp.status}")
                else:
                    self.log_test("Error Handling", False, f"Unexpected response: HTTP {resp.status}")
        except Exception as e:
            self.log_test("Error Handling", False, str(e))
        
        # Test non-existent workflow
        try:
            async with self.session.get(f"{LANGGRAPH_URL}/workflow/nonexistent-id") as resp:
                if resp.status == 404:
                    self.log_test("404 Handling", True, "Properly returned 404 for non-existent workflow")
                else:
                    self.log_test("404 Handling", False, f"Unexpected response: HTTP {resp.status}")
        except Exception as e:
            self.log_test("404 Handling", False, str(e))
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Integration Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        await self.test_service_health()
        await self.test_gateway_endpoints()
        await self.test_langgraph_endpoints()
        await self.test_workflow_execution()
        await self.test_gateway_langgraph_integration()
        await self.test_error_handling()
        
        # Generate summary
        end_time = time.time()
        duration = end_time - start_time
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Integration is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check the details above.")
        
        # Save detailed results
        with open("integration_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "total_tests": total,
                    "passed": passed,
                    "failed": total - passed,
                    "success_rate": (passed/total)*100,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: integration_test_results.json")

async def main():
    """Main test runner"""
    async with IntegrationTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())