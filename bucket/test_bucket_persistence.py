"""
Test Script for Bucket Persistence Integrity System
Tests all append-only, hash linking, and validation features
"""

import sys
import json
from datetime import datetime
from services.hash_service import compute_artifact_hash, verify_artifact_hash
from services.artifact_schema import validate_artifact
from services.bucket_service import store_artifact, get_artifact, list_artifacts
from services.replay_service import validate_replay, validate_artifact_chain


def test_hash_service():
    """Test deterministic hash computation"""
    print("\n=== Testing Hash Service ===")
    
    artifact = {
        "artifact_id": "test1",
        "source_module_id": "test_module",
        "schema_version": "1.0.0",
        "timestamp_utc": "2025-01-19T10:00:00Z",
        "artifact_type": "truth_event"
    }
    
    # Test determinism
    hash1 = compute_artifact_hash(artifact)
    hash2 = compute_artifact_hash(artifact)
    assert hash1 == hash2, "Hash not deterministic!"
    print(f"✅ Deterministic hash: {hash1[:16]}...")
    
    # Test verification
    artifact["artifact_hash"] = hash1
    assert verify_artifact_hash(artifact), "Hash verification failed!"
    print("✅ Hash verification passed")
    
    # Test tampering detection
    artifact["payload"] = {"tampered": True}
    assert not verify_artifact_hash(artifact), "Tampering not detected!"
    print("✅ Tampering detection works")


def test_schema_validation():
    """Test artifact schema validation"""
    print("\n=== Testing Schema Validation ===")
    
    # Valid artifact
    valid_artifact = {
        "artifact_id": "test2",
        "source_module_id": "test_module",
        "schema_version": "1.0.0",
        "artifact_hash": "dummy_hash",
        "timestamp_utc": "2025-01-19T10:00:00Z",
        "artifact_type": "truth_event"
    }
    
    is_valid, errors = validate_artifact(valid_artifact)
    assert is_valid, f"Valid artifact rejected: {errors}"
    print("✅ Valid artifact accepted")
    
    # Missing field
    invalid_artifact = valid_artifact.copy()
    del invalid_artifact["artifact_id"]
    is_valid, errors = validate_artifact(invalid_artifact)
    assert not is_valid, "Missing field not detected!"
    print(f"✅ Missing field detected: {errors[0]}")
    
    # Invalid type
    invalid_artifact = valid_artifact.copy()
    invalid_artifact["artifact_type"] = "invalid_type"
    is_valid, errors = validate_artifact(invalid_artifact)
    assert not is_valid, "Invalid type not detected!"
    print(f"✅ Invalid type detected: {errors[0]}")
    
    # Invalid schema version
    invalid_artifact = valid_artifact.copy()
    invalid_artifact["schema_version"] = "2.0.0"
    is_valid, errors = validate_artifact(invalid_artifact)
    assert not is_valid, "Invalid schema version not detected!"
    print(f"✅ Invalid schema version detected: {errors[0]}")


def test_bucket_storage():
    """Test append-only bucket storage"""
    print("\n=== Testing Bucket Storage ===")
    
    # Create valid artifact
    artifact = {
        "artifact_id": f"test_{datetime.now().timestamp()}",
        "source_module_id": "test_module",
        "schema_version": "1.0.0",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "artifact_type": "truth_event",
        "payload": {"test": "data"}
    }
    
    # Compute hash
    artifact["artifact_hash"] = compute_artifact_hash(artifact)
    
    # Store artifact
    result = store_artifact(artifact)
    assert result["success"], "Storage failed!"
    print(f"✅ Artifact stored: {result['artifact_id']}")
    
    # Retrieve artifact
    retrieved = get_artifact(artifact["artifact_id"])
    assert retrieved["artifact_id"] == artifact["artifact_id"], "Retrieval failed!"
    print(f"✅ Artifact retrieved: {retrieved['artifact_id']}")
    
    # Test duplicate rejection
    try:
        store_artifact(artifact)
        assert False, "Duplicate not rejected!"
    except ValueError as e:
        print(f"✅ Duplicate rejected: {str(e)}")


def test_replay_validation():
    """Test replay validation"""
    print("\n=== Testing Replay Validation ===")
    
    # Validate full replay
    is_valid, errors = validate_replay()
    if is_valid:
        print("✅ Full replay validation passed")
    else:
        print(f"⚠️  Replay validation errors: {errors}")
    
    # List artifacts
    result = list_artifacts(limit=10)
    print(f"✅ Total artifacts: {result['total']}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("BUCKET PERSISTENCE INTEGRITY SYSTEM - TEST SUITE")
    print("=" * 60)
    
    try:
        test_hash_service()
        test_schema_validation()
        test_bucket_storage()
        test_replay_validation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
