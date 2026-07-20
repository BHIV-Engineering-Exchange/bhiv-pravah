"""
Bucket Service - Append-Only Artifact Storage
Enforces all integrity constraints
"""

from typing import Dict, Any
from services.bucket_store import append_artifact, get_artifact_by_id, get_all_artifacts
from services.hash_service import compute_artifact_hash, verify_artifact_hash
from services.artifact_schema import validate_artifact
from utils.logger import get_logger

logger = get_logger(__name__)


def store_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store artifact with full validation and enforcement
    
    Raises:
        ValueError: If validation fails
    """
    
    # 1. Schema validation
    is_valid, errors = validate_artifact(artifact)
    if not is_valid:
        raise ValueError(f"Validation failed: {', '.join(errors)}")
    
    # 2. Hash verification
    if not verify_artifact_hash(artifact):
        computed = compute_artifact_hash(artifact)
        provided = artifact.get("artifact_hash")
        raise ValueError(f"artifact_hash mismatch. Expected: {computed}, Got: {provided}")
    
    # 3. Append to storage (duplicate check inside)
    append_artifact(artifact)
    
    logger.info(f"Artifact stored successfully: {artifact.get('artifact_id')}")
    
    return {
        "success": True,
        "artifact_id": artifact.get("artifact_id"),
        "artifact_hash": artifact.get("artifact_hash")
    }


def get_artifact(artifact_id: str) -> Dict[str, Any]:
    """Get artifact by ID (read-only)"""
    artifact = get_artifact_by_id(artifact_id)
    if not artifact:
        raise ValueError(f"Artifact not found: {artifact_id}")
    return artifact


def list_artifacts(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """List artifacts (read-only)"""
    artifacts = get_all_artifacts()
    total = len(artifacts)
    paginated = artifacts[offset:offset + limit]
    
    return {
        "artifacts": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }
