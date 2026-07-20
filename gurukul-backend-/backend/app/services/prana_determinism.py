import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict


UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
ISO_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
EXCLUDED_EXACT_KEYS = {
    "event_id",
    "validation_id",
    "created_at",
    "updated_at",
    "received_at",
    "logged_at",
    "last_seen",
    "freshness_timestamp",
    "event_timestamp",
    "replay_timestamp",
    "determinism_hash",
    "hash",
    "integrity_hash",
    "event_signature",
    "source_verification",
    "trace_chain_validation",
}


class PranaDeterminismService:
    """
    Stable PRANA hashing boundary.

    Rules:
    - Sort dictionary keys recursively
    - Strip nondeterministic timestamp/UUID fields before hashing
    - Normalize floats so 1, 1.0, and 1.000 hash the same
    - Preserve list order, since lists are semantically ordered
    """

    @staticmethod
    def _normalize_decimal(value: Decimal) -> int | str:
        normalized = value.normalize()
        if normalized == normalized.to_integral():
            return int(normalized)
        text = format(normalized, "f").rstrip("0").rstrip(".")
        return text if text else "0"

    def _normalize_scalar(self, value: Any) -> Any:
        if isinstance(value, bool) or value is None or isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return self._normalize_decimal(value)
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("Non-finite floats are not supported in deterministic hashing")
            return self._normalize_decimal(Decimal(str(value)))
        if isinstance(value, str):
            return value
        return str(value)

    def _should_exclude(self, key: str, value: Any) -> bool:
        lowered = key.lower()
        if lowered in EXCLUDED_EXACT_KEYS:
            return True
        if "timestamp" in lowered:
            return True
        if "uuid" in lowered:
            return True
        if (lowered == "id" or lowered.endswith("_id")) and isinstance(value, str) and UUID_PATTERN.match(value):
            return True
        if isinstance(value, str) and ISO_TIMESTAMP_PATTERN.match(value) and "time" in lowered:
            return True
        return False

    def normalize_for_hash(self, value: Any) -> Any:
        if isinstance(value, dict):
            normalized: Dict[str, Any] = {}
            for key in sorted(value.keys()):
                child = value[key]
                if self._should_exclude(key, child):
                    continue
                normalized[str(key)] = self.normalize_for_hash(child)
            return normalized
        if isinstance(value, (list, tuple)):
            return [self.normalize_for_hash(item) for item in value]
        return self._normalize_scalar(value)

    def canonical_json(self, value: Any) -> str:
        normalized = self.normalize_for_hash(value)
        return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def hash_payload(self, value: Any) -> str:
        return hashlib.sha256(self.canonical_json(value).encode("utf-8")).hexdigest()


prana_determinism = PranaDeterminismService()
