"""Stable deterministic hash helpers for pipeline replay verification."""

import hashlib
import json
from typing import Any, Dict, Optional

VOLATILE_KEYS = frozenset(
    {
        "timestamp",
        "trace_id",
        "workflow_id",
        "instruction_id",
        "contract_id",
        "decision_id",
        "created_at",
        "updated_at",
        "derived_at",
        "raised_at",
        "signal_id",
        "alert_id",
    }
)


def strip_volatile(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: strip_volatile(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [strip_volatile(v) for v in value]
    return value


def compute_pipeline_deterministic_hash(
    instruction: Optional[Dict[str, Any]],
    blueprint: Optional[Dict[str, Any]],
    contract: Optional[Dict[str, Any]],
    execution: Optional[Dict[str, Any]],
    signal: Optional[Dict[str, Any]] = None,
) -> str:
    """Hash semantic pipeline content; excludes trace-scoped volatile fields."""
    stable = {
        "prompt": (instruction or {}).get("prompt"),
        "intent": (instruction or {}).get("intent"),
        "module": (instruction or {}).get("module"),
        "product_context": (instruction or {}).get("product_context"),
        "blueprint": strip_volatile(
            {
                "target_product": (blueprint or {}).get("target_product"),
                "intent_type": (blueprint or {}).get("intent_type"),
                "payload": (blueprint or {}).get("payload"),
            }
        ),
        "contract": strip_volatile(
            {
                "execution_plan": (contract or {}).get("execution_plan"),
                "constraints": (contract or {}).get("constraints"),
            }
        ),
        "execution": strip_volatile(
            {
                "status": (execution or {}).get("status"),
                "message": (execution or {}).get("message"),
                "result": (execution or {}).get("result"),
            }
        ),
    }
    if signal is not None:
        stable["signal"] = strip_volatile(
            {
                "metric": signal.get("metric"),
                "value": signal.get("value"),
                "classification": signal.get("classification"),
                "threshold_breached": signal.get("threshold_breached"),
            }
        )
    combined = json.dumps(stable, sort_keys=True)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def hash_from_bucket_artifacts(artifacts: list) -> str:
    by_type = {a["artifact_type"]: a.get("data", {}) for a in artifacts}
    signal = by_type.get("signal")
    if signal is None:
        signal = (by_type.get("alert") or {}).get("signal")
    return compute_pipeline_deterministic_hash(
        by_type.get("instruction"),
        by_type.get("blueprint"),
        by_type.get("contract"),
        by_type.get("execution"),
        signal=signal,
    )
