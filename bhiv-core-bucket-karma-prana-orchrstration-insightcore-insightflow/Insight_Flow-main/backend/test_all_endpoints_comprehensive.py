#!/usr/bin/env python3
"""
Comprehensive endpoint testing script to identify all API errors
"""

import requests
import json
import sys
import time
from datetime import datetime

class EndpointTester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None
        self.errors = []
        self.successes = []
        
    def get_auth_token(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", json={
                "username": "smith",
                "password": "password123"
            })
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def get_headers(self, include_auth=True):
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if include_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def test_endpoint(self, method, endpoint, data=None, expected_status=200, description=""):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.get_headers(), timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=self.get_headers(), timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=self.get_headers(), timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.get_headers(), timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            status = "✅" if response.status_code == expected_status else "❌"
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected": expected_status,
                "description": description,
                "success": response.status_code == expected_status
            }
            
            if response.status_code != expected_status:
                try:
                    error_detail = response.json().get("detail", "No detail")
                except:
                    error_detail = response.text[:200]
                result["error"] = error_detail
                self.errors.append(result)
            else:
                self.successes.append(result)
            
            print(f"{status} {method} {endpoint} - {response.status_code} ({description})")
            
            if response.status_code != expected_status:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_result = {
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "description": description,
                "success": False
            }
            self.errors.append(error_result)
            print(f"❌ {method} {endpoint} - Exception: {e}")
            return error_result
    
    def run_comprehensive_test(self):
        """Run comprehensive test of all endpoints"""
        
        print("🚀 Starting Comprehensive Endpoint Testing")
        print("=" * 60)
        
        # Get authentication token first
        if not self.get_auth_token():
            print("⚠️  Continuing without authentication...")
        
        print("\n📋 Testing Core Endpoints")
        print("-" * 40)
        
        # Health check
        self.test_endpoint("GET", "/health", description="Health Check")
        
        # API docs
        self.test_endpoint("GET", "/docs", expected_status=200, description="API Documentation")
        
        print("\n🔐 Testing Authentication Endpoints")
        print("-" * 40)
        
        # Auth endpoints
        self.test_endpoint("POST", "/auth/login", {
            "username": "smith",
            "password": "password123"
        }, description="Login")
        
        self.test_endpoint("POST", "/auth/register", {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }, expected_status=201, description="Register")
        
        print("\n🎯 Testing Routing Endpoints")
        print("-" * 40)
        
        # Standard routing
        routing_request = {
            "input_data": {"text": "What is the weather today?"},
            "input_type": "text",
            "strategy": "q_learning",
            "context": {"user_id": "test_user"}
        }
        
        self.test_endpoint("POST", "/api/v1/routing/route", routing_request, description="Standard Routing")
        
        # STP routing
        self.test_endpoint("POST", "/api/v1/routing/route-stp", routing_request, description="STP Routing")
        
        # Agent routing
        agent_request = {
            "agent_type": "nlp",
            "context": {"priority": "normal"},
            "confidence_threshold": 0.75
        }
        
        self.test_endpoint("POST", "/api/v1/routing/route-agent", agent_request, description="Agent Routing")
        
        # Feedback (this is the one failing)
        feedback_request = {
            "routing_log_id": "test-log-id",
            "success": True,
            "latency_ms": 145.5,
            "accuracy_score": 0.88,
            "user_satisfaction": 4
        }
        
        self.test_endpoint("POST", "/api/v1/routing/feedback", feedback_request, description="Submit Feedback")
        
        print("\n👥 Testing Agent Endpoints")
        print("-" * 40)
        
        # Agent management
        self.test_endpoint("GET", "/api/v1/agents", description="List Agents")
        
        agent_data = {
            "name": "Test Agent",
            "type": "nlp",
            "capabilities": ["text_processing"],
            "tags": ["test"]
        }
        
        self.test_endpoint("POST", "/api/v1/agents", agent_data, expected_status=201, description="Create Agent")
        
        print("\n📊 Testing Analytics Endpoints")
        print("-" * 40)
        
        # Analytics
        self.test_endpoint("GET", "/api/v1/analytics/overview", description="Analytics Overview")
        self.test_endpoint("GET", "/api/routing/statistics", description="Routing Statistics")
        
        print("\n🔄 Testing Migration Endpoints")
        print("-" * 40)
        
        # Migration
        self.test_endpoint("GET", "/api/migration/status", description="Migration Status")
        
        print("\n⚙️ Testing Admin Endpoints")
        print("-" * 40)
        
        # Admin endpoints
        self.test_endpoint("GET", "/admin/system-health", description="System Health")
        
        print("\n🎯 Testing Karma Endpoints")
        print("-" * 40)
        
        # Karma endpoints
        self.test_endpoint("GET", "/api/karma/metrics", description="Karma Metrics")
        self.test_endpoint("POST", "/api/karma/toggle", {"enabled": True}, description="Toggle Karma")
        
        print("\n📦 Testing STP Endpoints")
        print("-" * 40)
        
        # STP endpoints
        self.test_endpoint("GET", "/api/stp/metrics", description="STP Metrics")
        
        print("\n" + "=" * 60)
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.successes) + len(self.errors)
        success_rate = (len(self.successes) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {total_tests}")
        print(f"Successes: {len(self.successes)} ✅")
        print(f"Failures: {len(self.errors)} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED ENDPOINTS:")
            print("-" * 40)
            for error in self.errors:
                print(f"• {error['method']} {error['endpoint']}")
                print(f"  Description: {error['description']}")
                if 'status_code' in error:
                    print(f"  Status: {error['status_code']} (expected {error.get('expected', 'N/A')})")
                if 'error' in error:
                    print(f"  Error: {error['error']}")
                print()
        
        if self.successes:
            print(f"✅ SUCCESSFUL ENDPOINTS:")
            print("-" * 40)
            for success in self.successes:
                print(f"• {success['method']} {success['endpoint']} - {success['description']}")

if __name__ == "__main__":
    tester = EndpointTester()
    tester.run_comprehensive_test()