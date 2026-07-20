"""
Test suite for Role Enforcement Service in Sovereign Application Runtime (SAR)
"""
import pytest
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "default_sar_api_key")

class TestRoleService:
    """Test cases for Role Enforcement Service"""
    
    def test_role_health_check(self):
        """Test role service health check"""
        response = requests.get(f"{BASE_URL}/role/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✅ Role health check passed")
    
    def test_get_available_roles(self):
        """Test getting available roles"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/role/available-roles", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "roles" in data
        print("✅ Available roles test passed")
    
    def test_get_current_user_info(self):
        """Test getting current user information"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/role/current", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
        print("✅ Current user info test passed")
    
    def test_get_user_permissions(self):
        """Test getting user permissions"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/role/permissions", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "permissions" in data
        print("✅ User permissions test passed")
    
    def test_get_user_roles(self):
        """Test getting roles for a specific user"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/role/user/test_user", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
        print("✅ User roles test passed")
    
    def test_check_permission(self):
        """Test permission checking functionality"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        permission_data = {
            "resource": "workflow",
            "action": "read"
        }
        response = requests.post(f"{BASE_URL}/role/check-permission", 
                                json=permission_data, headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "has_permission" in data
        print("✅ Permission check test passed")


if __name__ == "__main__":
    test_instance = TestRoleService()
    test_instance.test_role_health_check()
    test_instance.test_get_available_roles()
    test_instance.test_get_current_user_info()
    test_instance.test_get_user_permissions()
    test_instance.test_get_user_roles()
    test_instance.test_check_permission()
    print("\n🎉 All Role Service tests completed!")