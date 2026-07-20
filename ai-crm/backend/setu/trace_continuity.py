from datetime import datetime
from typing import Any, Dict, List, Optional

from .mongo_store import MongoSetuStore
from .utils import compute_lineage_hash

REQUIRED_FIELDS = [
    "execution_id",
    "trace_id",
    "source_system",
    "actor",
    "intent_type",
    "target_system",
    "parameters",
    "priority",
    "timestamp",
    "schema_version",
    "tenant_id"
]


class TraceContinuityError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

    def payload(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


def extract_execution(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, dict):
        if "execution" in payload:
            return payload.get("execution")
        if "execution_contract" in payload:
            return payload.get("execution_contract")
    return payload if isinstance(payload, dict) else None


class TraceContinuityValidator:
    def __init__(self, store: MongoSetuStore, schema_version: str = "1.0"):
        self.store = store
        self.schema_version = schema_version

    async def validate(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(execution, dict):
            raise TraceContinuityError(
                400,
                "execution_missing",
                "Execution contract is required",
                {"received_type": type(execution).__name__}
            )

        missing = [field for field in REQUIRED_FIELDS if execution.get(field) is None]
        if missing:
            raise TraceContinuityError(
                400,
                "execution_missing_fields",
                "Execution contract missing required fields",
                {"missing_fields": missing}
            )

        if execution.get("schema_version") != self.schema_version:
            raise TraceContinuityError(
                409,
                "schema_version_mismatch",
                "Unsupported schema version",
                {
                    "expected": self.schema_version,
                    "received": execution.get("schema_version")
                }
            )

        execution_id = execution.get("execution_id")
        trace_id = execution.get("trace_id")
        tenant_id = execution.get("tenant_id")
        trace_lineage = execution.get("trace_lineage") or {}

        existing = await self.store.get_trace_record(execution_id)
        if existing and existing.get("trace_id") != trace_id:
            raise TraceContinuityError(
                409,
                "trace_id_regenerated",
                "Trace ID regeneration detected",
                {
                    "execution_id": execution_id,
                    "expected_trace_id": existing.get("trace_id"),
                    "received_trace_id": trace_id
                }
            )

        existing_trace = await self.store.get_trace_by_trace_id(trace_id)
        if existing_trace and existing_trace.get("tenant_id") != tenant_id:
            raise TraceContinuityError(
                409,
                "tenant_trace_collision",
                "Trace ID reused across tenants",
                {
                    "trace_id": trace_id,
                    "expected_tenant_id": existing_trace.get("tenant_id"),
                    "received_tenant_id": tenant_id
                }
            )

        if trace_lineage.get("root_trace_id") and trace_lineage.get("root_trace_id") != trace_id:
            raise TraceContinuityError(
                409,
                "trace_root_mismatch",
                "Root trace ID mismatch",
                {
                    "execution_id": execution_id,
                    "root_trace_id": trace_lineage.get("root_trace_id"),
                    "trace_id": trace_id
                }
            )

        if trace_lineage.get("parent_execution_id"):
            parent = await self.store.get_trace_record(trace_lineage.get("parent_execution_id"))
            if parent:
                if parent.get("trace_id") != trace_id:
                    raise TraceContinuityError(
                        409,
                        "trace_lineage_mutated",
                        "Parent trace mismatch in lineage",
                        {
                            "execution_id": execution_id,
                            "parent_execution_id": trace_lineage.get("parent_execution_id"),
                            "parent_trace_id": parent.get("trace_id"),
                            "trace_id": trace_id
                        }
                    )
                if parent.get("tenant_id") != tenant_id:
                    raise TraceContinuityError(
                        409,
                        "tenant_lineage_violation",
                        "Tenant lineage mismatch",
                        {
                            "execution_id": execution_id,
                            "parent_execution_id": trace_lineage.get("parent_execution_id"),
                            "expected_tenant_id": parent.get("tenant_id"),
                            "received_tenant_id": tenant_id
                        }
                    )

        computed_hash = compute_lineage_hash(execution)
        if trace_lineage.get("lineage_hash") and trace_lineage.get("lineage_hash") != computed_hash:
            raise TraceContinuityError(
                409,
                "lineage_hash_mismatch",
                "Lineage hash mismatch",
                {
                    "execution_id": execution_id,
                    "expected_hash": computed_hash,
                    "received_hash": trace_lineage.get("lineage_hash")
                }
            )

        if existing and existing.get("lineage_hash") and existing.get("lineage_hash") != computed_hash:
            raise TraceContinuityError(
                409,
                "lineage_hash_mutated",
                "Stored lineage hash mismatch",
                {
                    "execution_id": execution_id,
                    "expected_hash": existing.get("lineage_hash"),
                    "received_hash": computed_hash
                }
            )

        record = {
            "execution_id": execution_id,
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "root_trace_id": trace_lineage.get("root_trace_id") or trace_id,
            "parent_execution_id": trace_lineage.get("parent_execution_id"),
            "lineage_hash": trace_lineage.get("lineage_hash") or computed_hash,
            "seen_at": datetime.utcnow().isoformat(),
            "source_system": execution.get("source_system"),
            "intent_type": execution.get("intent_type")
        }

        await self.store.upsert_trace_record(record)
        await self.store.append_trace_log({
            "event": "trace_continuity_ok",
            "execution_id": execution_id,
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "lineage_hash": record["lineage_hash"],
            "timestamp": datetime.utcnow().isoformat()
        })

        return record
