#!/usr/bin/env python3
"""
Complete Integration Test for BHIV HR Platform
Tests Gateway ↔ LangGraph integration and all services
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Service URLs
SERVICES = {
    "gateway": "http://localhost:8000",
    "agent": "http://localhost:9000", 
    "langgraph": "http://localhost:9001",
    "hr_portal": "http://localhost:8501",
    "client_portal": "http://localhost:8502",
    "candidate_portal": "http://localhost:8503"
}

API_KEY = "test-api-key-12345"

class IntegrationTester:
    def __init__(self):
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}: {details}")
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_all_services(self):
        """Test all services are running"""
        print("Testing All Services...")
        
        async with aiohttp.ClientSession() as session:
            for service, url in SERVICES.items():
                try:
                    if service.endswith('_portal'):
                        # Streamlit services - just check if accessible
                        async with session.get(url, timeout=5) as resp:
                            success = resp.status == 200
                            self.log_result(f"{service.upper()}", success, 
                                          f"HTTP {resp.status}" if not success else "Running")
                    else:
                        # API services - check health endpoint
                        async with session.get(f"{url}/health", timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                self.log_result(f"{service.upper()}", True, 
                                              f"Healthy - {data.get('status', 'OK')}")
                            else:
                                self.log_result(f"{service.upper()}", False, f"HTTP {resp.status}")
                                
                except Exception as e:
                    self.log_result(f"{service.upper()}", False, f"Offline - {str(e)}")
    
    async def test_gateway_langgraph_integration(self):
        """Test Gateway ↔ LangGraph integration"""
        print("\nTesting Gateway <-> LangGraph Integration...")
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {API_KEY}"}
            
            # Test 1: LangGraph health check via Gateway
            try:
                async with session.get(f"{SERVICES['gateway']}/api/v1/workflow/health", 
                                     headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get('langgraph_status', 'unknown')
                        self.log_result("Gateway -> LangGraph Health", 
                                      status == 'connected', f"Status: {status}")
                    else:
                        self.log_result("Gateway -> LangGraph Health", False, f"HTTP {resp.status}")
            except Exception as e:
                self.log_result("Gateway -> LangGraph Health", False, str(e))
            
            # Test 2: Workflow trigger
            try:
                workflow_data = {
                    "candidate_id": 1,
                    "job_id": 1,
                    "candidate_name": "Test User",
                    "candidate_email": "test@example.com",
                    "candidate_phone": "+1234567890",
                    "job_title": "Software Engineer"
                }
                
                async with session.post(f"{SERVICES['gateway']}/api/v1/workflow/trigger", 
                                      json=workflow_data, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        success = data.get('success', False)
                        workflow_id = data.get('workflow_id')
                        self.log_result("Workflow Trigger", success, 
                                      f"ID: {workflow_id}" if workflow_id else "No ID returned")
                        
                        # Test workflow status if we got an ID
                        if workflow_id:
                            await self.test_workflow_status(session, headers, workflow_id)
                    else:
                        self.log_result("Workflow Trigger", False, f"HTTP {resp.status}")
            except Exception as e:
                self.log_result("Workflow Trigger", False, str(e))
            
            # Test 3: Webhook endpoints
            webhook_tests = [
                ("candidate-applied", "Candidate Applied Webhook"),
                ("candidate-shortlisted", "Candidate Shortlisted Webhook"),
                ("interview-scheduled", "Interview Scheduled Webhook")
            ]
            
            for webhook, test_name in webhook_tests:
                try:
                    async with session.post(f"{SERVICES['gateway']}/api/v1/webhooks/{webhook}", 
                                          json=workflow_data, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            success = data.get('success', False)
                            self.log_result(test_name, success, 
                                          f"Status: {data.get('status', 'unknown')}")
                        else:
                            self.log_result(test_name, False, f"HTTP {resp.status}")
                except Exception as e:
                    self.log_result(test_name, False, str(e))
    
    async def test_workflow_status(self, session, headers, workflow_id):
        """Test workflow status endpoint"""
        try:
            await asyncio.sleep(1)  # Give workflow time to start
            async with session.get(f"{SERVICES['gateway']}/api/v1/workflow/status/{workflow_id}", 
                                 headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get('status', 'unknown')
                    self.log_result("Workflow Status", True, f"Status: {status}")
                else:
                    self.log_result("Workflow Status", False, f"HTTP {resp.status}")
        except Exception as e:
            self.log_result("Workflow Status", False, str(e))
    
    async def test_direct_langgraph(self):
        """Test LangGraph service directly"""
        print("\nTesting LangGraph Service Directly...")
        
        async with aiohttp.ClientSession() as session:
            # Test health
            try:
                async with session.get(f"{SERVICES['langgraph']}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log_result("LangGraph Direct Health", True, 
                                      f"Service: {data.get('service', 'unknown')}")
                    else:
                        self.log_result("LangGraph Direct Health", False, f"HTTP {resp.status}")
            except Exception as e:
                self.log_result("LangGraph Direct Health", False, str(e))
            
            # Test workflow start
            try:
                workflow_data = {
                    "candidate_id": 1,
                    "job_id": 1,
                    "application_id": 1,
                    "candidate_email": "test@example.com",
                    "candidate_phone": "+1234567890",
                    "candidate_name": "Test User",
                    "job_title": "Software Engineer"
                }
                
                async with session.post(f"{SERVICES['langgraph']}/workflows/application/start", 
                                      json=workflow_data) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        workflow_id = data.get('workflow_id')
                        self.log_result("LangGraph Direct Workflow", True, 
                                      f"ID: {workflow_id}")
                    else:
                        self.log_result("LangGraph Direct Workflow", False, f"HTTP {resp.status}")
            except Exception as e:
                self.log_result("LangGraph Direct Workflow", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\nNext Steps:")
        if failed_tests == 0:
            print("All tests passed! Ready for Render deployment.")
        else:
            print("Fix failed services before deployment:")
            print("   1. Check Docker containers: docker-compose ps")
            print("   2. View logs: docker-compose logs [service-name]")
            print("   3. Verify environment variables")

async def main():
    tester = IntegrationTester()
    
    print("BHIV HR Platform - Complete Integration Test")
    print("=" * 60)
    
    await tester.test_all_services()
    await tester.test_gateway_langgraph_integration()
    await tester.test_direct_langgraph()
    
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())