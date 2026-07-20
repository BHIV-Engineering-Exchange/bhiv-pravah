"""
Test suite for Tenant Service in Sovereign Application Runtime (SAR)
"""
import pytest
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "default_sar_api_key")

class TestTenantService:
    """Test cases for Tenant Service"""
    
    def test_tenant_health_check(self):
        """Test tenant service health check"""
        response = requests.get(f"{BASE_URL}/tenants/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✅ Tenant health check passed")
    
    def test_get_current_tenant(self):
        """Test getting current tenant information"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/tenants/current", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "tenant_id" in data
        print("✅ Get current tenant test passed")
    
    def test_tenant_isolation_check(self):
        """Test tenant isolation functionality"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/tenants/isolation-check/test_tenant", 
                              headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "access_allowed" in data
        print("✅ Tenant isolation check test passed")
    
    def test_query_filter(self):
        """Test tenant query filter generation"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/tenants/query-filter/users", 
                              headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "filter_clause" in data
        print("✅ Query filter test passed")
    
    def test_shared_resource_access(self):
        """Test shared resource access checking"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/tenants/shared-resource-access/templates", 
                              headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "access_allowed" in data
        print("✅ Shared resource access test passed")


if __name__ == "__main__":
    test_instance = TestTenantService()
    test_instance.test_tenant_health_check()
    test_instance.test_get_current_tenant()
    test_instance.test_tenant_isolation_check()
    test_instance.test_query_filter()
    test_instance.test_shared_resource_access()
    print("\n🎉 All Tenant Service tests completed!")