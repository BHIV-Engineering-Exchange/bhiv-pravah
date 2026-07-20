"""
Bucket contract validation utilities.

This module enforces API-boundary rules for Core-facing Bucket contract APIs.
It intentionally does not modify storage behavior.
"""

from datetime import datetime
import json
from typing import Any, Dict, Optional, Tuple


class ContractValidationError(Exception):
    """Raised when a request violates the Bucket contract."""

    def __init__(self, message: str, code: str = "contract_validation_error"):
        super().__init__(message)
        self.code = code


def utc_iso_timestamp() -> str:
    """Return UTC ISO8601 timestamp with Z suffix."""
    return datetime.utcnow().isoformat() + "Z"


def ensure_core_integration(integration_id: str) -> None:
    """Allow only Core integration identifiers."""
    if not integration_id:
        raise ContractValidationError("integration_id is required", "missing_integration_id")

    normalized = integration_id.strip().lower()
    allowed_exact = {"core", "bhiv_core", "bhiv-core"}
    allowed_prefixes = ("core_", "core-", "bhiv_core", "bhiv-core")

    if normalized in allowed_exact:
        return

    if normalized.startswith(allowed_prefixes):
        return

    raise ContractValidationError(
        "Integration boundary violation: only Core integration is allowed",
        "integration_boundary_violation",
    )


def ensure_payload_size_within_limit(payload_obj: Any, max_bytes: int) -> None:
    """Reject oversized payloads deterministically."""
    try:
        payload_bytes = len(json.dumps(payload_obj, separators=(",", ":")).encode("utf-8"))
    except Exception:
        raise ContractValidationError("Unable to evaluate payload size", "payload_size_check_failed")

    if payload_bytes > max_bytes:
        raise ContractValidationError(
            f"Payload size {payload_bytes} exceeds limit {max_bytes}",
            "payload_too_large",
        )


def ensure_lineage_request_valid(artifact: Dict[str, Any], expected_parent_hash: Optional[str]) -> None:
    """Validate lineage by checking parent hash against current chain state."""
    parent_hash = artifact.get("parent_hash")

    # First artifact in a chain
    if expected_parent_hash is None:
        if parent_hash is not None:
            raise ContractValidationError(
                "Invalid lineage: first artifact must not contain parent_hash",
                "invalid_lineage",
            )
        return

    # Subsequent artifacts must include exact parent hash
    if parent_hash != expected_parent_hash:
        raise ContractValidationError(
            f"Invalid lineage: expected parent_hash={expected_parent_hash}",
            "invalid_lineage",
        )


def artifact_matches_filters(
    artifact: Dict[str, Any],
    artifact_type: Optional[str] = None,
    source_module_id: Optional[str] = None,
) -> bool:
    """Apply deterministic artifact filtering for query endpoint."""
    if artifact_type and artifact.get("artifact_type") != artifact_type:
        return False
    if source_module_id and artifact.get("source_module_id") != source_module_id:
        return False
    return True


def filter_audit_entry(
    entry: Dict[str, Any],
    artifact_id: Optional[str],
    operation_type: Optional[str],
    status: Optional[str],
) -> bool:
    """Filter audit entries based on optional request criteria."""
    if artifact_id and entry.get("artifact_id") != artifact_id:
        return False
    if operation_type and entry.get("operation_type") != operation_type:
        return False
    if status and entry.get("status") != status:
        return False
    return True 