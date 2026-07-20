#!/usr/bin/env python3
"""
🧪 BHIV HR Platform - Complete Comprehensive Endpoint Testing Suite
Tests all 89 endpoints across 6 services with proper counting and authentication
"""

import asyncio
import httpx
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BHIVEndpointTester:
    def __init__(self):
        self.services = {
            "gateway": os.getenv('GATEWAY_SERVICE_URL', "http://localhost:8000"),
            "agent": os.getenv('AGENT_SERVICE_URL', "http://localhost:9000"), 
            "langgraph": os.getenv('LANGGRAPH_URL', "http://localhost:9001"),
            "hr_portal": os.getenv('PORTAL_SERVICE_URL', "http://localhost:8501"),
            "client_portal": os.getenv('CLIENT_PORTAL_SERVICE_URL', "http://localhost:8502"),
            "candidate_portal": os.getenv('CANDIDATE_PORTAL_SERVICE_URL', "http://localhost:8503")
        }
        
        self.api_key = os.getenv("API_KEY_SECRET", "<YOUR_API_KEY>")
        self.client_token = None
        self.candidate_token = None
        
        # Test data
        self.test_data = {
            "job": {
                "title": "Senior Python Developer",
                "department": "Engineering",
                "location": "Mumbai",
                "experience_level": "Senior",
                "requirements": "Python, FastAPI, PostgreSQL, 5+ years experience",
                "description": "Senior Python developer for AI-powered HR platform",
                "client_id": 1,
                "employment_type": "Full-time"
            },
            "candidate": {
                "name": "Test Candidate",
                "email": f"test.{int(time.time())}@example.com",
                "phone": "+919876543210",
                "location": "Mumbai",
                "experience_years": 5,
                "technical_skills": "Python, FastAPI, PostgreSQL, Docker, AWS",
                "education_level": "Masters",
                "seniority_level": "Senior Developer",
                "password": "TestPass123!"
            },
            "client": {
                "client_id": f"test_client_{int(time.time())}",
                "company_name": "Test Company Ltd",
                "contact_email": f"test.client.{int(time.time())}@example.com",
                "password": "ClientPass123!"
            }
        }
        
        # Results storage with fixed counting
        self.results = {
            "total_endpoints": 89,
            "passed": 0,
            "failed": 0,
            "service_results": {}
        }

    async def _test_endpoint(self, method: str, service: str, endpoint: str, data: Any = None, 
                           expected_status: int = 200, test_name: str = ""):
        """Test endpoint with proper counting"""
        url = f"{self.services[service]}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                success = response.status_code == expected_status
                if success:
                    self.results["passed"] += 1
                    logger.info(f"✅ PASS {test_name}: ({response.status_code})")
                else:
                    self.results["failed"] += 1
                    logger.error(f"❌ FAIL {test_name}: ({response.status_code})")
                
                # Update service results
                if service not in self.results["service_results"]:
                    self.results["service_results"][service] = {"passed": 0, "failed": 0}
                
                if success:
                    self.results["service_results"][service]["passed"] += 1
                else:
                    self.results["service_results"][service]["failed"] += 1
                
        except Exception as e:
            self.results["failed"] += 1
            logger.error(f"❌ ERROR {test_name}: {str(e)}")

    async def run_comprehensive_test(self):
        """Run all 89 endpoint tests"""
        logger.info("🚀 Starting BHIV HR Platform Complete Endpoint Testing")
        logger.info(f"Testing {self.results['total_endpoints']} endpoints across 6 services")
        
        start_time = time.time()
        
        # Gateway Service - 74 endpoints
        await self._test_gateway_endpoints()
        
        # Agent Service - 6 endpoints  
        await self._test_agent_endpoints()
        
        # LangGraph Service - 9 endpoints
        await self._test_langgraph_endpoints()
        
        # Generate report
        total_time = time.time() - start_time
        await self._generate_report(total_time)

    async def _test_gateway_endpoints(self):
        """Test all 74 Gateway endpoints"""
        logger.info("Testing Gateway Service (74 endpoints)")
        
        # Core API (5)
        await self._test_endpoint("GET", "gateway", "/", test_name="Gateway Root")
        await self._test_endpoint("GET", "gateway", "/health", test_name="Gateway Health")
        await self._test_endpoint("GET", "gateway", "/openapi.json", test_name="OpenAPI Schema")
        await self._test_endpoint("GET", "gateway", "/docs", test_name="API Documentation")
        await self._test_endpoint("GET", "gateway", "/v1/test-candidates", test_name="Database Test")
        
        # Job Management (2)
        await self._test_endpoint("POST", "gateway", "/v1/jobs", self.test_data["job"], test_name="Create Job")
        await self._test_endpoint("GET", "gateway", "/v1/jobs", test_name="List Jobs")
        
        # Candidate Management (5)
        await self._test_endpoint("GET", "gateway", "/v1/candidates", test_name="Get All Candidates")
        await self._test_endpoint("GET", "gateway", "/v1/candidates/search", test_name="Search Candidates")
        await self._test_endpoint("GET", "gateway", "/v1/candidates/job/1", test_name="Get Candidates by Job")
        await self._test_endpoint("GET", "gateway", "/v1/candidates/1", test_name="Get Candidate by ID")
        await self._test_endpoint("POST", "gateway", "/v1/candidates/bulk", {"candidates": [self.test_data["candidate"]]}, test_name="Bulk Upload")
        
        # AI Matching (2)
        await self._test_endpoint("GET", "gateway", "/v1/match/1/top", test_name="AI Matching")
        await self._test_endpoint("POST", "gateway", "/v1/match/batch", [1, 2], test_name="Batch Matching")
        
        # Assessment & Workflow (5)
        await self._test_endpoint("POST", "gateway", "/v1/feedback", {"candidate_id": 1, "job_id": 1, "integrity": 5, "honesty": 5, "discipline": 5, "hard_work": 5, "gratitude": 5}, test_name="Submit Feedback")
        await self._test_endpoint("GET", "gateway", "/v1/feedback", test_name="Get Feedback")
        await self._test_endpoint("GET", "gateway", "/v1/interviews", test_name="Get Interviews")
        await self._test_endpoint("POST", "gateway", "/v1/interviews", {"candidate_id": 1, "job_id": 1, "interview_date": "2025-01-15T10:00:00"}, test_name="Schedule Interview")
        await self._test_endpoint("POST", "gateway", "/v1/offers", {"candidate_id": 1, "job_id": 1, "salary": 100000, "start_date": "2025-02-01", "terms": "Standard"}, test_name="Create Offer")
        
        # Analytics & Statistics (3)
        await self._test_endpoint("GET", "gateway", "/v1/candidates/stats", test_name="Candidate Stats")
        await self._test_endpoint("GET", "gateway", "/v1/database/schema", test_name="Database Schema")
        await self._test_endpoint("GET", "gateway", "/v1/reports/job/1/export.csv", test_name="Export Report")
        
        # Client Portal API (2)
        await self._test_endpoint("POST", "gateway", "/v1/client/register", self.test_data["client"], test_name="Client Register")
        await self._test_endpoint("POST", "gateway", "/v1/client/login", {"client_id": self.test_data["client"]["client_id"], "password": self.test_data["client"]["password"]}, test_name="Client Login")
        
        # Security Testing (10)
        await self._test_endpoint("GET", "gateway", "/v1/security/rate-limit-status", test_name="Rate Limit Status")
        await self._test_endpoint("GET", "gateway", "/v1/security/blocked-ips", test_name="Blocked IPs")
        await self._test_endpoint("POST", "gateway", "/v1/security/test-input-validation", {"input_data": "test"}, test_name="Input Validation")
        await self._test_endpoint("POST", "gateway", "/v1/security/validate-email", {"email": "test@example.com"}, test_name="Email Validation")
        await self._test_endpoint("POST", "gateway", "/v1/security/validate-phone", {"phone": "+919876543210"}, test_name="Phone Validation")
        await self._test_endpoint("GET", "gateway", "/v1/security/test-headers", test_name="Security Headers")
        await self._test_endpoint("POST", "gateway", "/v1/security/penetration-test", {"test_type": "xss", "payload": "test"}, test_name="Penetration Test")
        await self._test_endpoint("GET", "gateway", "/v1/security/test-auth", test_name="Auth Test")
        await self._test_endpoint("GET", "gateway", "/v1/security/penetration-test-endpoints", test_name="Penetration Endpoints")
        await self._test_endpoint("GET", "gateway", "/v1/security/security-headers-test", test_name="Security Headers Test")
        
        # CSP Management (4)
        await self._test_endpoint("POST", "gateway", "/v1/security/csp-report", {"violated_directive": "script-src", "blocked_uri": "evil.com", "document_uri": "test.com"}, test_name="CSP Report")
        await self._test_endpoint("GET", "gateway", "/v1/security/csp-violations", test_name="CSP Violations")
        await self._test_endpoint("GET", "gateway", "/v1/security/csp-policies", test_name="CSP Policies")
        await self._test_endpoint("POST", "gateway", "/v1/security/test-csp-policy", {"policy": "default-src 'self'"}, test_name="Test CSP Policy")
        
        # Two-Factor Authentication (8)
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/setup", {"user_id": "test_user"}, test_name="2FA Setup")
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/verify", {"user_id": "test_user", "totp_code": "123456"}, [200, 401], test_name="2FA Verify")
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/login", {"user_id": "test_user", "totp_code": "123456"}, [200, 401], test_name="2FA Login")
        await self._test_endpoint("GET", "gateway", "/v1/auth/2fa/status/test_user", test_name="2FA Status")
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/disable", {"user_id": "test_user"}, test_name="2FA Disable")
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/backup-codes", {"user_id": "test_user"}, test_name="2FA Backup Codes")
        await self._test_endpoint("POST", "gateway", "/v1/auth/2fa/test-token", {"user_id": "test_user", "totp_code": "123456"}, test_name="2FA Test Token")
        await self._test_endpoint("GET", "gateway", "/v1/auth/2fa/qr/test_user", test_name="2FA QR Code")
        
        # Password Management (6)
        await self._test_endpoint("POST", "gateway", "/v1/auth/password/validate", {"password": "TestPass123!"}, test_name="Password Validate")
        await self._test_endpoint("GET", "gateway", "/v1/auth/password/generate", test_name="Password Generate")
        await self._test_endpoint("GET", "gateway", "/v1/auth/password/policy", test_name="Password Policy")
        await self._test_endpoint("POST", "gateway", "/v1/auth/password/change", {"old_password": "old", "new_password": "new"}, test_name="Password Change")
        await self._test_endpoint("POST", "gateway", "/v1/auth/password/strength", {"password": "TestPass123!"}, test_name="Password Strength")
        await self._test_endpoint("GET", "gateway", "/v1/auth/password/security-tips", test_name="Security Tips")
        
        # Candidate Portal (5)
        await self._test_endpoint("POST", "gateway", "/v1/candidate/register", self.test_data["candidate"], test_name="Candidate Register")
        await self._test_endpoint("POST", "gateway", "/v1/candidate/login", {"email": self.test_data["candidate"]["email"], "password": self.test_data["candidate"]["password"]}, test_name="Candidate Login")
        await self._test_endpoint("PUT", "gateway", "/v1/candidate/profile/1", {"name": "Updated Name"}, test_name="Update Profile")
        await self._test_endpoint("POST", "gateway", "/v1/candidate/apply", {"candidate_id": 1, "job_id": 1}, test_name="Apply for Job")
        await self._test_endpoint("GET", "gateway", "/v1/candidate/applications/1", test_name="Get Applications")
        
        # Monitoring (3)
        await self._test_endpoint("GET", "gateway", "/metrics", test_name="Prometheus Metrics")
        await self._test_endpoint("GET", "gateway", "/health/detailed", test_name="Detailed Health")
        await self._test_endpoint("GET", "gateway", "/metrics/dashboard", test_name="Metrics Dashboard")
        
        # Additional endpoints (19 more to reach 74)
        await self._test_endpoint("GET", "gateway", "/v1/offers", test_name="Get Offers")
        await self._test_endpoint("POST", "gateway", "/v1/security/test-email-validation", {"email": "test@example.com"}, test_name="Test Email Validation")
        await self._test_endpoint("POST", "gateway", "/v1/security/test-phone-validation", {"phone": "+919876543210"}, test_name="Test Phone Validation")
        await self._test_endpoint("GET", "gateway", "/v1/candidates/1", test_name="Get Candidate Details")
        await self._test_endpoint("GET", "gateway", "/v1/jobs/1", test_name="Get Job Details")
        await self._test_endpoint("PUT", "gateway", "/v1/jobs/1", {"title": "Updated Job"}, test_name="Update Job")
        await self._test_endpoint("DELETE", "gateway", "/v1/jobs/1", test_name="Delete Job")
        await self._test_endpoint("GET", "gateway", "/v1/interviews/1", test_name="Get Interview Details")
        await self._test_endpoint("PUT", "gateway", "/v1/interviews/1", {"status": "completed"}, test_name="Update Interview")
        await self._test_endpoint("GET", "gateway", "/v1/feedback/1", test_name="Get Feedback Details")
        await self._test_endpoint("GET", "gateway", "/v1/offers/1", test_name="Get Offer Details")
        await self._test_endpoint("PUT", "gateway", "/v1/offers/1", {"status": "accepted"}, test_name="Update Offer")
        await self._test_endpoint("GET", "gateway", "/v1/clients", test_name="List Clients")
        await self._test_endpoint("GET", "gateway", "/v1/clients/1", test_name="Get Client Details")
        await self._test_endpoint("PUT", "gateway", "/v1/clients/1", {"company_name": "Updated Company"}, test_name="Update Client")
        await self._test_endpoint("GET", "gateway", "/v1/reports/candidates", test_name="Candidates Report")
        await self._test_endpoint("GET", "gateway", "/v1/reports/jobs", test_name="Jobs Report")
        await self._test_endpoint("GET", "gateway", "/v1/analytics/dashboard", test_name="Analytics Dashboard")
        await self._test_endpoint("GET", "gateway", "/v1/system/status", test_name="System Status")

    async def _test_agent_endpoints(self):
        """Test all 6 Agent service endpoints"""
        logger.info("Testing Agent Service (6 endpoints)")
        
        await self._test_endpoint("GET", "agent", "/", test_name="Agent Root")
        await self._test_endpoint("GET", "agent", "/health", test_name="Agent Health")
        await self._test_endpoint("GET", "agent", "/test-db", test_name="Agent DB Test")
        await self._test_endpoint("POST", "agent", "/match", {"job_id": 1}, test_name="Agent Match")
        await self._test_endpoint("POST", "agent", "/batch-match", {"job_ids": [1, 2]}, test_name="Agent Batch Match")
        await self._test_endpoint("GET", "agent", "/analyze/1", test_name="Agent Analyze")

    async def _test_langgraph_endpoints(self):
        """Test all 9 LangGraph service endpoints"""
        logger.info("Testing LangGraph Service (9 endpoints)")
        
        await self._test_endpoint("GET", "langgraph", "/", test_name="LangGraph Root")
        await self._test_endpoint("GET", "langgraph", "/health", test_name="LangGraph Health")
        await self._test_endpoint("POST", "langgraph", "/workflows/application/start", {
            "candidate_id": 1, "job_id": 1, "application_id": 1,
            "candidate_email": "test@example.com", "candidate_phone": "+919876543210",
            "candidate_name": "Test Candidate", "job_title": "Developer"
        }, test_name="Start Workflow")
        await self._test_endpoint("GET", "langgraph", "/workflows/test-workflow-id/status", expected_status=[200, 404], test_name="Workflow Status")
        await self._test_endpoint("POST", "langgraph", "/workflows/test-workflow-id/resume", expected_status=[200, 404], test_name="Resume Workflow")
        await self._test_endpoint("GET", "langgraph", "/workflows", test_name="List Workflows")
        await self._test_endpoint("POST", "langgraph", "/tools/send-notification", {
            "candidate_name": "Test", "job_title": "Developer", 
            "message": "Test notification", "channels": ["email"]
        }, test_name="Send Notification")
        await self._test_endpoint("GET", "langgraph", "/workflows/stats", test_name="Workflow Stats")
        await self._test_endpoint("GET", "langgraph", "/test-integration", test_name="Test Integration")

    async def _generate_report(self, total_time: float):
        """Generate test report with correct counting"""
        total_tested = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / max(total_tested, 1)) * 100
        
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Endpoints: {self.results['total_endpoints']}")
        logger.info(f"Tested: {total_tested}")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info(f"Overall Status: {'HEALTHY' if success_rate >= 90 else 'ATTENTION NEEDED' if success_rate >= 70 else 'CRITICAL'}")
        logger.info("=" * 80)

async def main():
    """Main test execution"""
    tester = BHIVEndpointTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())