"""
Append-Only Bucket Storage
Enforces write-once semantics with duplicate rejection
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

STORAGE_PATH = Path("data/bucket_artifacts.json")


def _ensure_storage():
    """Ensure storage file exists"""
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORAGE_PATH.exists():
        STORAGE_PATH.write_text("[]")


def append_artifact(artifact: Dict[str, Any]) -> None:
    """
    Append artifact to storage (write-once only)
    
    Raises:
        ValueError: If duplicate artifact_id detected
    """
    _ensure_storage()
    
    existing = json.loads(STORAGE_PATH.read_text())
    
    # Duplicate rejection
    duplicate = next((a for a in existing if a.get("artifact_id") == artifact.get("artifact_id")), None)
    if duplicate:
        raise ValueError(f"Duplicate artifact_id detected: {artifact.get('artifact_id')}")
    
    existing.append(artifact)
    STORAGE_PATH.write_text(json.dumps(existing, indent=2))
    logger.info(f"Artifact appended: {artifact.get('artifact_id')}")


def get_all_artifacts() -> List[Dict[str, Any]]:
    """Get all artifacts (read-only)"""
    _ensure_storage()
    return json.loads(STORAGE_PATH.read_text())


def get_artifact_by_id(artifact_id: str) -> Optional[Dict[str, Any]]:
    """Get artifact by ID (read-only)"""
    artifacts = get_all_artifacts()
    return next((a for a in artifacts if a.get("artifact_id") == artifact_id), None)


def get_artifact_by_hash(artifact_hash: str) -> Optional[Dict[str, Any]]:
    """Get artifact by hash (read-only)"""
    artifacts = get_all_artifacts()
    return next((a for a in artifacts if a.get("artifact_hash") == artifact_hash), None)
