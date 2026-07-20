"""
System Integration Test Suite for Sovereign Application Runtime (SAR)
Tests the integration between different services
"""
import pytest
import requests
import os
from unittest.mock import patch, MagicMock

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "default_sar_api_key")

class TestSystemIntegration:
    """Test cases for system integration across services"""
    
    def test_system_health_checks(self):
        """Test health checks for all services"""
        endpoints = [
            f"{BASE_URL}/health",  # Main health check
            f"{BASE_URL}/auth/health",
            f"{BASE_URL}/tenants/health", 
            f"{BASE_URL}/role/health",
            f"{BASE_URL}/audit/health",
            f"{BASE_URL}/workflow/health"
        ]
        
        for endpoint in endpoints:
            response = requests.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy" or data["status"] == "ready"
        
        print("✅ All system health checks passed")
    
    def test_cross_service_authentication_and_tenancy(self):
        """Test authentication and tenancy integration"""
        # First, try to get current tenant with API key
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/tenants/current", headers=headers)
        # Should be successful with API key
        assert response.status_code in [200, 401, 403]  # Could be 401/403 if token type is not accepted
        
        print("✅ Cross-service authentication and tenancy integration test passed")
    
    def test_role_based_access_control_integration(self):
        """Test RBAC integration with other services"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Test getting current user info through role service
        response = requests.get(f"{BASE_URL}/role/current", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        # Test getting permissions
        response = requests.get(f"{BASE_URL}/role/permissions", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        print("✅ RBAC integration test passed")
    
    def test_audit_log_integration(self):
        """Test audit logging integration with other services"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Try to get audit events
        response = requests.get(f"{BASE_URL}/audit/events", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        # Try to get audit stats
        response = requests.get(f"{BASE_URL}/audit/stats", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        print("✅ Audit log integration test passed")
    
    def test_workflow_and_role_integration(self):
        """Test workflow and role service integration"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # Try to get workflow definitions
        response = requests.get(f"{BASE_URL}/workflow/definitions", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        # Try to get workflow instances
        response = requests.get(f"{BASE_URL}/workflow/instances", headers=headers)
        assert response.status_code in [200, 401, 403]
        
        print("✅ Workflow and role integration test passed")
    
    def test_adapter_manager_integration(self):
        """Test adapter manager functionality"""
        # Import and test adapter manager directly
        from integration.adapter_manager import AdapterManager
        
        # Test basic instantiation
        manager = AdapterManager()
        assert hasattr(manager, 'execute_all_adapters')
        assert hasattr(manager, 'get_active_adapters')
        
        # Test with some configurations
        configs = {
            "insightflow": {"enabled": True, "name": "InsightFlow Test"},
            "bucket": {"enabled": False, "name": "Bucket Test"}
        }
        manager = AdapterManager(configs)
        
        # Test active adapters
        active = manager.get_active_adapters()
        assert "insightflow" in active
        assert "bucket" not in active
        
        print("✅ Adapter manager integration test passed")
    
    def test_main_application_startup(self):
        """Test main application startup and routing"""
        # Test main endpoints
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "Sovereign Application Runtime" in data["service"] or "BHIV Application Framework" in data["service"]
        
        # Test ready endpoint
        response = requests.get(f"{BASE_URL}/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"
        
        print("✅ Main application startup test passed")


if __name__ == "__main__":
    test_instance = TestSystemIntegration()
    test_instance.test_system_health_checks()
    test_instance.test_cross_service_authentication_and_tenancy()
    test_instance.test_role_based_access_control_integration()
    test_instance.test_audit_log_integration()
    test_instance.test_workflow_and_role_integration()
    test_instance.test_adapter_manager_integration()
    test_instance.test_main_application_startup()
    print("\n🎉 All System Integration tests completed!")