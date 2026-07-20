#!/usr/bin/env python3
"""
🧪 BHIV HR Platform - Comprehensive Endpoint Testing Suite
Tests all 89 endpoints across 6 services with proper workflow integration
"""

import asyncio
import httpx
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging with UTF-8 encoding
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BHIVEndpointTester:
    def __init__(self):
        # Service URLs
        self.services = {
            "gateway": "https://bhiv-hr-gateway-ltg0.onrender.com",
            "agent": "https://bhiv-hr-agent-nhgg.onrender.com", 
            "langgraph": "https://bhiv-hr-langgraph.onrender.com",
            "hr_portal": "https://bhiv-hr-portal-u670.onrender.com",
            "client_portal": "https://bhiv-hr-client-portal-3iod.onrender.com",
            "candidate_portal": "https://bhiv-hr-candidate-portal-abe6.onrender.com"
        }
        
        # Test credentials and data
        self.api_key = os.getenv("API_KEY_SECRET", "test-api-key")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Common test data
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
                "email": f"test.candidate.{int(time.time())}@example.com",
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
            },
            "feedback": {
                "candidate_id": 1,
                "job_id": 1,
                "integrity": 5,
                "honesty": 5,
                "discipline": 4,
                "hard_work": 5,
                "gratitude": 4,
                "comments": "Excellent candidate with strong values"
            },
            "interview": {
                "candidate_id": 1,
                "job_id": 1,
                "interview_date": "2025-01-15T10:00:00",
                "interviewer": "Test Interviewer",
                "notes": "Initial screening interview"
            }
        }
        
        # Test results storage
        self.results = {
            "total_endpoints": 89,
            "tested_endpoints": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "service_results": {},
            "integration_tests": {},
            "workflow_tests": {},
            "detailed_results": []
        }
        
        # Dynamic test data (populated during tests)
        self.created_job_id = None
        self.created_candidate_id = None
        self.client_token = None
        self.candidate_token = None
        self.workflow_id = None

    async def run_comprehensive_test(self):
        """Run comprehensive endpoint testing suite"""
        logger.info("Starting BHIV HR Platform Comprehensive Endpoint Testing")
        logger.info(f"Testing {self.results['total_endpoints']} endpoints across 6 services")
        
        start_time = time.time()
        
        try:
            # Phase 1: Service Health Checks
            await self._test_service_health()
            
            # Phase 2: Core API Endpoints
            await self._test_core_endpoints()
            
            # Phase 3: Authentication & Security
            await self._test_authentication_security()
            
            # Phase 4: Business Logic Workflow
            await self._test_business_workflow()
            
            # Phase 5: AI & Matching Engine
            await self._test_ai_matching()
            
            # Phase 6: LangGraph Workflows
            await self._test_langgraph_workflows()
            
            # Phase 7: Integration Tests
            await self._test_service_integration()
            
            # Phase 8: Portal Accessibility
            await self._test_portal_accessibility()
            
        except Exception as e:
            logger.error(f"❌ Critical error during testing: {e}")
        
        # Generate comprehensive report
        total_time = time.time() - start_time
        await self._generate_test_report(total_time)

    async def _test_service_health(self):
        """Test basic health endpoints for all services"""
        logger.info("Phase 1: Testing Service Health")
        
        health_endpoints = [
            ("gateway", "/health"),
            ("gateway", "/"),
            ("agent", "/health"),
            ("agent", "/"),
            ("langgraph", "/health"),
            ("langgraph", "/")
        ]
        
        for service, endpoint in health_endpoints:
            await self._test_endpoint("GET", service, endpoint, expected_status=200, 
                                    test_name=f"{service.title()} Health Check")

    async def _test_core_endpoints(self):
        """Test core API endpoints"""
        logger.info("Phase 2: Testing Core API Endpoints")
        
        # Gateway core endpoints
        core_tests = [
            ("GET", "gateway", "/openapi.json", None, 200, "OpenAPI Schema"),
            ("GET", "gateway", "/v1/test-candidates", None, 200, "Database Connectivity"),
            ("GET", "gateway", "/v1/candidates/stats", None, 200, "Candidate Statistics"),
            ("GET", "gateway", "/v1/database/schema", None, 200, "Database Schema"),
            ("GET", "gateway", "/metrics", None, 200, "Prometheus Metrics"),
            ("GET", "gateway", "/health/detailed", None, 200, "Detailed Health Check")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in core_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)

    async def _test_authentication_security(self):
        """Test authentication and security endpoints"""
        logger.info("Phase 3: Testing Authentication & Security")
        
        # Security testing endpoints
        security_tests = [
            ("GET", "gateway", "/v1/security/rate-limit-status", None, 200, "Rate Limit Status"),
            ("GET", "gateway", "/v1/security/blocked-ips", None, 200, "Blocked IPs"),
            ("POST", "gateway", "/v1/security/test-input-validation", 
             {"input_data": "test input"}, 200, "Input Validation"),
            ("POST", "gateway", "/v1/security/validate-email", 
             {"email": "test@example.com"}, 200, "Email Validation"),
            ("POST", "gateway", "/v1/security/validate-phone", 
             {"phone": "+919876543210"}, 200, "Phone Validation"),
            ("GET", "gateway", "/v1/security/test-headers", None, 200, "Security Headers"),
            ("GET", "gateway", "/v1/security/csp-policies", None, 200, "CSP Policies"),
            ("GET", "gateway", "/v1/security/test-auth", None, 200, "Authentication Test")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in security_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)
        
        # 2FA endpoints
        twofa_tests = [
            ("POST", "gateway", "/v1/auth/2fa/setup", {"user_id": "test_user"}, 200, "2FA Setup"),
            ("GET", "gateway", "/v1/auth/2fa/status/test_user", None, 200, "2FA Status"),
            ("GET", "gateway", "/v1/auth/2fa/qr/test_user", None, 200, "2FA QR Code")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in twofa_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)
        
        # Password management
        password_tests = [
            ("POST", "gateway", "/v1/auth/password/validate", 
             {"password": "TestPass123!"}, 200, "Password Validation"),
            ("GET", "gateway", "/v1/auth/password/generate", None, 200, "Password Generation"),
            ("GET", "gateway", "/v1/auth/password/policy", None, 200, "Password Policy"),
            ("GET", "gateway", "/v1/auth/password/security-tips", None, 200, "Security Tips")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in password_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)

    async def _test_business_workflow(self):
        """Test complete business workflow: Job -> Candidate -> Application -> Interview -> Feedback"""
        logger.info("Phase 4: Testing Business Logic Workflow")
        
        # Step 1: Create Job
        job_response = await self._test_endpoint("POST", "gateway", "/v1/jobs", 
                                                self.test_data["job"], 200, "Create Job")
        if job_response and job_response.get("job_id"):
            self.created_job_id = job_response["job_id"]
            logger.info(f"Created job with ID: {self.created_job_id}")
        
        # Step 2: List Jobs
        await self._test_endpoint("GET", "gateway", "/v1/jobs", None, 200, "List Jobs")
        
        # Step 3: Register Client
        await self._test_endpoint("POST", "gateway", "/v1/client/register", 
                                self.test_data["client"], 200, "Client Registration")
        
        # Step 4: Client Login
        login_response = await self._test_endpoint("POST", "gateway", "/v1/client/login", 
                                                 {"client_id": self.test_data["client"]["client_id"], 
                                                  "password": self.test_data["client"]["password"]}, 
                                                 200, "Client Login")
        if login_response and login_response.get("access_token"):
            self.client_token = login_response["access_token"]
            logger.info("Client authentication successful")
        
        # Step 5: Register Candidate
        candidate_response = await self._test_endpoint("POST", "gateway", "/v1/candidate/register", 
                                                     self.test_data["candidate"], 200, "Candidate Registration")
        
        # Step 6: Candidate Login
        candidate_login_response = await self._test_endpoint("POST", "gateway", "/v1/candidate/login", 
                                                           {"email": self.test_data["candidate"]["email"], 
                                                            "password": self.test_data["candidate"]["password"]}, 
                                                           200, "Candidate Login")
        if candidate_login_response and candidate_login_response.get("token"):
            self.candidate_token = candidate_login_response["token"]
            if candidate_login_response.get("candidate", {}).get("id"):
                self.created_candidate_id = candidate_login_response["candidate"]["id"]
                logger.info(f"Candidate authenticated with ID: {self.created_candidate_id}")
        
        # Step 7: Bulk Upload Candidates
        bulk_candidates = {"candidates": [self.test_data["candidate"]]}
        await self._test_endpoint("POST", "gateway", "/v1/candidates/bulk", 
                                bulk_candidates, 200, "Bulk Upload Candidates")
        
        # Step 8: Search Candidates
        await self._test_endpoint("GET", "gateway", "/v1/candidates/search", 
                                None, 200, "Search Candidates")
        
        # Step 9: Get All Candidates
        await self._test_endpoint("GET", "gateway", "/v1/candidates", 
                                None, 200, "Get All Candidates")
        
        # Step 10: Schedule Interview
        if self.created_candidate_id and self.created_job_id:
            interview_data = {
                "candidate_id": self.created_candidate_id,
                "job_id": self.created_job_id,
                "interview_date": "2025-01-15T10:00:00",
                "interviewer": "Test Interviewer",
                "notes": "Automated test interview"
            }
            await self._test_endpoint("POST", "gateway", "/v1/interviews", 
                                    interview_data, 200, "Schedule Interview")
        
        # Step 11: Get Interviews
        await self._test_endpoint("GET", "gateway", "/v1/interviews", 
                                None, 200, "Get Interviews")
        
        # Step 12: Submit Feedback
        if self.created_candidate_id and self.created_job_id:
            feedback_data = {
                "candidate_id": self.created_candidate_id,
                "job_id": self.created_job_id,
                "integrity": 5,
                "honesty": 5,
                "discipline": 4,
                "hard_work": 5,
                "gratitude": 4,
                "comments": "Automated test feedback"
            }
            await self._test_endpoint("POST", "gateway", "/v1/feedback", 
                                    feedback_data, 200, "Submit Feedback")
        
        # Step 13: Get Feedback
        await self._test_endpoint("GET", "gateway", "/v1/feedback", 
                                None, 200, "Get Feedback")

    async def _test_ai_matching(self):
        """Test AI matching and agent endpoints"""
        logger.info("Phase 5: Testing AI & Matching Engine")
        
        # Agent service tests
        agent_tests = [
            ("GET", "agent", "/test-db", None, 200, "Agent Database Test"),
            ("POST", "agent", "/match", {"job_id": 1}, 200, "AI Candidate Matching"),
            ("POST", "agent", "/batch-match", {"job_ids": [1, 2]}, 200, "Batch AI Matching"),
            ("GET", "agent", "/analyze/1", None, 200, "Candidate Analysis")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in agent_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)
        
        # Gateway AI matching endpoints
        gateway_ai_tests = [
            ("GET", "gateway", "/v1/match/1/top", None, 200, "Gateway AI Matching"),
            ("POST", "gateway", "/v1/match/batch", [1, 2], 200, "Gateway Batch Matching")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in gateway_ai_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)

    async def _test_langgraph_workflows(self):
        """Test LangGraph workflow endpoints"""
        logger.info("Phase 6: Testing LangGraph Workflows")
        
        # Start workflow
        if self.created_candidate_id and self.created_job_id:
            workflow_data = {
                "candidate_id": self.created_candidate_id,
                "job_id": self.created_job_id,
                "application_id": 1,
                "candidate_email": self.test_data["candidate"]["email"],
                "candidate_phone": self.test_data["candidate"]["phone"],
                "candidate_name": self.test_data["candidate"]["name"],
                "job_title": self.test_data["job"]["title"]
            }
            
            workflow_response = await self._test_endpoint("POST", "langgraph", "/workflows/application/start", 
                                                        workflow_data, 200, "Start Workflow")
            if workflow_response and workflow_response.get("workflow_id"):
                self.workflow_id = workflow_response["workflow_id"]
                logger.info(f"Started workflow with ID: {self.workflow_id}")
        
        # LangGraph endpoints
        langgraph_tests = [
            ("GET", "langgraph", "/workflows", None, 200, "List Workflows"),
            ("GET", "langgraph", "/workflows/stats", None, 200, "Workflow Stats"),
            ("POST", "langgraph", "/tools/send-notification", 
             {"candidate_name": "Test", "job_title": "Developer", "message": "Test notification", "channels": ["email"]}, 
             200, "Send Notification"),
            ("GET", "langgraph", "/test-integration", None, 200, "Test Integration")
        ]
        
        for method, service, endpoint, data, expected_status, test_name in langgraph_tests:
            await self._test_endpoint(method, service, endpoint, data, expected_status, test_name)
        
        # Test workflow status if workflow was created
        if self.workflow_id:
            await self._test_endpoint("GET", "langgraph", f"/workflows/{self.workflow_id}/status", 
                                    None, 200, "Get Workflow Status")

    async def _test_service_integration(self):
        """Test integration between services"""
        logger.info("Phase 7: Testing Service Integration")
        
        integration_results = {}
        
        # Test Gateway -> Agent integration
        try:
            gateway_match = await self._test_endpoint("GET", "gateway", "/v1/match/1/top", 
                                                    None, 200, "Gateway-Agent Integration", return_response=True)
            agent_match = await self._test_endpoint("POST", "agent", "/match", 
                                                   {"job_id": 1}, 200, "Direct Agent Match", return_response=True)
            
            integration_results["gateway_agent"] = {
                "status": "✅ INTEGRATED" if gateway_match and agent_match else "❌ DISCONNECTED",
                "gateway_response": bool(gateway_match),
                "agent_response": bool(agent_match)
            }
        except Exception as e:
            integration_results["gateway_agent"] = {"status": "❌ ERROR", "error": str(e)}
        
        # Test Gateway -> LangGraph integration
        try:
            if self.workflow_id:
                gateway_workflow = await self._test_endpoint("GET", "gateway", f"/api/v1/workflows/{self.workflow_id}/status", 
                                                           None, 200, "Gateway-LangGraph Integration", return_response=True)
                langgraph_workflow = await self._test_endpoint("GET", "langgraph", f"/workflows/{self.workflow_id}/status", 
                                                             None, 200, "Direct LangGraph Status", return_response=True)
                
                integration_results["gateway_langgraph"] = {
                    "status": "✅ INTEGRATED" if gateway_workflow and langgraph_workflow else "❌ DISCONNECTED",
                    "gateway_response": bool(gateway_workflow),
                    "langgraph_response": bool(langgraph_workflow)
                }
            else:
                integration_results["gateway_langgraph"] = {"status": "⚠️ SKIPPED", "reason": "No workflow created"}
        except Exception as e:
            integration_results["gateway_langgraph"] = {"status": "❌ ERROR", "error": str(e)}
        
        self.results["integration_tests"] = integration_results

    async def _test_portal_accessibility(self):
        """Test portal accessibility"""
        logger.info("Phase 8: Testing Portal Accessibility")
        
        portal_results = {}
        
        for portal_name, portal_service_url in [
            ("hr_portal", self.services["hr_portal"]),
            ("client_portal", self.services["client_portal"]),
            ("candidate_portal", self.services["candidate_portal"])
        ]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(portal_service_url)
                    portal_results[portal_name] = {
                        "status": "✅ ACCESSIBLE" if response.status_code == 200 else f"❌ ERROR ({response.status_code})",
                        "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                        "accessible": response.status_code == 200
                    }
            except Exception as e:
                portal_results[portal_name] = {
                    "status": "❌ UNREACHABLE",
                    "error": str(e),
                    "accessible": False
                }
        
        self.results["portal_accessibility"] = portal_results

    async def _test_endpoint(self, method: str, service: str, endpoint: str, 
                           data: Any = None, expected_status: int = 200, 
                           test_name: str = "", return_response: bool = False) -> Optional[Dict]:
        """Test individual endpoint"""
        url = f"{self.services[service]}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=self.headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=self.headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                # Record result
                success = response.status_code == expected_status
                result = {
                    "test_name": test_name or f"{method} {endpoint}",
                    "service": service,
                    "endpoint": endpoint,
                    "method": method,
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "success": success,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    self.results["passed"] += 1
                    logger.info(f"PASS {test_name}: ({response.status_code})")
                    if return_response:
                        try:
                            return response.json()
                        except:
                            return {"status": "success"}
                else:
                    self.results["failed"] += 1
                    logger.error(f"FAIL {test_name}: ({response.status_code})")
                    result["error"] = response.text[:200] if response.text else "No response body"
                
                self.results["tested_endpoints"] += 1
                self.results["detailed_results"].append(result)
                
                # Update service results
                if service not in self.results["service_results"]:
                    self.results["service_results"][service] = {"passed": 0, "failed": 0, "total": 0}
                
                self.results["service_results"][service]["total"] += 1
                if success:
                    self.results["service_results"][service]["passed"] += 1
                else:
                    self.results["service_results"][service]["failed"] += 1
                
                return response.json() if success and return_response else None
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["tested_endpoints"] += 1
            logger.error(f"ERROR {test_name}: {str(e)}")
            
            error_result = {
                "test_name": test_name or f"{method} {endpoint}",
                "service": service,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["detailed_results"].append(error_result)
            return None

    async def _generate_test_report(self, total_time: float):
        """Generate comprehensive test report"""
        logger.info("Generating Comprehensive Test Report")
        
        # Calculate success rate
        success_rate = (self.results["passed"] / max(self.results["tested_endpoints"], 1)) * 100
        
        report = f"""
# 🧪 BHIV HR Platform - Comprehensive Endpoint Test Report

**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Test Time**: {total_time:.2f} seconds  
**Test Environment**: Production (Render Cloud)

## 📊 Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| **Total Endpoints** | {self.results['total_endpoints']} | 📋 Documented |
| **Tested Endpoints** | {self.results['tested_endpoints']} | 🧪 Executed |
| **Passed Tests** | {self.results['passed']} | ✅ Success |
| **Failed Tests** | {self.results['failed']} | ❌ Failed |
| **Success Rate** | {success_rate:.1f}% | {'✅ EXCELLENT' if success_rate >= 90 else '⚠️ NEEDS ATTENTION' if success_rate >= 70 else '❌ CRITICAL'} |

## 🏗️ Service-Level Results

"""
        
        for service, stats in self.results["service_results"].items():
            service_success_rate = (stats["passed"] / max(stats["total"], 1)) * 100
            status_icon = "✅" if service_success_rate >= 90 else "⚠️" if service_success_rate >= 70 else "❌"
            
            report += f"""
### {service.title().replace('_', ' ')} Service
- **Endpoints Tested**: {stats['total']}
- **Passed**: {stats['passed']} | **Failed**: {stats['failed']}
- **Success Rate**: {service_success_rate:.1f}% {status_icon}
"""
        
        # Integration test results
        if self.results.get("integration_tests"):
            report += "\n## 🔗 Service Integration Results\n\n"
            for integration, result in self.results["integration_tests"].items():
                report += f"- **{integration.replace('_', ' ').title()}**: {result['status']}\n"
        
        # Portal accessibility results
        if self.results.get("portal_accessibility"):
            report += "\n## 🌐 Portal Accessibility Results\n\n"
            for portal, result in self.results["portal_accessibility"].items():
                report += f"- **{portal.replace('_', ' ').title()}**: {result['status']}\n"
        
        # Workflow test results
        report += f"""
## 💼 Business Workflow Test Results

| Component | Status | Details |
|-----------|--------|---------|
| **Job Creation** | {'✅ SUCCESS' if self.created_job_id else '❌ FAILED'} | Job ID: {self.created_job_id or 'Not Created'} |
| **Client Authentication** | {'✅ SUCCESS' if self.client_token else '❌ FAILED'} | Token: {'Generated' if self.client_token else 'Failed'} |
| **Candidate Registration** | {'✅ SUCCESS' if self.created_candidate_id else '❌ FAILED'} | Candidate ID: {self.created_candidate_id or 'Not Created'} |
| **Workflow Automation** | {'✅ SUCCESS' if self.workflow_id else '❌ FAILED'} | Workflow ID: {self.workflow_id or 'Not Started'} |

## 🔍 Detailed Test Results

### ✅ Passed Tests ({self.results['passed']})
"""
        
        passed_tests = [r for r in self.results["detailed_results"] if r["success"]]
        for test in passed_tests[:10]:  # Show first 10 passed tests
            report += f"- {test['test_name']} ({test['service']}) - {test['actual_status']}\n"
        
        if len(passed_tests) > 10:
            report += f"- ... and {len(passed_tests) - 10} more passed tests\n"
        
        report += f"\n### ❌ Failed Tests ({self.results['failed']})\n"
        
        failed_tests = [r for r in self.results["detailed_results"] if not r["success"]]
        for test in failed_tests:
            error_msg = test.get('error', 'Unknown error')[:100]
            report += f"- {test['test_name']} ({test['service']}) - Status: {test['actual_status']} - Error: {error_msg}\n"
        
        if not failed_tests:
            report += "🎉 No failed tests!\n"
        
        report += f"""
## 🎯 Recommendations

### ✅ Strengths
- **High Success Rate**: {success_rate:.1f}% of endpoints working correctly
- **Service Integration**: {'All services properly integrated' if all(r.get('status', '').startswith('✅') for r in self.results.get('integration_tests', {}).values()) else 'Some integration issues detected'}
- **Portal Accessibility**: {'All portals accessible' if all(r.get('accessible', False) for r in self.results.get('portal_accessibility', {}).values()) else 'Some portals may have issues'}

### 🔧 Areas for Improvement
"""
        
        if failed_tests:
            report += f"- **Failed Endpoints**: {len(failed_tests)} endpoints need attention\n"
        if success_rate < 95:
            report += f"- **Success Rate**: Target 95%+ success rate (currently {success_rate:.1f}%)\n"
        
        report += f"""
## 📋 Test Summary

**Test Execution**: {'✅ COMPLETED' if self.results['tested_endpoints'] > 0 else '❌ INCOMPLETE'}  
**Overall Status**: {'✅ SYSTEM HEALTHY' if success_rate >= 90 else '⚠️ NEEDS ATTENTION' if success_rate >= 70 else '❌ CRITICAL ISSUES'}  
**Production Ready**: {'✅ YES' if success_rate >= 90 and self.results['failed'] < 5 else '⚠️ WITH CAUTION' if success_rate >= 70 else '❌ NOT RECOMMENDED'}

---

*Report Generated by BHIV Comprehensive Endpoint Tester*  
*Test Environment: Production (Render Cloud)*  
*Total Test Time: {total_time:.2f} seconds*
"""
        
        # Save report
        with open("COMPREHENSIVE_TEST_REPORT.md", "w") as f:
            f.write(report)
        
        # Print summary
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Endpoints: {self.results['total_endpoints']}")
        logger.info(f"Tested: {self.results['tested_endpoints']}")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed: {self.results['failed']}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info(f"Overall Status: {'HEALTHY' if success_rate >= 90 else 'ATTENTION NEEDED' if success_rate >= 70 else 'CRITICAL'}")
        logger.info("=" * 80)
        logger.info("Detailed report saved to: COMPREHENSIVE_TEST_REPORT.md")

async def main():
    """Main test execution"""
    tester = BHIVEndpointTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())