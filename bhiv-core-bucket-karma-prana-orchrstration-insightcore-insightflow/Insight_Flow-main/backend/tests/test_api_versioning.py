# tests/test_api_versioning.py

import pytest
from app.services.compatibility_service import CompatibilityService


class TestAPIVersioning:
    """Test API versioning and compatibility functionality"""
    
    def test_detect_ksml_format(self):
        """Test detection of KSML format"""
        service = CompatibilityService()
        
        ksml_data = {
            "meta": {
                "version": "1.0",
                "packet_type": "routing_request",
                "message_id": "msg-123"
            },
            "payload": {
                "data": {"test": "data"}
            }
        }
        
        version = service.detect_api_version(ksml_data)
        assert version == "ksml"
    
    def test_detect_core_v2_format(self):
        """Test detection of Core v2 format"""
        service = CompatibilityService()
        
        core_data = {
            "task_type": "nlp",
            "min_confidence": 0.8,
            "task_context": {"text": "hello"}
        }
        
        version = service.detect_api_version(core_data)
        assert version == "v2"
    
    def test_detect_legacy_v1_format(self):
        """Test detection of legacy v1 format"""
        service = CompatibilityService()
        
        legacy_data = {
            "input_data": {"text": "hello"},
            "input_type": "text",
            "strategy": "q_learning"
        }
        
        version = service.detect_api_version(legacy_data)
        assert version == "v1"
    
    def test_get_version_info(self):
        """Test version information retrieval"""
        service = CompatibilityService()
        
        info = service.get_version_info()
        
        assert "supported_versions" in info
        assert "v1" in info["supported_versions"]
        assert "v2" in info["supported_versions"]
        assert info["default_version"] == "v1"
        assert info["latest_version"] == "v2"
    
    def test_validate_version_compatibility(self):
        """Test version compatibility validation"""
        service = CompatibilityService()
        
        # Test compatible v1 data
        v1_data = {
            "input_data": {"text": "hello"},
            "input_type": "text"
        }
        
        is_compatible, message = service.validate_version_compatibility(v1_data, "v1")
        assert is_compatible is True
        
        # Test v2 data with v1 expectation (should be convertible)
        v2_data = {
            "task_type": "nlp",
            "min_confidence": 0.8
        }
        
        is_compatible, message = service.validate_version_compatibility(v2_data, "v1")
        assert is_compatible is True
        assert "Auto-converted" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])