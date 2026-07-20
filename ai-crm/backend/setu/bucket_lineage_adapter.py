from datetime import datetime
from typing import Any, Dict, Optional

from .mongo_store import MongoSetuStore
from .utils import compute_determinism_hash


class BucketLineageAdapter:
    def __init__(self, store: MongoSetuStore):
        self.store = store

    async def emit_execution_event(self, execution: Dict[str, Any], event_type: str,
                                   payload: Optional[Dict[str, Any]] = None,
                                   overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not execution.get("execution_id") or not execution.get("trace_id") or not execution.get("tenant_id"):
            raise ValueError("Execution identifiers are required for lineage emission")

        overrides = overrides or {}
        timestamp = overrides.get("timestamp") or execution.get("timestamp") or datetime.utcnow().isoformat()
        sequence = overrides.get("sequence") or await self.store.next_lineage_sequence(execution.get("trace_id"))

        event = {
            "lineage_event_id": "",
            "execution_id": execution.get("execution_id"),
            "trace_id": execution.get("trace_id"),
            "tenant_id": execution.get("tenant_id"),
            "event_type": event_type,
            "timestamp": timestamp,
            "sequence": sequence,
            "payload": payload or {}
        }

        event["determinism_hash"] = compute_determinism_hash(event)
        event["lineage_event_id"] = "lin_" + event["determinism_hash"][:16]

        await self.store.append_lineage_event(event)
        return event

    async def list_events(self, trace_id: str, limit: int = 200):
        return await self.store.list_lineage_events(trace_id, limit)

    async def verify_execution_history(self, execution_id: str, trace_id: str) -> Dict[str, Any]:
        """Verify execution event, signal, and history exist in Bucket"""
        
        verification_result = {
            "execution_id": execution_id,
            "trace_id": trace_id,
            "verified": True,
            "verification_details": {}
        }
        
        # Check execution event exists
        execution_events = await self.store.list_lineage_events(trace_id, limit=1000)
        execution_event_found = any(
            event.get("execution_id") == execution_id 
            for event in execution_events
        )
        
        verification_result["verification_details"]["execution_event_exists"] = execution_event_found
        
        # Check signal exists
        signal_records = await self.store.list_signal_ingestion(trace_id, limit=1000)
        signal_found = any(
            record.get("entity_id") == execution_id or record.get("trace_id") == trace_id
            for record in signal_records
        )
        
        verification_result["verification_details"]["signal_exists"] = signal_found
        
        # Check history exists (trace logs)
        history_logs = await self.store.list_trace_logs(trace_id, limit=1000)
        history_found = len(history_logs) > 0
        
        verification_result["verification_details"]["history_exists"] = history_found
        
        # Overall verification
        verification_result["verified"] = (
            execution_event_found and 
            signal_found and 
            history_found
        )
        
        # Log verification result
        await self.store.append_trace_log({
            "event": "BUCKET_HISTORY_VERIFICATION",
            "execution_id": execution_id,
            "trace_id": trace_id,
            "verified": verification_result["verified"],
            "verification_details": verification_result["verification_details"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return verification_result

    async def retrieve_lineage_verification(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve lineage verification without duplication of local truth"""
        
        # Get existing lineage events from Bucket
        lineage_events = await self.list_events(trace_id)
        
        # Get trace logs from Bucket  
        trace_logs = await self.store.list_trace_logs(trace_id)
        
        # Get signal records from Bucket
        signal_records = await self.store.list_signal_ingestion(trace_id)
        
        return {
            "trace_id": trace_id,
            "lineage_events": lineage_events,
            "trace_logs": trace_logs, 
            "signal_records": signal_records,
            "verification_status": "retrieved_from_bucket",
            "local_duplication": False,
            "retrieved_at": datetime.utcnow().isoformat()
        }
