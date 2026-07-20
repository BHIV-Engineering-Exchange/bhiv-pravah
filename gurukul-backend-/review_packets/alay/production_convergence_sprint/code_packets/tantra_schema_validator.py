"""
tantra_schema_validator.py — Strict Contract Enforcer for TANTRA Payloads
==========================================================================

Validates Pravah and Bucket payloads before transmission.
Rules:
  - All required fields must be present
  - Field types must be exact
  - No extra keys allowed (strict contract)
  - Violations are logged and raise ContractViolationError
"""

import logging
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger("TantraSchemaValidator")


class ContractViolationError(Exception):
    """Raised when a payload violates the TANTRA contract schema."""
    def __init__(self, connector: str, reason: str, payload_preview: str = ""):
        self.connector = connector
        self.reason = reason
        self.payload_preview = payload_preview
        super().__init__(f"[{connector}] Contract violation: {reason}")


# ── Pravah Signal Schema ───────────────────────────────────────────────────
PRAVAH_REQUIRED_FIELDS: Dict[str, type] = {
    "source":                 str,
    "trace_id":               str,
    "timestamp":              str,
    "event_type":             str,
    "action":                 str,
    "status":                 str,
    "payload":                dict,
    "schema_version":         str,
    "provenance":             str,
    "ownership":              str,
    "replay_metadata":        dict,
    "event_signature":        str,
    "source_verification":    str,
    "trace_chain_validation":  str,
    "integrity_hash":         str,
}

# ── Bucket Memory Schema ───────────────────────────────────────────────────
BUCKET_REQUIRED_FIELDS: Dict[str, type] = {
    "trace_id":        str,
    "user_id":         str,
    "session_id":      str,
    "action":          str,
    "outcome":         str,
    "payload":         dict,
    "timestamp":       str,
    "source":          str,
    "prev_hash":       str,
    "current_hash":    str,
    "schema_version":  str,
    "provenance":      str,
    "ownership":       str,
    "replay_metadata": dict,
}


def _validate(connector: str, payload: Dict[str, Any], schema: Dict[str, type]) -> None:
    """
    Core validation logic.
    Raises ContractViolationError on:
      - Missing required field
      - Wrong field type
      - Extra keys not in schema
    """
    preview = str(payload)[:120]

    # 1. Check required fields + types
    for field, expected_type in schema.items():
        if field not in payload:
            logger.error(f"[{connector}] CONTRACT VIOLATION — missing field: '{field}' | payload={preview}")
            raise ContractViolationError(connector, f"missing required field: '{field}'", preview)

        value = payload[field]
        if not isinstance(value, expected_type):
            logger.error(
                f"[{connector}] CONTRACT VIOLATION — field '{field}' expected {expected_type.__name__}, "
                f"got {type(value).__name__} | payload={preview}"
            )
            raise ContractViolationError(
                connector,
                f"field '{field}' must be {expected_type.__name__}, got {type(value).__name__}",
                preview,
            )

    # 2. No extra keys
    extra_keys = set(payload.keys()) - set(schema.keys())
    if extra_keys:
        logger.error(f"[{connector}] CONTRACT VIOLATION — extra keys not allowed: {extra_keys} | payload={preview}")
        raise ContractViolationError(connector, f"extra keys not allowed: {extra_keys}", preview)

    # 3. Validate timestamp is valid ISO-8601
    for field in ("timestamp",):
        if field in payload and field in schema:
            try:
                datetime.fromisoformat(payload[field].replace("Z", "+00:00"))
            except Exception:
                raise ContractViolationError(connector, f"'{field}' is not a valid ISO-8601 timestamp")

    logger.debug(f"[{connector}] Schema validation passed.")


def validate_pravah_payload(payload: Dict[str, Any]) -> None:
    """Validate a Pravah signal payload. Raises ContractViolationError if invalid."""
    _validate("Pravah", payload, PRAVAH_REQUIRED_FIELDS)

    # Cryptographic & Integrity Verification
    import hmac
    import hashlib
    from app.services.prana_determinism import prana_determinism
    from app.core.config import settings

    # 1. Integrity Hash verification
    computed_hash = prana_determinism.hash_payload(payload)
    if payload.get("integrity_hash") != computed_hash:
        logger.error(f"[Pravah] INTEGRITY HASH MISMATCH | Stored: {payload.get('integrity_hash')} | Computed: {computed_hash}")
        raise ContractViolationError("Pravah", f"integrity_hash mismatch: expected {computed_hash}, got {payload.get('integrity_hash')}")

    # 2. Event Signature verification
    api_key = getattr(settings, "TANTRA_API_KEY", None)
    if not api_key:
        logger.error("[Pravah] TANTRA_API_KEY is not configured in production settings.")
        raise ContractViolationError("Pravah", "TANTRA_API_KEY is missing (debug HMAC fallbacks are disabled in production)")
    expected_signature = hmac.new(
        api_key.encode("utf-8") if isinstance(api_key, str) else api_key,
        computed_hash.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    if payload.get("event_signature") != expected_signature:
        logger.error("[Pravah] SIGNATURE VERIFICATION FAILED")
        raise ContractViolationError("Pravah", "event_signature verification failed (invalid signature)")


def validate_bucket_payload(payload: Dict[str, Any]) -> None:
    """Validate a Bucket memory payload. Raises ContractViolationError if invalid."""
    _validate("Bucket", payload, BUCKET_REQUIRED_FIELDS)
