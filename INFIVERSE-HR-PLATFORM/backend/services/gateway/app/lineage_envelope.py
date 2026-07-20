"""Ownership metadata and lineage envelope for cross-system signals."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LineageEnvelope(BaseModel):
    origin_system: str
    owning_system: str
    schema_version: str = "1.0.0"
    trace_id: str
    correlation_id: str
    trust_classification: str = "derived"
    visibility_scope: str = "tenant"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_request(
        cls,
        *,
        origin_system: str = "gateway",
        owning_system: str = "sampada",
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        visibility_scope: str = "tenant",
        trust_classification: str = "canonical",
        schema_version: str = "1.0.0",
    ) -> "LineageEnvelope":
        cid = correlation_id or str(uuid.uuid4())
        return cls(
            origin_system=origin_system,
            owning_system=owning_system,
            schema_version=schema_version,
            trace_id=trace_id or cid,
            correlation_id=cid,
            trust_classification=trust_classification,
            visibility_scope=visibility_scope,
        )


def attach_lineage(document: Dict[str, Any], envelope: LineageEnvelope) -> Dict[str, Any]:
    doc = dict(document)
    doc["lineage"] = envelope.to_dict()
    doc["updated_at"] = datetime.now(timezone.utc)
    return doc
