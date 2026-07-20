from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ValidationError

from .mongo_store import MongoSetuStore
from .telemetry_layer import TelemetryLayer

REQUIRED_SIGNAL_FIELDS = [
    "trace_id",
    "entity_id", 
    "event_type",
    "signal_type",
    "severity",
    "timestamp",
    "tenant_id"
]

VALID_SEVERITIES = ["low", "medium", "high", "critical"]
VALID_SIGNAL_TYPES = ["execution", "monitoring", "alert", "status"]


class SampadaSignal(BaseModel):
    trace_id: str
    entity_id: str
    event_type: str
    signal_type: str
    severity: str
    timestamp: str
    tenant_id: str
    payload: Optional[Dict[str, Any]] = {}


class SignalIngestionError(Exception):
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


class SignalIngestionModule:
    def __init__(self, store: MongoSetuStore, telemetry_layer: TelemetryLayer):
        self.store = store
        self.telemetry_layer = telemetry_layer

    async def ingest_sampada_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest Sampada signal with validation and logging"""
        
        # Validate signal contract
        try:
            signal = self._validate_signal_payload(signal_data)
        except SignalIngestionError as e:
            await self._log_ingestion_failure(signal_data, e)
            raise e
        
        # Preserve incoming trace metadata
        ingestion_record = {
            "ingestion_id": f"ing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{signal.trace_id[:8]}",
            "trace_id": signal.trace_id,
            "entity_id": signal.entity_id,
            "event_type": signal.event_type,
            "signal_type": signal.signal_type,
            "severity": signal.severity,
            "timestamp": signal.timestamp,
            "tenant_id": signal.tenant_id,
            "payload": signal.payload,
            "ingested_at": datetime.utcnow().isoformat(),
            "status": "ingested"
        }
        
        # Store signal
        await self.store.append_signal_ingestion(ingestion_record)
        
        # Log successful ingestion
        await self._log_ingestion_success(signal)
        
        return {
            "success": True,
            "ingestion_id": ingestion_record["ingestion_id"],
            "trace_id": signal.trace_id,
            "message": "Signal ingested successfully"
        }

    def _validate_signal_payload(self, signal_data: Dict[str, Any]) -> SampadaSignal:
        """Validate incoming signal payload"""
        
        if not isinstance(signal_data, dict):
            raise SignalIngestionError(
                400,
                "invalid_payload_type",
                "Signal payload must be a dictionary",
                {"received_type": type(signal_data).__name__}
            )
        
        # Check required fields
        missing = [field for field in REQUIRED_SIGNAL_FIELDS if field not in signal_data]
        if missing:
            raise SignalIngestionError(
                400,
                "missing_required_fields",
                "Signal payload missing required fields",
                {"missing_fields": missing}
            )
        
        # Validate severity
        severity = signal_data.get("severity")
        if severity not in VALID_SEVERITIES:
            raise SignalIngestionError(
                400,
                "invalid_severity",
                "Invalid severity level",
                {
                    "received_severity": severity,
                    "valid_severities": VALID_SEVERITIES
                }
            )
        
        # Validate signal type
        signal_type = signal_data.get("signal_type")
        if signal_type not in VALID_SIGNAL_TYPES:
            raise SignalIngestionError(
                400,
                "invalid_signal_type",
                "Invalid signal type",
                {
                    "received_signal_type": signal_type,
                    "valid_signal_types": VALID_SIGNAL_TYPES
                }
            )
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(signal_data["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise SignalIngestionError(
                400,
                "invalid_timestamp",
                "Invalid timestamp format, expected ISO format",
                {"received_timestamp": signal_data.get("timestamp")}
            )
        
        # Validate trace_id format
        trace_id = signal_data.get("trace_id", "")
        if not trace_id or len(trace_id) < 8:
            raise SignalIngestionError(
                400,
                "invalid_trace_id",
                "Invalid trace_id format",
                {"received_trace_id": trace_id}
            )
        
        # Create validated signal object
        try:
            return SampadaSignal(**signal_data)
        except ValidationError as e:
            raise SignalIngestionError(
                400,
                "validation_failed",
                "Signal validation failed",
                {"validation_errors": str(e)}
            )

    async def _log_ingestion_success(self, signal: SampadaSignal):
        """Log successful signal ingestion"""
        await self.store.append_trace_log({
            "event": "SIGNAL_INGESTED",
            "trace_id": signal.trace_id,
            "entity_id": signal.entity_id,
            "tenant_id": signal.tenant_id,
            "signal_type": signal.signal_type,
            "severity": signal.severity,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _log_ingestion_failure(self, signal_data: Dict[str, Any], error: SignalIngestionError):
        """Log failed signal ingestion"""
        await self.store.append_trace_log({
            "event": "SIGNAL_INGESTION_FAILED", 
            "trace_id": signal_data.get("trace_id"),
            "tenant_id": signal_data.get("tenant_id"),
            "error_code": error.code,
            "error_message": error.message,
            "error_details": error.details,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def get_ingested_signals(self, trace_id: str, limit: int = 100) -> list:
        """Retrieve ingested signals by trace_id"""
        return await self.store.list_signal_ingestion(trace_id, limit)