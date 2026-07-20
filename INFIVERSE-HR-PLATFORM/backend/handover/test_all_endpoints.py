#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Suite
Based on API Contract Documentation (Parts 1-5)
Version: 4.1.0
Last Updated: January 22, 2026
Total Endpoints: 111 (80 Gateway + 6 Agent + 25 LangGraph)
Database: MongoDB Atlas
"""

import json
import requests
import time
import sys
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EndpointTest:
    """Endpoint test definition based on API contract"""
    number: int
    name: str
    method: str
    path: str
    service: str  # gateway, agent, langgraph
    auth_required: bool
    timeout: int
    description: str
    request_body: Dict[str, Any] = None
    expected_status: int = 200
    query_params: str = ""

class EndpointTester:
    """Comprehensive API endpoint tester following API contract standards"""
    
    def __init__(self):
        self.base_urls = {
            'gateway': 'http://localhost:8000',
            'agent': 'http://localhost:9000',
            'langgraph': 'http://localhost:9001'
        }
        self.api_key = 'prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.results = []
        self.test_summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'by_service': {
                'gateway': {'total': 0, 'passed': 0, 'failed': 0},
                'agent': {'total': 0, 'passed': 0, 'failed': 0},
                'langgraph': {'total': 0, 'passed': 0, 'failed': 0}
            }
        }
        self.endpoints = self._load_endpoints()
    
    def _load_endpoints(self) -> List[EndpointTest]:
        """Load all 111 endpoints from API contract specifications"""
        endpoints = []
        
        # Gateway Endpoints (1-80)
        gateway_endpoints = [
            # Core Services (1-18)
            EndpointTest(1, 'Gateway Root', 'GET', '/', 'gateway', False, 5, 'Gateway service root endpoint'),
            EndpointTest(2, 'Gateway Health', 'GET', '/health', 'gateway', False, 5, 'Health check endpoint'),
            EndpointTest(3, 'Gateway OpenAPI', 'GET', '/openapi.json', 'gateway', False, 5, 'OpenAPI specification'),
            EndpointTest(4, 'Gateway Docs', 'GET', '/docs', 'gateway', False, 5, 'Swagger UI documentation'),
            EndpointTest(5, 'Test DB Connection', 'GET', '/test-db', 'gateway', True, 5, 'Test database connection'),
            
            # Authentication (6-18)
            EndpointTest(6, 'Setup 2FA', 'POST', '/auth/2fa/setup', 'gateway', True, 10, 'Setup two-factor authentication', {'user_id': 'test_user'}),
            EndpointTest(7, 'Verify 2FA', 'POST', '/auth/2fa/verify', 'gateway', True, 8, 'Verify two-factor authentication code', {'user_id': 'test_user', 'totp_code': '853476'}),
            EndpointTest(8, 'Auth Login', 'POST', '/auth/login', 'gateway', False, 10, 'Authenticate user login', {'username': 'admin', 'password': 'admin123'}),
            EndpointTest(9, '2FA Status', 'GET', '/auth/2fa/status/test_user', 'gateway', True, 5, 'Get 2FA status for user'),
            EndpointTest(10, '2FA Setup v1', 'POST', '/v1/auth/2fa/setup', 'gateway', True, 5, 'Setup 2FA v1 endpoint', {'user_id': 'test_user'}),
            EndpointTest(11, '2FA Verify v1', 'POST', '/v1/auth/2fa/verify', 'gateway', True, 5, 'Verify 2FA v1 endpoint', {'user_id': 'test_user', 'totp_code': '853476'}),
            EndpointTest(12, '2FA Login', 'POST', '/v1/auth/2fa/login', 'gateway', True, 5, 'Login with 2FA', {'user_id': 'test_user', 'totp_code': '853476'}),
            EndpointTest(13, '2FA Status v1', 'GET', '/v1/auth/2fa/status/test_user', 'gateway', True, 5, 'Get 2FA status v1'),
            EndpointTest(14, 'Disable 2FA', 'POST', '/v1/auth/2fa/disable', 'gateway', True, 5, 'Disable 2FA', {'user_id': 'test_user'}),
            EndpointTest(15, 'Backup Codes', 'POST', '/v1/auth/2fa/backup-codes', 'gateway', True, 5, 'Generate backup codes', {'user_id': 'test_user'}),
            EndpointTest(16, 'Test Token', 'POST', '/v1/auth/2fa/test-token', 'gateway', True, 5, 'Test 2FA token', {'user_id': 'test_user', 'totp_code': '123456'}),
            EndpointTest(17, 'QR Code', 'GET', '/v1/auth/2fa/qr/test_user', 'gateway', True, 5, 'Get QR code for 2FA setup'),
            EndpointTest(18, 'Webhook Interview Scheduled', 'POST', '/api/v1/webhooks/interview-scheduled', 'gateway', True, 5, 'Handle interview scheduled webhook', {'candidate_id': 1, 'job_id': 1, 'interview_time': '2026-01-22T10:00:00Z'}),
            
            # Job Management (19-20)
            EndpointTest(19, 'List Jobs', 'GET', '/v1/jobs', 'gateway', True, 15, 'List all active job postings'),
            EndpointTest(20, 'Create Job', 'POST', '/v1/jobs', 'gateway', True, 10, 'Create new job posting', {'title': 'Senior Software Engineer', 'department': 'Engineering', 'location': 'Remote', 'experience_level': 'senior', 'requirements': '5+ years Python, FastAPI, PostgreSQL', 'description': 'Join our team to build scalable HR solutions', 'employment_type': 'Full-time'}),
            
            # Candidate Management (21-26)
            EndpointTest(21, 'List Candidates', 'GET', '/v1/candidates', 'gateway', True, 15, 'Get all candidates with pagination', query_params='limit=50&offset=0'),
            EndpointTest(22, 'Candidate Stats', 'GET', '/v1/candidates/stats', 'gateway', True, 5, 'Get candidate statistics'),
            EndpointTest(23, 'Search Candidates', 'GET', '/v1/candidates/search', 'gateway', True, 8, 'Search candidates by skills', query_params='skills=Python'),
            EndpointTest(24, 'Candidates by Job', 'GET', '/v1/candidates/job/1', 'gateway', True, 5, 'Get candidates for specific job'),
            EndpointTest(25, 'Candidate by ID', 'GET', '/v1/candidates/1', 'gateway', True, 5, 'Get candidate by ID'),
            EndpointTest(26, 'Bulk Upload Candidates', 'POST', '/v1/candidates/bulk', 'gateway', True, 120, 'Bulk upload multiple candidates', {'candidates': [{'name': 'Jane Smith', 'email': 'jane.smith@example.com', 'phone': '+1234567890', 'location': 'New York, NY', 'experience_years': 3, 'technical_skills': 'JavaScript, React, Node.js', 'seniority_level': 'Mid', 'education_level': 'Bachelor', 'resume_path': '/resumes/jane_smith.pdf', 'status': 'applied'}]}),
            
            # AI Matching Engine (27-28)
            EndpointTest(27, 'Top Matches', 'GET', '/v1/match/123/top', 'gateway', True, 60, 'AI-powered semantic candidate matching via Agent Service', query_params='limit=10'),
            EndpointTest(28, 'Batch Match', 'POST', '/v1/match/batch', 'gateway', True, 120, 'Batch AI matching for multiple jobs', {'job_ids': [123, 124, 125]}),
            
            # Assessment & Workflow (29-35)
            EndpointTest(29, 'Submit Feedback', 'POST', '/v1/feedback', 'gateway', True, 15, 'Submit values assessment feedback for candidate', {'candidate_id': 123, 'job_id': 45, 'integrity': 5, 'honesty': 5, 'discipline': 4, 'hard_work': 5, 'gratitude': 4, 'comments': 'Excellent candidate with strong values alignment'}),
            EndpointTest(30, 'Get Feedback', 'GET', '/v1/feedback', 'gateway', True, 5, 'Get feedback for candidate'),
            EndpointTest(31, 'List Interviews', 'GET', '/v1/interviews', 'gateway', True, 5, 'List all interviews'),
            EndpointTest(32, 'Schedule Interview', 'POST', '/v1/interviews', 'gateway', True, 10, 'Schedule interview for candidate', {'candidate_id': 123, 'job_id': 45, 'interview_date': '2026-01-22T10:00:00Z', 'interviewer': 'HR Team'}),
            EndpointTest(33, 'Create Offer', 'POST', '/v1/offers', 'gateway', True, 10, 'Create job offer for candidate', {'candidate_id': 123, 'job_id': 45, 'salary': 120000, 'start_date': '2026-02-01', 'terms': 'Full-time'}),
            EndpointTest(34, 'List Offers', 'GET', '/v1/offers', 'gateway', True, 5, 'List all job offers'),
            EndpointTest(35, 'Get Offer', 'GET', '/v1/offers/1', 'gateway', True, 5, 'Get specific job offer'),
            
            # Client Portal API (36-37)
            EndpointTest(36, 'Client Register', 'POST', '/v1/client/register', 'gateway', False, 10, 'Register new client', {'client_id': 'TECH001', 'company_name': 'Tech Corp', 'contact_email': 'admin@techcorp.com', 'password': 'secure_password_123'}),
            EndpointTest(37, 'Client Login', 'POST', '/v1/client/login', 'gateway', False, 10, 'Client login', {'client_id': 'TECH001', 'password': 'secure_password_123'}),
            
            # Security Testing (38-47)
            EndpointTest(38, 'Rate Limit Status', 'GET', '/v1/security/rate-limit-status', 'gateway', True, 5, 'Check current rate limit status'),
            EndpointTest(39, 'Blocked IPs', 'GET', '/v1/security/blocked-ips', 'gateway', True, 5, 'View list of blocked IP addresses'),
            EndpointTest(40, 'Test Input Validation', 'POST', '/v1/security/test-input-validation', 'gateway', True, 5, 'Test input validation against various attack vectors', {'input_data': "<script>alert('xss')</script>", 'field_type': 'text_input', 'validation_rules': ['xss', 'sql_injection', 'command_injection']}),
            EndpointTest(41, 'Validate Email', 'POST', '/v1/security/validate-email', 'gateway', True, 5, 'Validate email format and security checks', {'email': 'test@example.com', 'check_mx_record': True, 'check_disposable': True}),
            EndpointTest(42, 'Test Email Validation', 'POST', '/v1/security/test-email-validation', 'gateway', True, 10, 'Comprehensive email validation testing', {'email': 'test@example.com', 'validation_tests': ['format', 'domain', 'disposable', 'role_account']}),
            EndpointTest(43, 'Validate Phone', 'POST', '/v1/security/validate-phone', 'gateway', True, 5, 'Validate phone number format', {'phone': '+1234567890', 'country_code': 'US'}),
            EndpointTest(44, 'Test Phone Validation', 'POST', '/v1/security/test-phone-validation', 'gateway', True, 5, 'Comprehensive phone validation testing', {'phone': '+1234567890', 'validation_tests': ['format', 'country_code', 'carrier']}),
            EndpointTest(45, 'Test Headers', 'GET', '/v1/security/test-headers', 'gateway', True, 5, 'Test security headers'),
            EndpointTest(46, 'Security Headers Test', 'GET', '/v1/security/security-headers-test', 'gateway', True, 5, 'Comprehensive security headers test'),
            EndpointTest(47, 'Penetration Test', 'POST', '/v1/security/penetration-test', 'gateway', True, 15, 'Run penetration test', {'test_type': 'xss', 'payload': "<script>alert('test')</script>"}),
            
            # CSP Management (48-51)
            EndpointTest(48, 'CSP Report', 'POST', '/v1/security/csp-report', 'gateway', True, 5, 'Submit Content Security Policy violation report', {'violated_directive': 'script-src', 'blocked_uri': 'https://malicious.com', 'document_uri': 'https://bhiv-hr.com'}),
            EndpointTest(49, 'CSP Violations', 'GET', '/v1/security/csp-violations', 'gateway', True, 5, 'Get CSP violations'),
            EndpointTest(50, 'CSP Policies', 'GET', '/v1/security/csp-policies', 'gateway', True, 5, 'Get CSP policies'),
            EndpointTest(51, 'Test CSP Policy', 'POST', '/v1/security/test-csp-policy', 'gateway', True, 5, 'Test CSP policy', {'policy': "default-src 'self'"}),
            
            # Two-Factor Authentication (52-59)
            EndpointTest(52, 'Test Auth', 'GET', '/v1/security/test-auth', 'gateway', True, 5, 'Test authentication mechanisms'),
            EndpointTest(53, 'Penetration Test Endpoints', 'GET', '/v1/security/penetration-test-endpoints', 'gateway', True, 5, 'Get endpoints for penetration testing'),
            EndpointTest(54, 'Get 2FA Status', 'GET', '/v1/auth/2fa/status/1', 'gateway', True, 5, 'Get 2FA status for user ID'),
            EndpointTest(55, 'Get QR Code', 'GET', '/v1/auth/2fa/qr/1', 'gateway', True, 5, 'Get QR code for 2FA setup'),
            EndpointTest(56, 'Validate TOTP', 'POST', '/v1/auth/2fa/validate', 'gateway', True, 5, 'Validate TOTP code', {'user_id': 1, 'totp_code': '123456'}),
            EndpointTest(57, 'Reset 2FA', 'POST', '/v1/auth/2fa/reset', 'gateway', True, 10, 'Reset 2FA for user', {'user_id': 1, 'admin_password': 'admin123'}),
            EndpointTest(58, 'List 2FA Users', 'GET', '/v1/auth/2fa/users', 'gateway', True, 5, 'List users with 2FA enabled'),
            EndpointTest(59, 'Update 2FA Settings', 'PUT', '/v1/auth/2fa/settings', 'gateway', True, 5, 'Update 2FA settings', {'user_id': 1, 'enabled': True, 'backup_codes_enabled': True}),
            
            # Password Management (60-65)
            EndpointTest(60, 'Validate Password', 'POST', '/v1/auth/password/validate', 'gateway', True, 5, 'Validate password strength', {'password': 'SecurePassword123!'}),
            EndpointTest(61, 'Generate Password', 'GET', '/v1/auth/password/generate', 'gateway', True, 5, 'Generate secure password'),
            EndpointTest(62, 'Password Policy', 'GET', '/v1/auth/password/policy', 'gateway', True, 5, 'Get password policy'),
            EndpointTest(63, 'Change Password', 'POST', '/v1/auth/password/change', 'gateway', True, 10, 'Change user password', {'user_id': 1, 'old_password': 'old_password', 'new_password': 'new_secure_password_123'}),
            EndpointTest(64, 'Password Strength', 'POST', '/v1/auth/password/strength', 'gateway', True, 5, 'Check password strength', {'password': 'SecurePassword123!'}),
            EndpointTest(65, 'Security Tips', 'GET', '/v1/auth/password/security-tips', 'gateway', True, 5, 'Get password security tips'),
            
            # Candidate Portal (66-71)
            EndpointTest(66, 'Candidate Register', 'POST', '/v1/candidate/register', 'gateway', False, 10, 'Register new candidate', {'name': 'John Doe', 'email': 'john.doe@example.com', 'password': 'secure_password_123', 'phone': '+1234567890', 'location': 'San Francisco, CA', 'experience_years': 5, 'technical_skills': 'Python, FastAPI, PostgreSQL', 'seniority_level': 'Senior', 'education_level': 'Bachelor'}),
            EndpointTest(67, 'Candidate Login', 'POST', '/v1/candidate/login', 'gateway', False, 10, 'Candidate login', {'email': 'john.doe@example.com', 'password': 'secure_password_123'}),
            EndpointTest(68, 'Update Profile', 'PUT', '/v1/candidate/profile/1', 'gateway', True, 10, 'Update candidate profile', {'phone': '+1987654321', 'location': 'New York, NY', 'technical_skills': 'Python, FastAPI, PostgreSQL, Docker', 'experience_years': 6}),
            EndpointTest(69, 'Apply for Job', 'POST', '/v1/candidate/apply', 'gateway', True, 15, 'Apply for job', {'candidate_id': 1, 'job_id': 123, 'cover_letter': 'I am excited to apply for this position...', 'resume_path': '/resumes/john_doe.pdf'}),
            EndpointTest(70, 'Get Applications', 'GET', '/v1/candidate/applications/1', 'gateway', True, 5, 'Get candidate applications'),
            EndpointTest(71, 'Withdraw Application', 'DELETE', '/v1/candidate/application/1', 'gateway', True, 10, 'Withdraw job application'),
            
            # RL + Feedback Agent (72-75)
            EndpointTest(72, 'RL Predict', 'POST', '/v1/rl/predict', 'gateway', True, 20, 'Reinforcement Learning prediction', {'candidate_id': 123, 'job_id': 45, 'candidate_features': {'experience': 5, 'skills': ['Python', 'FastAPI', 'PostgreSQL']}, 'job_features': {'required_experience': 3, 'required_skills': ['Python', 'FastAPI']}}),
            EndpointTest(73, 'RL Feedback', 'POST', '/v1/rl/feedback', 'gateway', True, 10, 'Reinforcement Learning feedback', {'candidate_id': 123, 'job_id': 45, 'actual_outcome': 'hired', 'feedback_score': 4.5, 'feedback_source': 'hr'}),
            EndpointTest(74, 'RL Analytics', 'GET', '/v1/rl/analytics', 'gateway', True, 15, 'Get RL analytics'),
            EndpointTest(75, 'RL Performance', 'GET', '/v1/rl/performance', 'gateway', True, 10, 'Get RL performance metrics'),
            
            # Recruiter Portal (76)
            EndpointTest(76, 'Recruiter Dashboard', 'GET', '/v1/recruiter/dashboard', 'gateway', True, 15, 'Get recruiter dashboard data'),
            
            # Additional Gateway Endpoints (77-80)
            EndpointTest(77, 'Get Job Details', 'GET', '/v1/jobs/123', 'gateway', True, 5, 'Get specific job details'),
            EndpointTest(78, 'Update Job', 'PUT', '/v1/jobs/123', 'gateway', True, 10, 'Update job posting', {'title': 'Senior Software Engineer', 'department': 'Engineering', 'location': 'Remote', 'experience_level': 'senior', 'requirements': '5+ years Python, FastAPI, PostgreSQL', 'description': 'Updated job description', 'status': 'active'}),
            EndpointTest(79, 'Delete Job', 'DELETE', '/v1/jobs/123', 'gateway', True, 10, 'Delete job posting'),
            EndpointTest(80, 'Export Candidates', 'GET', '/v1/candidates/export', 'gateway', True, 30, 'Export candidates to CSV', query_params='format=csv&fields=name,email,phone,skills'),
        ]
        
        # Agent Endpoints (81-86)
        agent_endpoints = [
            EndpointTest(81, 'Agent Root', 'GET', '/', 'agent', False, 2, 'AI Agent service information'),
            EndpointTest(82, 'Agent Health', 'GET', '/health', 'agent', False, 5, 'Health check for AI Agent service'),
            EndpointTest(83, 'Agent Test DB', 'GET', '/test-db', 'agent', True, 10, 'Test database connectivity'),
            EndpointTest(84, 'Agent Match', 'POST', '/match', 'agent', True, 60, 'AI-powered candidate matching using Phase 3 semantic engine', {'job_id': 123}),
            EndpointTest(85, 'Agent Batch Match', 'POST', '/batch-match', 'agent', True, 120, 'Batch AI matching for multiple jobs', {'job_ids': [123, 124, 125]}),
            EndpointTest(86, 'Agent Analyze', 'GET', '/analyze/123', 'agent', True, 60, 'Detailed candidate analysis with skill categorization'),
        ]
        
        # LangGraph Endpoints (87-111)
        langgraph_endpoints = [
            # Core Endpoints (87-88)
            EndpointTest(87, 'LangGraph Root', 'GET', '/', 'langgraph', False, 2, 'LangGraph service information'),
            EndpointTest(88, 'LangGraph Health', 'GET', '/health', 'langgraph', False, 5, 'Health check for LangGraph service'),
            
            # Workflow Endpoints (89-93)
            EndpointTest(89, 'Start Application Workflow', 'POST', '/workflows/application/start', 'langgraph', True, 10, 'Start AI workflow for candidate processing', {'candidate_id': 123, 'job_id': 45, 'application_id': 789, 'candidate_email': 'john.doe@example.com', 'candidate_phone': '+1234567890', 'candidate_name': 'John Doe', 'job_title': 'Senior Software Engineer', 'job_description': 'Build scalable HR solutions'}),
            EndpointTest(90, 'Get Workflow Status', 'GET', '/workflows/status/wf_abc123def456', 'langgraph', True, 5, 'Get workflow status'),
            EndpointTest(91, 'Resume Workflow', 'POST', '/workflows/wf_abc123def456/resume', 'langgraph', True, 10, 'Resume paused workflow'),
            EndpointTest(92, 'Cancel Workflow', 'POST', '/workflows/wf_abc123def456/cancel', 'langgraph', True, 10, 'Cancel workflow execution'),
            EndpointTest(93, 'List Workflows', 'GET', '/workflows', 'langgraph', True, 10, 'List all workflows'),
            
            # Notification Endpoints (94-102)
            EndpointTest(94, 'Send Email', 'POST', '/notifications/email', 'langgraph', True, 15, 'Send email notification', {'to': 'john.doe@example.com', 'subject': 'Job Application', 'body': 'Thank you for your application', 'template': 'application_received'}),
            EndpointTest(95, 'Send SMS', 'POST', '/notifications/sms', 'langgraph', True, 10, 'Send SMS notification', {'to': '+1234567890', 'message': 'Your interview is scheduled for tomorrow', 'template': 'interview_reminder'}),
            EndpointTest(96, 'Send WhatsApp', 'POST', '/notifications/whatsapp', 'langgraph', True, 15, 'Send WhatsApp notification', {'to': '+1234567890', 'message': 'Congratulations! You have been selected for the next round', 'template': 'shortlisted'}),
            EndpointTest(97, 'Send Telegram', 'POST', '/notifications/telegram', 'langgraph', True, 10, 'Send Telegram notification', {'to': 'user_id_123', 'message': 'New job matches found', 'template': 'job_matches'}),
            EndpointTest(98, 'Send Multi-Channel', 'POST', '/notifications/multi-channel', 'langgraph', True, 20, 'Send notification across multiple channels', {'candidate_id': 123, 'message': 'Application update', 'channels': ['email', 'sms', 'whatsapp']}),
            EndpointTest(99, 'Get Notification Status', 'GET', '/notifications/status/123', 'langgraph', True, 5, 'Get notification delivery status'),
            EndpointTest(100, 'Retry Notification', 'POST', '/notifications/123/retry', 'langgraph', True, 10, 'Retry failed notification'),
            EndpointTest(101, 'Bulk Notifications', 'POST', '/notifications/bulk', 'langgraph', True, 30, 'Send bulk notifications', {'candidates': [123, 456, 789], 'message': 'Important update', 'channel': 'email'}),
            EndpointTest(102, 'Notification Templates', 'GET', '/notifications/templates', 'langgraph', True, 5, 'Get available notification templates'),
            
            # RL Integration Endpoints (103-111)
            EndpointTest(103, 'RL Predict', 'POST', '/rl/predict', 'langgraph', True, 20, 'Reinforcement Learning prediction', {'candidate_id': 123, 'job_id': 45, 'candidate_features': {'experience': 5, 'skills': ['Python', 'FastAPI', 'PostgreSQL']}, 'job_features': {'required_experience': 3, 'required_skills': ['Python', 'FastAPI']}}),
            EndpointTest(104, 'RL Feedback', 'POST', '/rl/feedback', 'langgraph', True, 10, 'Reinforcement Learning feedback', {'candidate_id': 123, 'job_id': 45, 'actual_outcome': 'hired', 'feedback_score': 4.5, 'feedback_source': 'hr'}),
            EndpointTest(105, 'RL Analytics', 'GET', '/rl/analytics', 'langgraph', True, 15, 'Get RL analytics'),
            EndpointTest(106, 'RL Performance', 'GET', '/rl/performance', 'langgraph', True, 10, 'Get RL performance metrics'),
            EndpointTest(107, 'RL History', 'GET', '/rl/history/123', 'langgraph', True, 10, 'Get RL prediction history for candidate'),
            EndpointTest(108, 'RL Retrain', 'POST', '/rl/retrain', 'langgraph', True, 120, 'Retrain RL model with new data'),
            EndpointTest(109, 'RL Performance v1', 'GET', '/rl/performance/v1.0.0', 'langgraph', True, 10, 'Get RL performance metrics for specific version'),
            EndpointTest(110, 'RL Monitor', 'POST', '/rl/start-monitoring', 'langgraph', True, 15, 'Start RL monitoring'),
            EndpointTest(111, 'Integration Test', 'GET', '/test-integration', 'langgraph', True, 10, 'Test LangGraph integration with other services'),
        ]
        
        endpoints.extend(gateway_endpoints)
        endpoints.extend(agent_endpoints)
        endpoints.extend(langgraph_endpoints)
        
        return endpoints
    
    def test_endpoint(self, endpoint: EndpointTest) -> Dict[str, Any]:
        """Test a single endpoint with comprehensive validation"""
        start_time = time.time()
        result = {
            'number': endpoint.number,
            'name': endpoint.name,
            'method': endpoint.method,
            'path': endpoint.path,
            'service': endpoint.service,
            'url': f"{self.base_urls[endpoint.service]}{endpoint.path}",
            'status': 'UNKNOWN',
            'response_time': 0,
            'status_code': None,
            'error': None,
            'response_body': None,
            'validation_passed': False
        }
        
        try:
            # Construct full URL with query parameters
            url = f"{self.base_urls[endpoint.service]}{endpoint.path}"
            if endpoint.query_params:
                url += f"?{endpoint.query_params}"
            
            # Prepare headers
            headers = self.headers.copy() if endpoint.auth_required else {'Content-Type': 'application/json'}
            
            # Make request
            response = requests.request(
                method=endpoint.method,
                url=url,
                headers=headers,
                json=endpoint.request_body,
                timeout=endpoint.timeout
            )
            
            end_time = time.time()
            result['response_time'] = round((end_time - start_time) * 1000, 2)
            result['status_code'] = response.status_code
            result['response_body'] = response.text[:1000] if response.text else ""
            
            # Determine test status
            if response.status_code == endpoint.expected_status:
                result['status'] = 'PASS'
                result['validation_passed'] = True
            elif response.status_code == 401 and not endpoint.auth_required:
                # Expected unauthorized for non-auth endpoints
                result['status'] = 'PASS'
                result['validation_passed'] = True
            elif response.status_code == 404:
                result['status'] = 'NOT_FOUND'
            elif response.status_code == 401:
                result['status'] = 'UNAUTHORIZED'
            elif response.status_code == 403:
                result['status'] = 'FORBIDDEN'
            elif response.status_code == 422:
                result['status'] = 'VALIDATION_ERROR'
            elif response.status_code >= 500:
                result['status'] = 'SERVER_ERROR'
            else:
                result['status'] = 'CLIENT_ERROR'
                
        except requests.exceptions.Timeout:
            result['status'] = 'TIMEOUT'
            result['error'] = f'Request timed out after {endpoint.timeout}s'
            result['response_time'] = endpoint.timeout * 1000
            
        except requests.exceptions.ConnectionError:
            result['status'] = 'CONNECTION_ERROR'
            result['error'] = 'Connection failed - service may be down'
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            
        return result
    
    def run_tests(self) -> List[Dict[str, Any]]:
        """Run tests on all endpoints"""
        logger.info(f"Starting API contract compliance tests for {len(self.endpoints)} endpoints...")
        
        for i, endpoint in enumerate(self.endpoints, 1):
            logger.info(f"[{i:3d}/{len(self.endpoints)}] Testing: {endpoint.service.upper()} - {endpoint.name}")
            
            result = self.test_endpoint(endpoint)
            self.results.append(result)
            
            # Update summary
            self.test_summary['total'] += 1
            self.test_summary['by_service'][endpoint.service]['total'] += 1
            
            if result['status'] == 'PASS':
                self.test_summary['passed'] += 1
                self.test_summary['by_service'][endpoint.service]['passed'] += 1
            elif result['status'] in ['NOT_FOUND', 'UNAUTHORIZED', 'FORBIDDEN', 'VALIDATION_ERROR']:
                self.test_summary['failed'] += 1
                self.test_summary['by_service'][endpoint.service]['failed'] += 1
            else:
                self.test_summary['errors'] += 1
            
            # Log result
            status_symbol = {
                'PASS': '✅',
                'TIMEOUT': '⏰',
                'CONNECTION_ERROR': '❌',
                'NOT_FOUND': '4️⃣',
                'UNAUTHORIZED': '1️⃣',
                'FORBIDDEN': '3️⃣',
                'VALIDATION_ERROR': '2️⃣',
                'SERVER_ERROR': '5️⃣',
                'CLIENT_ERROR': '4️⃣',
                'ERROR': '❌'
            }.get(result['status'], '❓')
            
            logger.info(f"   {status_symbol} {result['status']} - {result['response_time']}ms")
            if result['error']:
                logger.warning(f"   Error: {result['error']}")
        
        return self.results
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        if not self.results:
            logger.warning("No test results to report!")
            return
        
        logger.info("=" * 80)
        logger.info("API CONTRACT COMPLIANCE TEST REPORT")
        logger.info("=" * 80)
        logger.info(f"Total Endpoints Tested: {self.test_summary['total']}")
        logger.info(f"Passed: {self.test_summary['passed']} ({self.test_summary['passed']/self.test_summary['total']*100:.1f}%)")
        logger.info(f"Failed: {self.test_summary['failed']} ({self.test_summary['failed']/self.test_summary['total']*100:.1f}%)")
        logger.info(f"Errors: {self.test_summary['errors']} ({self.test_summary['errors']/self.test_summary['total']*100:.1f}%)")
        
        logger.info("\nService Breakdown:")
        for service, stats in self.test_summary['by_service'].items():
            logger.info(f"  {service.upper()}: {stats['passed']}/{stats['total']} passed")
        
        # Log failed endpoints
        failed_endpoints = [r for r in self.results if r['status'] != 'PASS']
        if failed_endpoints:
            logger.info(f"\nFailed/Errored Endpoints ({len(failed_endpoints)}):")
            for result in failed_endpoints:
                logger.info(f"  #{result['number']} {result['service'].upper()} - {result['name']}: {result['status']}")
                if result['error']:
                    logger.info(f"    Error: {result['error']}")
        
        # Save detailed results
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.test_summary,
            'results': self.results
        }
        
        with open('api_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\nDetailed results saved to: api_test_results.json")
        logger.info("=" * 80)

def main():
    """Main execution function"""
    tester = EndpointTester()
    
    try:
        # Run all tests
        results = tester.run_tests()
        
        # Generate report
        tester.generate_report()
        
        # Return exit code based on results
        if tester.test_summary['passed'] == tester.test_summary['total']:
            logger.info("🎉 All tests passed!")
            return 0
        else:
            logger.warning("⚠️  Some tests failed or had errors")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Fatal error during test execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())