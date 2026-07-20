"""Telemetry payload validation schema."""

from __future__ import annotations

from jsonschema import ValidationError, validate

from src.core.failure_handler import FailureHandler

TELEMETRY_SCHEMA = {
    "type": "object",
    "required": ["source_id", "metric", "value", "unit", "timestamp"],
    "properties": {
        "source_id": {"type": "string"},
        "metric": {"type": "string"},
        "value": {"type": "number"},
        "unit": {"type": "string"},
        "timestamp": {"type": "string"},
        "site": {"type": "string"},
    },
    "additionalProperties": True,
}


def validate_telemetry(payload: dict) -> tuple[bool, str | None]:
    """Validate telemetry payload against schema."""
    try:
        validate(instance=payload, schema=TELEMETRY_SCHEMA)
        return True, None
    except ValidationError as exc:
        failure = FailureHandler().handle_validation_error("telemetry_payload", exc.message)
        return False, failure.get("message")
