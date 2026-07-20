"""
Test script to validate the adapter system for the Sovereign Application Runtime (SAR).
"""

from integration.adapter_manager import AdapterManager
from typing import Dict, Any

def test_adapters():
    """Test the adapter system with sample events."""
    
    # Example configuration enabling all adapters
    configs = {
        'artha': {
            "name": "Artha Adapter",
            "enabled": True,
            "artha_api_url": "https://artha-api.example.com",
            "artha_api_key": "test-key"
        },
        'karya': {
            "name": "Karya Adapter", 
            "enabled": True,
            "karya_api_url": "https://karya-api.example.com",
            "karya_api_key": "test-key"
        },
        'insightflow': {
            "name": "InsightFlow Adapter",
            "enabled": True,
            "insightflow_api_url": "https://insightflow-api.example.com",
            "insightflow_api_key": "test-key"
        },
        'bucket': {
            "name": "Bucket Adapter",
            "enabled": True,
            "bucket_api_url": "https://bucket-api.example.com",
            "bucket_credentials": "test-credentials"
        }
    }
    
    # Initialize manager
    manager = AdapterManager(configs)
    
    # Test event 1: Payroll-related event (should trigger Artha adapter primarily)
    payroll_event = {
        "event_id": "evt_123",
        "action": "payroll_processed",
        "tenant_id": "tenant_abc", 
        "user_id": "user_123",
        "timestamp": "2026-01-10T17:00:00Z",
        "data": {"amount": 5000, "employee_id": "emp_456"}
    }
    
    print("Testing payroll event...")
    results = manager.execute_all_adapters(payroll_event)
    print(f"Results: {results}")
    print()
    
    # Test event 2: Task-related event (should trigger Karya adapter primarily)
    task_event = {
        "event_id": "evt_456",
        "action": "task_created",
        "tenant_id": "tenant_def",
        "user_id": "user_789",
        "timestamp": "2026-01-10T17:05:00Z",
        "data": {"task_name": "Review documents", "assignee": "user_789"}
    }
    
    print("Testing task event...")
    results = manager.execute_all_adapters(task_event)
    print(f"Results: {results}")
    print()
    
    # Test event 3: General event (should trigger InsightFlow primarily)
    general_event = {
        "event_id": "evt_789",
        "action": "user_login",
        "tenant_id": "tenant_ghi",
        "user_id": "user_101",
        "timestamp": "2026-01-10T17:10:00Z",
        "data": {"ip_address": "192.168.1.100"}
    }
    
    print("Testing general event...")
    results = manager.execute_all_adapters(general_event)
    print(f"Results: {results}")
    print()
    
    # Test with adapters disabled
    print("Testing with all adapters disabled...")
    disabled_configs = {
        'artha': {"enabled": False},
        'karya': {"enabled": False}, 
        'insightflow': {"enabled": False},
        'bucket': {"enabled": False}
    }
    
    disabled_manager = AdapterManager(disabled_configs)
    results = disabled_manager.execute_all_adapters(payroll_event)
    print(f"Results with disabled adapters: {results}")
    print()
    
    # Show active adapters
    print(f"Active adapters in enabled manager: {manager.get_active_adapters()}")
    print(f"Active adapters in disabled manager: {disabled_manager.get_active_adapters()}")
    
    print("\nAdapter system test completed successfully!")

if __name__ == "__main__":
    test_adapters()