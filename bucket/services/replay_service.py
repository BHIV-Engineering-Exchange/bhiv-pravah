"""
Replay Validation Service
Verifies artifact chain integrity and detects tampering
"""

from typing import Dict, Any, List, Tuple
from services.bucket_store import get_all_artifacts
from services.hash_service import compute_artifact_hash
from utils.logger import get_logger

logger = get_logger(__name__)


def validate_replay() -> Tuple[bool, List[str]]:
    """
    Validate entire artifact chain for integrity
    
    Returns:
        (is_valid, errors)
    """
    artifacts = get_all_artifacts()
    errors = []
    
    for i, artifact in enumerate(artifacts):
        # Verify hash integrity
        computed_hash = compute_artifact_hash(artifact)
        if computed_hash != artifact.get("artifact_hash"):
            errors.append(f"Tampering detected at index {i}, artifact_id: {artifact.get('artifact_id')}")
        
        # Verify parent chain
        parent_hash = artifact.get("parent_hash")
        if parent_hash:
            parent = next((a for a in artifacts if a.get("artifact_hash") == parent_hash), None)
            if not parent:
                errors.append(f"Broken parent chain at artifact_id: {artifact.get('artifact_id')}")
    
    is_valid = len(errors) == 0
    if is_valid:
        logger.info(f"Replay validation passed for {len(artifacts)} artifacts")
    else:
        logger.error(f"Replay validation failed with {len(errors)} errors")
    
    return is_valid, errors


def validate_artifact_chain(artifact_id: str) -> Tuple[bool, List[str]]:
    """Validate chain from specific artifact backwards"""
    artifacts = get_all_artifacts()
    artifact = next((a for a in artifacts if a.get("artifact_id") == artifact_id), None)
    
    if not artifact:
        return False, [f"Artifact not found: {artifact_id}"]
    
    errors = []
    current = artifact
    
    while current:
        computed_hash = compute_artifact_hash(current)
        if computed_hash != current.get("artifact_hash"):
            errors.append(f"Hash mismatch at: {current.get('artifact_id')}")
        
        parent_hash = current.get("parent_hash")
        if not parent_hash:
            break
        
        current = next((a for a in artifacts if a.get("artifact_hash") == parent_hash), None)
        if not current:
            errors.append(f"Missing parent: {parent_hash}")
            break
    
    return len(errors) == 0, errors
