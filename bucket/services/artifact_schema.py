"""
Artifact Schema Validation and Envelope Enforcement
Enforces mandatory fields and artifact type classification
"""

from typing import Dict, Any, List
from datetime import datetime


REQUIRED_ENVELOPE_FIELDS = [
    "artifact_id",
    "source_module_id",
    "schema_version",
    "artifact_hash",
    "timestamp_utc",
    "artifact_type"
]

ALLOWED_ARTIFACT_TYPES = [
    "truth_event",
    "projection_event",
    "registry_snapshot",
    "policy_snapshot",
    "replay_proof",
    "telemetry_record"
]

ALLOWED_SCHEMA_VERSIONS = ["1.0.0"]


def validate_envelope(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """Validate artifact envelope has all required fields"""
    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in artifact:
            return False, f"Missing required field: {field}"
    return True, ""


def validate_artifact_type(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """Validate artifact type is in allowed list"""
    artifact_type = artifact.get("artifact_type")
    if artifact_type not in ALLOWED_ARTIFACT_TYPES:
        return False, f"Invalid artifact_type: {artifact_type}. Allowed: {ALLOWED_ARTIFACT_TYPES}"
    return True, ""


def validate_schema_version(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """Validate schema version is supported"""
    schema_version = artifact.get("schema_version")
    if schema_version not in ALLOWED_SCHEMA_VERSIONS:
        return False, f"Unsupported schema_version: {schema_version}. Allowed: {ALLOWED_SCHEMA_VERSIONS}"
    return True, ""


def validate_parent_hash(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """Validate parent_hash if required"""
    if artifact.get("parent_required") and not artifact.get("parent_hash"):
        return False, "Missing parent_hash for chained artifact"
    return True, ""


def validate_replay_proof(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """Validate replay_proof has input_hash"""
    if artifact.get("artifact_type") == "replay_proof" and not artifact.get("input_hash"):
        return False, "replay_proof requires input_hash"
    return True, ""


def validate_artifact(artifact: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Run all validations on artifact"""
    errors = []
    
    validations = [
        validate_envelope,
        validate_artifact_type,
        validate_schema_version,
        validate_parent_hash,
        validate_replay_proof
    ]
    
    for validation_func in validations:
        valid, error = validation_func(artifact)
        if not valid:
            errors.append(error)
    
    return len(errors) == 0, errors
