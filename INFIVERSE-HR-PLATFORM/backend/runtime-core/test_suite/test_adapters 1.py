"""
Test suite for Integration Adapters in Sovereign Application Runtime (SAR)
"""
import pytest
import os
from unittest.mock import patch, MagicMock

# Import adapter classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # Add parent directory to path

from integration.adapters.base_adapter import BaseIntegrationAdapter
from integration.adapters.artha_adapter import ArthaAdapter
from integration.adapters.karya_adapter import KaryaAdapter
from integration.adapters.insightflow_adapter import InsightFlowAdapter
from integration.adapters.bucket_adapter import BucketAdapter
from integration.adapter_manager import AdapterManager

class TestAdapters:
    """Test cases for Integration Adapters"""
    
    def test_base_adapter_initialization(self):
        """Test base adapter initialization"""
        # Create a concrete implementation for testing
        class ConcreteAdapter(BaseIntegrationAdapter):
            def _execute_internal(self, event):
                return {"event": event, "result": "success"}
        
        config = {"enabled": True, "name": "Test Adapter"}
        adapter = ConcreteAdapter(config)
        assert adapter.enabled == True
        assert adapter.name == "Test Adapter"
        print("✅ Base adapter initialization test passed")
    
    def test_artha_adapter_initialization(self):
        """Test Artha adapter initialization"""
        config = {"enabled": True, "name": "Artha Adapter"}
        adapter = ArthaAdapter(config)
        assert adapter.enabled == True
        assert adapter.name == "Artha Adapter"
        print("✅ Artha adapter initialization test passed")
    
    def test_karya_adapter_initialization(self):
        """Test Karya adapter initialization"""
        config = {"enabled": True, "name": "Karya Adapter"}
        adapter = KaryaAdapter(config)
        assert adapter.enabled == True
        assert adapter.name == "Karya Adapter"
        print("✅ Karya adapter initialization test passed")
    
    def test_insightflow_adapter_initialization(self):
        """Test InsightFlow adapter initialization"""
        config = {"enabled": True, "name": "InsightFlow Adapter"}
        adapter = InsightFlowAdapter(config)
        assert adapter.enabled == True
        assert adapter.name == "InsightFlow Adapter"
        print("✅ InsightFlow adapter initialization test passed")
    
    def test_bucket_adapter_initialization(self):
        """Test Bucket adapter initialization"""
        config = {"enabled": True, "name": "Bucket Adapter"}
        adapter = BucketAdapter(config)
        assert adapter.enabled == True
        assert adapter.name == "Bucket Adapter"
        print("✅ Bucket adapter initialization test passed")
    
    def test_adapter_execution_disabled(self):
        """Test adapter execution when disabled"""
        config = {"enabled": False, "name": "Disabled Adapter"}
        adapter = ArthaAdapter(config)
        event = {"action": "test_action"}
        result = adapter.execute(event)
        assert result is None
        print("✅ Disabled adapter execution test passed")
    
    def test_adapter_manager_initialization(self):
        """Test adapter manager initialization"""
        configs = {
            "artha": {"enabled": True},
            "karya": {"enabled": True},
            "insightflow": {"enabled": True},
            "bucket": {"enabled": True}
        }
        manager = AdapterManager(configs)
        assert len(manager.adapters) == 4
        assert "artha" in manager.adapters
        assert "karya" in manager.adapters
        assert "insightflow" in manager.adapters
        assert "bucket" in manager.adapters
        print("✅ Adapter manager initialization test passed")
    
    def test_get_active_adapters(self):
        """Test getting active adapters"""
        configs = {
            "artha": {"enabled": True},
            "karya": {"enabled": False}
        }
        manager = AdapterManager(configs)
        active = manager.get_active_adapters()
        assert "artha" in active
        assert "karya" not in active
        print("✅ Get active adapters test passed")
    
    def test_execute_single_adapter(self):
        """Test executing a single adapter"""
        config = {"enabled": True, "name": "Test Adapter"}
        adapter = InsightFlowAdapter(config)
        event = {
            "action": "test_action",
            "event_id": "test_event_123",
            "timestamp": "2026-01-10T17:00:00Z"
        }
        result = adapter.execute(event)
        assert result is not None
        assert result["adapter"] == "insightflow"
        assert result["event_action"] == "test_action"
        assert result["success"] == True
        print("✅ Execute single adapter test passed")
    
    def test_adapter_manager_execute_all(self):
        """Test executing all adapters through manager"""
        configs = {
            "insightflow": {"enabled": True},
            "bucket": {"enabled": False}
        }
        manager = AdapterManager(configs)
        event = {
            "action": "test_action",
            "event_id": "test_event_123",
            "timestamp": "2026-01-10T17:00:00Z"
        }
        results = manager.execute_all_adapters(event)
        assert "insightflow" in results
        assert results["insightflow"] is not None
        assert "bucket" in results
        assert results["bucket"] is None
        print("✅ Execute all adapters through manager test passed")


if __name__ == "__main__":
    test_instance = TestAdapters()
    test_instance.test_base_adapter_initialization()
    test_instance.test_artha_adapter_initialization()
    test_instance.test_karya_adapter_initialization()
    test_instance.test_insightflow_adapter_initialization()
    test_instance.test_bucket_adapter_initialization()
    test_instance.test_adapter_execution_disabled()
    test_instance.test_adapter_manager_initialization()
    test_instance.test_get_active_adapters()
    test_instance.test_execute_single_adapter()
    test_instance.test_adapter_manager_execute_all()
    print("\n🎉 All Adapter tests completed!")