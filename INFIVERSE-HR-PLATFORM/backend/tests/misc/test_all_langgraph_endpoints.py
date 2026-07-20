#!/usr/bin/env python3
"""
Comprehensive LangGraph Endpoints Test
Test all 9 endpoints with proper inputs and outputs
"""

import httpx
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

class LangGraphTester:
    def __init__(self):
        self.base_url = "http://localhost:9001"  # Test on localhost
        self.api_key = os.getenv("API_KEY_SECRET")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.results = {}
    
    async def test_endpoint(self, method, endpoint, data=None, description=""):
        """Test individual endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}", headers=self.headers, timeout=30.0)
                elif method == "POST":
                    response = await client.post(f"{self.base_url}{endpoint}", json=data, headers=self.headers, timeout=30.0)
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 201],
                    "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    "description": description
                }
                
                print(f"{method} {endpoint}: {response.status_code} - {description}")
                if result["success"]:
                    print(f"  SUCCESS: {json.dumps(result['response'], indent=2)[:200]}...")
                else:
                    print(f"  ERROR: {result['response']}")
                
                return result
                
        except Exception as e:
            result = {
                "status_code": 0,
                "success": False,
                "response": str(e),
                "description": description
            }
            print(f"{method} {endpoint}: ERROR - {str(e)}")
            return result
    
    async def run_all_tests(self):
        """Test all LangGraph endpoints"""
        
        print("=== TESTING ALL LANGGRAPH ENDPOINTS ===\n")
        
        # 1. GET / - Service Info
        self.results["service_info"] = await self.test_endpoint(
            "GET", "/", 
            description="Service information and status"
        )
        
        # 2. GET /health - Health Check
        self.results["health"] = await self.test_endpoint(
            "GET", "/health",
            description="Health check and monitoring"
        )
        
        # 3. POST /tools/send-notification - Multi-channel Notification
        notification_data = {
            "candidate_name": "John Doe",
            "candidate_email": "john.doe@example.com",
            "candidate_phone": "+919284967526",
            "job_title": "Software Engineer",
            "message": "Your application has been received and is under review.",
            "channels": ["email", "whatsapp"],
            "application_status": "received"
        }
        self.results["send_notification"] = await self.test_endpoint(
            "POST", "/tools/send-notification", notification_data,
            description="Multi-channel notification (Email + WhatsApp)"
        )
        
        # 4. POST /workflows/application/start - Start AI Workflow
        workflow_data = {
            "candidate_id": 1,
            "job_id": 1,
            "application_id": 1001,
            "candidate_email": "jane.smith@example.com",
            "candidate_phone": "+919284967526",
            "candidate_name": "Jane Smith",
            "job_title": "Data Scientist",
            "job_description": "AI/ML role with Python and TensorFlow experience required"
        }
        self.results["start_workflow"] = await self.test_endpoint(
            "POST", "/workflows/application/start", workflow_data,
            description="Start AI workflow for candidate processing"
        )
        
        # Wait for workflow to start
        await asyncio.sleep(2)
        
        # 5. GET /workflows - List Workflows
        self.results["list_workflows"] = await self.test_endpoint(
            "GET", "/workflows",
            description="List all workflows with status"
        )
        
        # 6. GET /workflows/stats - Workflow Statistics
        self.results["workflow_stats"] = await self.test_endpoint(
            "GET", "/workflows/stats",
            description="Workflow statistics and analytics"
        )
        
        # Get workflow ID from start_workflow result for status check
        workflow_id = None
        if self.results["start_workflow"]["success"]:
            workflow_id = self.results["start_workflow"]["response"].get("workflow_id")
        
        # 7. GET /workflows/{id}/status - Workflow Status
        if workflow_id:
            self.results["workflow_status"] = await self.test_endpoint(
                "GET", f"/workflows/{workflow_id}/status",
                description=f"Get status of workflow {workflow_id}"
            )
        else:
            # Use dummy ID for testing
            self.results["workflow_status"] = await self.test_endpoint(
                "GET", "/workflows/test-workflow-123/status",
                description="Get workflow status (test ID)"
            )
        
        # 8. POST /workflows/{id}/resume - Resume Workflow
        if workflow_id:
            self.results["resume_workflow"] = await self.test_endpoint(
                "POST", f"/workflows/{workflow_id}/resume",
                description=f"Resume workflow {workflow_id}"
            )
        else:
            self.results["resume_workflow"] = await self.test_endpoint(
                "POST", "/workflows/test-workflow-123/resume",
                description="Resume workflow (test ID)"
            )
        
        # 9. GET /test-integration - Integration Test
        self.results["test_integration"] = await self.test_endpoint(
            "GET", "/test-integration",
            description="Integration testing and system validation"
        )
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n=== TEST SUMMARY ===")
        
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results.values() if r["success"]])
        
        print(f"Total Endpoints Tested: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        for endpoint, result in self.results.items():
            status = "PASS" if result["success"] else "FAIL"
            print(f"  {endpoint}: {status} ({result['status_code']}) - {result['description']}")
        
        # Key functionality check
        print(f"\nKEY FUNCTIONALITY:")
        comm_working = self.results.get("send_notification", {}).get("success", False)
        workflow_working = self.results.get("start_workflow", {}).get("success", False)
        health_working = self.results.get("health", {}).get("success", False)
        
        print(f"  Communication System: {'WORKING' if comm_working else 'FAILED'}")
        print(f"  AI Workflow System: {'WORKING' if workflow_working else 'FAILED'}")
        print(f"  Health Monitoring: {'WORKING' if health_working else 'FAILED'}")

async def main():
    """Run comprehensive LangGraph endpoint tests"""
    tester = LangGraphTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())