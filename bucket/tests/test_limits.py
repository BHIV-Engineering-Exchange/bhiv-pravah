"""
Unit Tests for BHIV Bucket Scale Limits
Tests all scale boundaries and validation functions
"""

import pytest
from config.limits import (
    BucketLimits,
    PRODUCT_QUOTAS,
    PRODUCT_ARTIFACT_ALLOWLIST,
    validate_product_quota,
    validate_product_artifact_type
)

class TestArtifactSizeValidation:
    """Test artifact size validation"""
    
    def test_valid_artifact_size(self):
        """Test artifact within size limit"""
        valid, msg = BucketLimits.validate_artifact_size(100_000_000)  # 100MB
        assert valid == True
        assert "within limits" in msg
    
    def test_max_artifact_size(self):
        """Test artifact at exact limit"""
        valid, msg = BucketLimits.validate_artifact_size(BucketLimits.MAX_ARTIFACT_SIZE_BYTES)
        assert valid == True
    
    def test_oversized_artifact(self):
        """Test artifact exceeding limit"""
        valid, msg = BucketLimits.validate_artifact_size(600_000_000)  # 600MB
        assert valid == False
        assert "exceeds limit" in msg

class TestStorageCapacity:
    """Test storage capacity monitoring"""
    
    def test_healthy_storage(self):
        """Test storage at 50% capacity"""
        status = BucketLimits.check_storage_capacity(500)  # 50%
        assert status["status"] == "HEALTHY"
        assert status["action_required"] == "NONE"
    
    def test_caution_storage(self):
        """Test storage at 75% capacity"""
        status = BucketLimits.check_storage_capacity(750)  # 75%
        assert status["status"] == "CAUTION"
        assert status["escalation_path"] == "Ops_Team"
    
    def test_warning_storage(self):
        """Test storage at 95% capacity"""
        status = BucketLimits.check_storage_capacity(950)  # 95%
        assert status["status"] == "WARNING"
        assert status["response_timeline"] == "6_HOURS"
    
    def test_critical_storage(self):
        """Test storage at 99% capacity"""
        status = BucketLimits.check_storage_capacity(990)  # 99%
        assert status["status"] == "CRITICAL"
        assert status["action_required"] == "HALT_WRITES"
        assert status["response_timeline"] == "IMMEDIATE"

class TestConcurrentWrites:
    """Test concurrent writes monitoring"""
    
    def test_safe_concurrent_writes(self):
        """Test safe level of concurrent writes"""
        status = BucketLimits.check_concurrent_writes(30)
        assert status["status"] == "GREEN"
        assert status["action"] == "NONE"
    
    def test_elevated_concurrent_writes(self):
        """Test elevated concurrent writes"""
        status = BucketLimits.check_concurrent_writes(60)
        assert status["status"] == "YELLOW"
        assert status["action"] == "MONITOR"
    
    def test_warning_concurrent_writes(self):
        """Test warning level concurrent writes"""
        status = BucketLimits.check_concurrent_writes(80)
        assert status["status"] == "ORANGE"
        assert status["action"] == "ALERT_OPS"
    
    def test_critical_concurrent_writes(self):
        """Test critical concurrent writes"""
        status = BucketLimits.check_concurrent_writes(100)
        assert status["status"] == "RED"
        assert status["action"] == "PAUSE_NEW_WRITES"

class TestProductQuotas:
    """Test product quota validation"""
    
    def test_valid_product_quota(self):
        """Test product within quota"""
        valid, msg = validate_product_quota("AI_ASSISTANT", 100_000_000_000)  # 100GB
        assert valid == True
    
    def test_product_quota_warning(self):
        """Test product approaching quota"""
        valid, msg = validate_product_quota("AI_ASSISTANT", 370_000_000_000)  # 92.5%
        assert valid == True
        assert "WARNING" in msg
    
    def test_product_quota_exceeded(self):
        """Test product exceeding quota"""
        valid, msg = validate_product_quota("AI_ASSISTANT", 450_000_000_000)  # Over 400GB
        assert valid == False
        assert "exceeded" in msg
    
    def test_unregistered_product(self):
        """Test unregistered product"""
        valid, msg = validate_product_quota("UNKNOWN_PRODUCT", 100_000_000_000)
        assert valid == False
        assert "not registered" in msg

class TestProductArtifactTypes:
    """Test product artifact type validation"""
    
    def test_valid_artifact_type(self):
        """Test valid artifact type for product"""
        valid, msg = validate_product_artifact_type("AI_ASSISTANT", "ConversationArtifact")
        assert valid == True
    
    def test_invalid_artifact_type(self):
        """Test invalid artifact type for product"""
        valid, msg = validate_product_artifact_type("AI_ASSISTANT", "MediaArtifact")
        assert valid == False
        assert "not allowed" in msg
    
    def test_unregistered_product_artifact(self):
        """Test artifact type for unregistered product"""
        valid, msg = validate_product_artifact_type("UNKNOWN", "SomeArtifact")
        assert valid == False
        assert "not registered" in msg

class TestMetadataValidation:
    """Test metadata size validation"""
    
    def test_valid_metadata_size(self):
        """Test metadata within size limit"""
        valid, msg = BucketLimits.validate_metadata_size(8000)  # 8KB
        assert valid == True
    
    def test_oversized_metadata(self):
        """Test metadata exceeding limit"""
        valid, msg = BucketLimits.validate_metadata_size(20000)  # 20KB
        assert valid == False
        assert "exceeds limit" in msg

class TestGetAllLimits:
    """Test getting all limits"""
    
    def test_get_all_limits_structure(self):
        """Test all limits return correct structure"""
        limits = BucketLimits.get_all_limits()
        assert "storage" in limits
        assert "performance" in limits
        assert "artifacts" in limits
        assert "query" in limits
        assert "audit" in limits
    
    def test_storage_limits_values(self):
        """Test storage limits have correct values"""
        limits = BucketLimits.get_all_limits()
        assert limits["storage"]["max_artifact_size_mb"] == 500
        assert limits["storage"]["max_total_storage_gb"] == 1000
    
    def test_performance_limits_values(self):
        """Test performance limits have correct values"""
        limits = BucketLimits.get_all_limits()
        assert limits["performance"]["max_concurrent_writes"] == 100
        assert limits["performance"]["max_write_throughput_per_sec"] == 1000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
