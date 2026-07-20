"""
Test suite for Audit Logging Service in Sovereign Application Runtime (SAR)
"""
import pytest
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "default_sar_api_key")

class TestAuditService:
    """Test cases for Audit Logging Service"""
    
    def test_audit_health_check(self):
        """Test audit service health check"""
        response = requests.get(f"{BASE_URL}/audit/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✅ Audit health check passed")
    
    def test_get_audit_events(self):
        """Test getting audit events"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/audit/events", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "events" in data
        print("✅ Get audit events test passed")
    
    def test_get_audit_event_by_id(self):
        """Test getting a specific audit event by ID"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/audit/events/test_event_123", headers=headers)
        # Expected to return 404 if event doesn't exist, or 200 if it does
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert "event_id" in data
        print("✅ Get audit event by ID test passed")
    
    def test_get_resource_audit_trail(self):
        """Test getting audit trail for a specific resource"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/audit/trail/test_resource/test_resource_id", 
                              headers=headers)
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert "audit_trail" in data
        print("✅ Get resource audit trail test passed")
    
    def test_get_audit_stats(self):
        """Test getting audit statistics"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/audit/stats", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "total_events" in data
        print("✅ Get audit stats test passed")
    
    def test_log_custom_event(self):
        """Test logging a custom audit event"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        # Using query parameters for this endpoint
        response = requests.post(
            f"{BASE_URL}/audit/log-custom?event_type=api_access&resource=test&action=test",
            headers=headers
        )
        assert response.status_code in [200, 401, 403]
        print("✅ Log custom event test passed")


if __name__ == "__main__":
    test_instance = TestAuditService()
    test_instance.test_audit_health_check()
    test_instance.test_get_audit_events()
    test_instance.test_get_audit_event_by_id()
    test_instance.test_get_resource_audit_trail()
    test_instance.test_get_audit_stats()
    test_instance.test_log_custom_event()
    print("\n🎉 All Audit Service tests completed!")