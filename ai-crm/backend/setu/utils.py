import hashlib
import json
from typing import Any, Dict


def stable_stringify(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ",".join(stable_stringify(item) for item in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda item: item[0])
        return "{" + ",".join(
            f"{json.dumps(key, ensure_ascii=True)}:{stable_stringify(val)}"
            for key, val in items
        ) + "}"
    return json.dumps(value, ensure_ascii=True)


def compute_lineage_hash(execution: Dict[str, Any]) -> str:
    lineage = execution.get("trace_lineage") or {}
    fingerprint = {
        "execution_id": execution.get("execution_id"),
        "trace_id": execution.get("trace_id"),
        "tenant_id": execution.get("tenant_id"),
        "root_trace_id": lineage.get("root_trace_id") or execution.get("trace_id"),
        "parent_trace_id": lineage.get("parent_trace_id"),
        "parent_execution_id": lineage.get("parent_execution_id")
    }
    return hashlib.sha256(stable_stringify(fingerprint).encode("utf-8")).hexdigest()


def compute_determinism_hash(event: Dict[str, Any]) -> str:
    base = dict(event)
    base.pop("determinism_hash", None)
    return hashlib.sha256(stable_stringify(base).encode("utf-8")).hexdigest()
