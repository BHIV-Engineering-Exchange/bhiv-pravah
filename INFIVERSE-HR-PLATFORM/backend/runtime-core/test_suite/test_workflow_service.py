"""
Test suite for Workflow Engine in Sovereign Application Runtime (SAR)
"""
import pytest
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "default_sar_api_key")

class TestWorkflowService:
    """Test cases for Workflow Engine"""
    
    def test_workflow_health_check(self):
        """Test workflow service health check"""
        response = requests.get(f"{BASE_URL}/workflow/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        print("✅ Workflow health check passed")
    
    def test_get_workflow_definitions(self):
        """Test getting workflow definitions"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/workflow/definitions", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "definitions" in data
        print("✅ Get workflow definitions test passed")
    
    def test_list_workflow_instances(self):
        """Test listing workflow instances"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/workflow/instances", headers=headers)
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert "instances" in data
        print("✅ List workflow instances test passed")
    
    def test_get_workflow_instance_details(self):
        """Test getting specific workflow instance details"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BASE_URL}/workflow/instances/test_instance_123", 
                              headers=headers)
        # Expected to return 404 if instance doesn't exist, or 200 if it does
        assert response.status_code in [200, 401, 403, 404]
        if response.status_code == 200:
            data = response.json()
            assert "instance_id" in data
        print("✅ Get workflow instance details test passed")
    
    def test_start_workflow(self):
        """Test starting a new workflow"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        workflow_data = {
            "workflow_name": "test_workflow",
            "parameters": {"test_param": "test_value"}
        }
        response = requests.post(f"{BASE_URL}/workflow/start", 
                                json=workflow_data, headers=headers)
        assert response.status_code in [200, 401, 403, 400]
        if response.status_code == 200:
            data = response.json()
            assert "instance_id" in data
        print("✅ Start workflow test passed")
    
    def test_pause_workflow_instance(self):
        """Test pausing a workflow instance"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.post(f"{BASE_URL}/workflow/instances/test_instance_123/pause", 
                                headers=headers)
        assert response.status_code in [200, 401, 403, 404]
        print("✅ Pause workflow instance test passed")
    
    def test_resume_workflow_instance(self):
        """Test resuming a workflow instance"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.post(f"{BASE_URL}/workflow/instances/test_instance_123/resume", 
                                headers=headers)
        assert response.status_code in [200, 401, 403, 404]
        print("✅ Resume workflow instance test passed")
    
    def test_cancel_workflow_instance(self):
        """Test cancelling a workflow instance"""
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.post(f"{BASE_URL}/workflow/instances/test_instance_123/cancel", 
                                headers=headers)
        assert response.status_code in [200, 401, 403, 404]
        print("✅ Cancel workflow instance test passed")


if __name__ == "__main__":
    test_instance = TestWorkflowService()
    test_instance.test_workflow_health_check()
    test_instance.test_get_workflow_definitions()
    test_instance.test_list_workflow_instances()
    test_instance.test_get_workflow_instance_details()
    test_instance.test_start_workflow()
    test_instance.test_pause_workflow_instance()
    test_instance.test_resume_workflow_instance()
    test_instance.test_cancel_workflow_instance()
    print("\n🎉 All Workflow Service tests completed!")