from datetime import datetime
from typing import Any, Dict, Optional

from .mongo_store import MongoSetuStore
from .signal_ingestion import SignalIngestionError
from .contract_validation import ContractValidationError


class FailureHandler:
    """Handles various validation failures with proper logging"""
    
    def __init__(self, store: MongoSetuStore):
        self.store = store

    async def handle_invalid_trace_id(self, trace_id: Optional[str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle invalid trace_id failure"""
        
        failure_record = {
            "failure_type": "invalid_trace_id",
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "reason": "Invalid or malformed trace_id",
            "details": {
                "received_trace_id": trace_id,
                "validation_rules": "trace_id must be non-empty string with minimum 8 characters"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 400
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        # Return rejection response
        return {
            "success": False,
            "error": "invalid_trace_id",
            "message": "Request rejected due to invalid trace_id",
            "details": failure_record["details"],
            "status_code": 400
        }

    async def handle_missing_required_field(
        self, 
        missing_fields: list, 
        trace_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle missing required field failure"""
        
        failure_record = {
            "failure_type": "missing_required_field",
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "reason": "Contract validation failure - missing required fields",
            "details": {
                "missing_fields": missing_fields,
                "required_fields": ["trace_id", "entity_id", "event_type", "timestamp", "tenant_id"]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 400
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        # Return rejection response
        return {
            "success": False,
            "error": "contract_validation_failure",
            "message": "Request rejected due to missing required fields",
            "details": failure_record["details"],
            "status_code": 400
        }

    async def handle_unauthorized_tenant(
        self,
        tenant_id: str,
        trace_id: Optional[str] = None,
        reason: str = "Unauthorized tenant access"
    ) -> Dict[str, Any]:
        """Handle unauthorized tenant failure"""
        
        failure_record = {
            "failure_type": "unauthorized_tenant", 
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "reason": reason,
            "details": {
                "attempted_tenant_id": tenant_id,
                "rejection_reason": "Tenant not authorized for this operation"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 403
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        # Return 403 rejection
        return {
            "success": False,
            "error": "unauthorized_tenant",
            "message": "403 rejection - tenant not authorized",
            "details": failure_record["details"], 
            "status_code": 403
        }

    async def handle_signal_ingestion_error(self, error: SignalIngestionError, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle signal ingestion errors"""
        
        failure_record = {
            "failure_type": "signal_ingestion_error",
            "trace_id": payload.get("trace_id"),
            "tenant_id": payload.get("tenant_id"),
            "reason": error.message,
            "details": {
                "error_code": error.code,
                "error_details": error.details,
                "original_payload": payload
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": error.status_code
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        return {
            "success": False,
            "error": error.code,
            "message": error.message,
            "details": error.details,
            "status_code": error.status_code
        }

    async def handle_contract_validation_error(self, error: ContractValidationError, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle contract validation errors"""
        
        failure_record = {
            "failure_type": "contract_validation_error",
            "trace_id": context.get("trace_id"),
            "tenant_id": context.get("tenant_id"), 
            "reason": error.message,
            "details": {
                "error_code": error.code,
                "error_details": error.details,
                "validation_context": context
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 400
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        return {
            "success": False,
            "error": error.code,
            "message": error.message,
            "details": error.details,
            "status_code": 400
        }

    async def handle_trace_continuity_error(
        self,
        error_code: str,
        error_message: str,
        execution: Dict[str, Any],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle trace continuity errors"""
        
        failure_record = {
            "failure_type": "trace_continuity_error",
            "trace_id": execution.get("trace_id"),
            "tenant_id": execution.get("tenant_id"),
            "execution_id": execution.get("execution_id"),
            "reason": error_message,
            "details": {
                "error_code": error_code,
                "error_details": details or {},
                "execution_context": execution
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": 409
        }
        
        # Log failure
        await self._log_failure(failure_record)
        
        return {
            "success": False,
            "error": error_code,
            "message": error_message,
            "details": details or {},
            "status_code": 409
        }

    async def _log_failure(self, failure_record: Dict[str, Any]):
        """Log failure to trace logs"""
        await self.store.append_trace_log({
            "event": "VALIDATION_FAILURE",
            "failure_type": failure_record["failure_type"],
            "trace_id": failure_record.get("trace_id"),
            "tenant_id": failure_record.get("tenant_id"),
            "execution_id": failure_record.get("execution_id"),
            "reason": failure_record["reason"],
            "details": failure_record["details"],
            "status_code": failure_record["status_code"],
            "timestamp": failure_record["timestamp"]
        })

    async def get_failure_logs(self, trace_id: str, limit: int = 100) -> list:
        """Get failure logs for a trace"""
        logs = await self.store.list_trace_logs(trace_id, limit=limit * 2)  # Get more to filter
        
        failure_logs = [
            log for log in logs 
            if log.get("event") == "VALIDATION_FAILURE"
        ]
        
        return failure_logs[:limit]

    async def test_failure_scenarios(self) -> Dict[str, Any]:
        """Test failure scenarios as required"""
        
        test_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "scenarios": []
        }
        
        # Test 1: Invalid trace_id
        test_1_result = await self.handle_invalid_trace_id("abc")
        test_results["scenarios"].append({
            "test": "invalid_trace_id",
            "expected": "Reject request",
            "result": test_1_result,
            "passed": test_1_result["status_code"] == 400
        })
        
        # Test 2: Missing required field
        test_2_result = await self.handle_missing_required_field(["entity_id", "event_type"])
        test_results["scenarios"].append({
            "test": "missing_required_field", 
            "expected": "Contract validation failure",
            "result": test_2_result,
            "passed": test_2_result["status_code"] == 400
        })
        
        # Test 3: Unauthorized tenant
        test_3_result = await self.handle_unauthorized_tenant("unauthorized_tenant_123")
        test_results["scenarios"].append({
            "test": "unauthorized_tenant",
            "expected": "403 rejection",
            "result": test_3_result,
            "passed": test_3_result["status_code"] == 403
        })
        
        return test_results