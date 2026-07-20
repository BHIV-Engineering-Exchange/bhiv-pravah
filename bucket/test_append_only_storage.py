"""
Comprehensive Test Suite for Append-Only Storage System
========================================================

Tests verify:
1. Append-only storage behavior
2. Hash chain integrity
3. Server-side hash authority
4. Domain-agnostic validation
5. Backward compatibility
6. Tamper detection
7. Deterministic replay

Run: python test_append_only_storage.py
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from services.append_only_storage import AppendOnlyStorage


class TestAppendOnlyStorage:
    """Test suite for append-only storage system."""
    
    @pytest.fixture
    def storage(self):
        """Create temporary storage for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AppendOnlyStorage(storage_path=tmpdir)
            yield storage
    
    @pytest.fixture
    def sample_artifact(self):
        """Create sample artifact for testing."""
        return {
            "artifact_id": "TEST001",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "schema_version": "1.0.0",
            "source_module_id": "test_module",
            "artifact_type": "test_type",
            "payload": {
                "test_data": "sample"
            }
        }
    
    # ========================================================================
    # DAY 1 TESTS: Append-Only Storage
    # ========================================================================
    
    def test_append_only_write(self, storage, sample_artifact):
        """Test that artifacts are appended, not rewritten."""
        # Store first artifact
        result1 = storage.store_artifact(sample_artifact)
        
        # Verify stored
        assert result1["artifact_id"] == "TEST001"
        assert "hash" in result1
        
        # Store second artifact
        artifact2 = sample_artifact.copy()
        artifact2["artifact_id"] = "TEST002"
        artifact2["parent_hash"] = result1["hash"]
        
        result2 = storage.store_artifact(artifact2)
        
        # Verify both exist
        assert storage.get_artifact("TEST001") is not None
        assert storage.get_artifact("TEST002") is not None
        
        # Verify log file has 2 lines
        with open(storage.log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
    
    def test_duplicate_rejection(self, storage, sample_artifact):
        """Test that duplicate artifact_id is rejected."""
        # Store first time
        storage.store_artifact(sample_artifact)
        
        # Try to store again with same artifact_id
        with pytest.raises(ValueError, match="Duplicate artifact_id"):
            storage.store_artifact(sample_artifact)
    
    def test_independent_records(self, storage, sample_artifact):
        """Test that each artifact is independent record."""
        # Store multiple artifacts
        artifacts = []
        for i in range(5):
            artifact = sample_artifact.copy()
            artifact["artifact_id"] = f"TEST{i:03d}"
            if i > 0:
                artifact["parent_hash"] = artifacts[-1]["hash"]
            result = storage.store_artifact(artifact)
            artifacts.append(result)
        
        # Verify each can be read independently
        for artifact in artifacts:
            retrieved = storage.get_artifact(artifact["artifact_id"])
            assert retrieved is not None
            assert retrieved["artifact_id"] == artifact["artifact_id"]
    
    def test_no_modification_after_write(self, storage, sample_artifact):
        """Test that artifacts cannot be modified after write."""
        # Store artifact
        result = storage.store_artifact(sample_artifact)
        original_hash = result["hash"]
        
        # Try to modify (should not be possible through API)
        # Verify hash remains same
        retrieved = storage.get_artifact("TEST001")
        assert retrieved["hash"] == original_hash
    
    # ========================================================================
    # DAY 2 TESTS: Hash Chain Integrity
    # ========================================================================
    
    def test_genesis_artifact_no_parent(self, storage, sample_artifact):
        """Test that first artifact has no parent_hash."""
        # First artifact should not have parent_hash
        result = storage.store_artifact(sample_artifact)
        
        assert result.get("parent_hash") is None
    
    def test_subsequent_artifacts_require_parent(self, storage, sample_artifact):
        """Test that subsequent artifacts must have parent_hash."""
        # Store first artifact
        result1 = storage.store_artifact(sample_artifact)
        
        # Try to store second without parent_hash
        artifact2 = sample_artifact.copy()
        artifact2["artifact_id"] = "TEST002"
        # Don't set parent_hash
        
        with pytest.raises(ValueError, match="parent_hash required"):
            storage.store_artifact(artifact2)
    
    def test_parent_hash_must_match_previous(self, storage, sample_artifact):
        """Test that parent_hash must match previous artifact's hash."""
        # Store first artifact
        result1 = storage.store_artifact(sample_artifact)
        
        # Try to store second with wrong parent_hash
        artifact2 = sample_artifact.copy()
        artifact2["artifact_id"] = "TEST002"
        artifact2["parent_hash"] = "wrong_hash"
        
        with pytest.raises(ValueError, match="Invalid parent_hash"):
            storage.store_artifact(artifact2)
    
    def test_orphan_rejection(self, storage, sample_artifact):
        """Test that orphan artifacts are rejected."""
        # Store first artifact
        result1 = storage.store_artifact(sample_artifact)
        
        # Try to create orphan (parent doesn't exist)
        artifact2 = sample_artifact.copy()
        artifact2["artifact_id"] = "TEST002"
        artifact2["parent_hash"] = "nonexistent_hash"
        
        with pytest.raises(ValueError):
            storage.store_artifact(artifact2)
    
    def test_chain_validation(self, storage, sample_artifact):
        """Test full chain integrity validation."""
        # Build chain of 5 artifacts
        artifacts = []
        for i in range(5):
            artifact = sample_artifact.copy()
            artifact["artifact_id"] = f"TEST{i:03d}"
            if i > 0:
                artifact["parent_hash"] = artifacts[-1]["hash"]
            result = storage.store_artifact(artifact)
            artifacts.append(result)
        
        # Validate chain
        is_valid, errors = storage.validate_chain_integrity()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_tamper_detection(self, storage, sample_artifact):
        """Test that tampering is detected."""
        # Store artifacts
        result1 = storage.store_artifact(sample_artifact)
        
        artifact2 = sample_artifact.copy()
        artifact2["artifact_id"] = "TEST002"
        artifact2["parent_hash"] = result1["hash"]
        storage.store_artifact(artifact2)
        
        # Manually tamper with log file
        with open(storage.log_file, 'r') as f:
            lines = f.readlines()
        
        # Modify first artifact
        artifact = json.loads(lines[0])
        artifact["payload"]["test_data"] = "TAMPERED"
        lines[0] = json.dumps(artifact) + '\n'
        
        with open(storage.log_file, 'w') as f:
            f.writelines(lines)
        
        # Validate chain - should detect tampering
        is_valid, errors = storage.validate_chain_integrity()
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Hash mismatch" in errors[0]
    
    # ========================================================================
    # DAY 2 TESTS: Hash Authority
    # ========================================================================
    
    def test_server_computes_hash(self, storage, sample_artifact):
        """Test that server computes hash, not client."""
        # Client sends artifact WITHOUT hash
        assert "hash" not in sample_artifact
        
        # Server stores and computes hash
        result = storage.store_artifact(sample_artifact)
        
        # Server returns computed hash
        assert "hash" in result
        assert len(result["hash"]) == 64  # SHA256 hex
    
    def test_client_hash_ignored(self, storage, sample_artifact):
        """Test that client-provided hash is ignored."""
        # Client tries to provide hash
        sample_artifact["hash"] = "fake_client_hash"
        
        # Server ignores it and computes own
        result = storage.store_artifact(sample_artifact)
        
        # Server hash is different
        assert result["hash"] != "fake_client_hash"
        assert len(result["hash"]) == 64
    
    def test_deterministic_hashing(self, storage, sample_artifact):
        """Test that same artifact produces same hash."""
        # Compute hash twice
        hash1 = storage.compute_hash(sample_artifact)
        hash2 = storage.compute_hash(sample_artifact)
        
        # Should be identical
        assert hash1 == hash2
    
    def test_hash_includes_all_fields(self, storage, sample_artifact):
        """Test that hash includes all metadata and payload."""
        # Compute original hash
        hash1 = storage.compute_hash(sample_artifact)
        
        # Modify payload
        sample_artifact["payload"]["test_data"] = "modified"
        hash2 = storage.compute_hash(sample_artifact)
        
        # Hash should change
        assert hash1 != hash2
    
    # ========================================================================
    # DAY 3 TESTS: Domain-Agnostic Validation
    # ========================================================================
    
    def test_required_metadata_fields(self, storage, sample_artifact):
        """Test that required metadata fields are enforced."""
        # Remove required field
        del sample_artifact["timestamp_utc"]
        
        # Should be rejected
        with pytest.raises(ValueError, match="Missing required field"):
            storage.store_artifact(sample_artifact)
    
    def test_unknown_envelope_fields_rejected(self, storage, sample_artifact):
        """Test that unknown envelope fields are rejected."""
        # Add unknown field
        sample_artifact["unknown_field"] = "value"
        
        # Should be rejected
        with pytest.raises(ValueError, match="Unknown envelope field"):
            storage.store_artifact(sample_artifact)
    
    def test_schema_version_validation(self, storage, sample_artifact):
        """Test that schema version is validated."""
        # Use wrong schema version
        sample_artifact["schema_version"] = "2.0.0"
        
        # Should be rejected
        with pytest.raises(ValueError, match="Invalid schema version"):
            storage.store_artifact(sample_artifact)
    
    def test_payload_size_limit(self, storage, sample_artifact):
        """Test that payload size limit is enforced."""
        # Create large payload (> 16MB)
        large_data = "x" * (17 * 1024 * 1024)  # 17MB
        sample_artifact["payload"] = {"large_data": large_data}
        
        # Should be rejected
        with pytest.raises(ValueError, match="Payload size.*exceeds limit"):
            storage.store_artifact(sample_artifact)
    
    def test_no_payload_interpretation(self, storage, sample_artifact):
        """Test that payload content is NOT interpreted."""
        # Payload with domain-specific data
        sample_artifact["payload"] = {
            "crop_health": "poor",
            "yield_prediction": 1200,
            "recommendation": "irrigate"
        }
        
        # Should be accepted (no interpretation)
        result = storage.store_artifact(sample_artifact)
        
        assert result is not None
        assert "hash" in result
    
    def test_structure_validation_only(self, storage, sample_artifact):
        """Test that only structure is validated, not content."""
        # Valid structure, arbitrary content
        sample_artifact["payload"] = {
            "arbitrary_field_1": "value1",
            "arbitrary_field_2": 12345,
            "arbitrary_field_3": [1, 2, 3],
            "arbitrary_field_4": {"nested": "data"}
        }
        
        # Should be accepted
        result = storage.store_artifact(sample_artifact)
        
        assert result is not None
    
    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================
    
    def test_aiaic_satellite_analysis_ingestion(self, storage):
        """Test ingestion of AIAIC satellite analysis artifact."""
        artifact = {
            "artifact_id": "aiaic_sat_20250120_001",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "schema_version": "1.0.0",
            "source_module_id": "aiaic_satellite_processor",
            "artifact_type": "satellite_analysis",
            "payload": {
                "satellite_image_id": "IMG_12345",
                "analysis_output": {
                    "vegetation_index": 0.75,
                    "crop_health_metrics": {"metric1": 0.8},
                    "anomaly_detection": {"detected": False}
                },
                "processing_metadata": {
                    "model_version": "2.1.0",
                    "processing_time_ms": 1234
                }
            }
        }
        
        # Should be accepted
        result = storage.store_artifact(artifact)
        
        assert result is not None
        assert result["artifact_id"] == "aiaic_sat_20250120_001"
    
    def test_marine_sensor_telemetry_ingestion(self, storage):
        """Test ingestion of Marine sensor telemetry artifact."""
        artifact = {
            "artifact_id": "marine_sensor_20250120_001",
            "timestamp_utc": datetime.utcnow().isoformat() + "Z",
            "schema_version": "1.0.0",
            "source_module_id": "marine_iot_gateway",
            "artifact_type": "sensor_telemetry",
            "payload": {
                "sensor_id": "SENSOR_789",
                "readings": {
                    "temperature_celsius": 23.5,
                    "salinity_ppt": 35.2,
                    "ph_level": 8.1,
                    "dissolved_oxygen_mg_l": 7.8
                },
                "location": {
                    "latitude": 12.9716,
                    "longitude": 77.5946
                }
            }
        }
        
        # Should be accepted
        result = storage.store_artifact(artifact)
        
        assert result is not None
        assert result["artifact_id"] == "marine_sensor_20250120_001"
    
    def test_deterministic_replay(self, storage, sample_artifact):
        """Test that replay is deterministic."""
        # Build chain
        artifacts = []
        for i in range(10):
            artifact = sample_artifact.copy()
            artifact["artifact_id"] = f"TEST{i:03d}"
            if i > 0:
                artifact["parent_hash"] = artifacts[-1]["hash"]
            result = storage.store_artifact(artifact)
            artifacts.append(result)
        
        # Replay chain
        replayed = []
        with open(storage.log_file, 'r') as f:
            for line in f:
                replayed.append(json.loads(line))
        
        # Verify order
        for i, artifact in enumerate(replayed):
            assert artifact["artifact_id"] == f"TEST{i:03d}"
    
    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================
    
    def test_high_volume_ingestion(self, storage, sample_artifact):
        """Test ingestion of many artifacts."""
        import time
        
        start_time = time.time()
        
        # Ingest 1000 artifacts
        artifacts = []
        for i in range(1000):
            artifact = sample_artifact.copy()
            artifact["artifact_id"] = f"PERF{i:04d}"
            if i > 0:
                artifact["parent_hash"] = artifacts[-1]["hash"]
            result = storage.store_artifact(artifact)
            artifacts.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 60  # Less than 60 seconds
        
        # Verify all stored
        stats = storage.get_storage_stats()
        assert stats["artifact_count"] == 1000


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
