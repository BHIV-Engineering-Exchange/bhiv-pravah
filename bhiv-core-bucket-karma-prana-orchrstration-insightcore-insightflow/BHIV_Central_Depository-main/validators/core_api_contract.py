"""
BHIV Core API Contract Validator
Enforces the published service contract between Core and Bucket
Validates input/output channels and data formats
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)

class InputChannel(Enum):
    """Allowed input channels from Core to Bucket"""
    ARTIFACT_WRITE = "artifact_write"
    METADATA_QUERY = "metadata_query"
    AUDIT_APPEND = "audit_append"
    RETENTION_REQUEST = "retention_request"

class OutputChannel(Enum):
    """Allowed output channels from Bucket to Core"""
    ARTIFACT_READ = "artifact_read"
    QUERY_RESULT = "query_result"
    AUDIT_CONFIRMATION = "audit_confirmation"
    RETENTION_STATUS = "retention_status"
    PROVENANCE_DATA = "provenance_data"

class ContractViolationType(Enum):
    """Types of contract violations"""
    INVALID_INPUT_CHANNEL = "invalid_input_channel"
    INVALID_OUTPUT_CHANNEL = "invalid_output_channel"
    SCHEMA_MISMATCH = "schema_mismatch"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_TYPE = "invalid_data_type"
    UNAUTHORIZED_FIELD = "unauthorized_field"

class CoreAPIContract:
    """Validates Core requests against published API contract"""
    
    def __init__(self):
        self.input_schemas = self._define_input_schemas()
        self.output_schemas = self._define_output_schemas()
        logger.info("Core API Contract initialized")
    
    def validate_input(
        self,
        channel: str,
        data: Dict[str, Any],
        requester_id: str
    ) -> Dict[str, Any]:
        """
        Validate input from Core against contract
        
        Args:
            channel: Input channel being used
            data: Input data payload
            requester_id: ID of requesting system
            
        Returns:
            Validation result
        """
        validation_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "requester_id": requester_id,
            "valid": False,
            "violations": [],
            "warnings": []
        }
        
        # Check 1: Validate channel exists
        if not self._is_valid_input_channel(channel):
            validation_result["violations"].append({
                "type": ContractViolationType.INVALID_INPUT_CHANNEL.value,
                "message": f"Invalid input channel: {channel}",
                "severity": "HIGH"
            })
            logger.warning(f"Invalid input channel attempted: {channel}")
            return validation_result
        
        # Check 2: Validate against schema
        schema = self.input_schemas.get(channel)
        if not schema:
            validation_result["violations"].append({
                "type": ContractViolationType.SCHEMA_MISMATCH.value,
                "message": f"No schema defined for channel: {channel}",
                "severity": "HIGH"
            })
            return validation_result
        
        # Check 3: Validate required fields
        schema_validation = self._validate_against_schema(data, schema, "input")
        if not schema_validation["valid"]:
            validation_result["violations"].extend(schema_validation["violations"])
            return validation_result
        
        # All checks passed
        validation_result["valid"] = True
        logger.info(f"Input validated for channel: {channel}")
        
        return validation_result
    
    def validate_output(
        self,
        channel: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate output to Core against contract
        
        Args:
            channel: Output channel being used
            data: Output data payload
            
        Returns:
            Validation result
        """
        validation_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": channel,
            "valid": False,
            "violations": []
        }
        
        # Check 1: Validate channel exists
        if not self._is_valid_output_channel(channel):
            validation_result["violations"].append({
                "type": ContractViolationType.INVALID_OUTPUT_CHANNEL.value,
                "message": f"Invalid output channel: {channel}",
                "severity": "HIGH"
            })
            return validation_result
        
        # Check 2: Validate against schema
        schema = self.output_schemas.get(channel)
        if schema:
            schema_validation = self._validate_against_schema(data, schema, "output")
            if not schema_validation["valid"]:
                validation_result["violations"].extend(schema_validation["violations"])
                return validation_result
        
        # All checks passed
        validation_result["valid"] = True
        
        return validation_result
    
    def _is_valid_input_channel(self, channel: str) -> bool:
        """Check if input channel is allowed"""
        return channel in [c.value for c in InputChannel]
    
    def _is_valid_output_channel(self, channel: str) -> bool:
        """Check if output channel is allowed"""
        return channel in [c.value for c in OutputChannel]
    
    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        direction: str
    ) -> Dict[str, Any]:
        """Validate data against schema"""
        violations = []
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                violations.append({
                    "type": ContractViolationType.MISSING_REQUIRED_FIELD.value,
                    "message": f"Missing required field: {field}",
                    "severity": "HIGH",
                    "field": field
                })
        
        # Check field types
        properties = schema.get("properties", {})
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    violations.append({
                        "type": ContractViolationType.INVALID_DATA_TYPE.value,
                        "message": f"Field {field} has invalid type. Expected {expected_type}",
                        "severity": "MEDIUM",
                        "field": field
                    })
            else:
                # Field not in schema - might be unauthorized
                if schema.get("additionalProperties") is False:
                    violations.append({
                        "type": ContractViolationType.UNAUTHORIZED_FIELD.value,
                        "message": f"Unauthorized field: {field}",
                        "severity": "LOW",
                        "field": field
                    })
        
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if not expected_python_type:
            return True  # Unknown type, allow
        
        return isinstance(value, expected_python_type)
    
    def _define_input_schemas(self) -> Dict[str, Dict]:
        """Define schemas for input channels"""
        return {
            InputChannel.ARTIFACT_WRITE.value: {
                "required": ["artifact_type", "product_id", "data"],
                "properties": {
                    "artifact_type": {"type": "string"},
                    "product_id": {"type": "string"},
                    "data": {"type": "object"},
                    "metadata": {"type": "object"}
                },
                "additionalProperties": True
            },
            InputChannel.METADATA_QUERY.value: {
                "required": ["query_type", "product_id"],
                "properties": {
                    "query_type": {"type": "string"},
                    "product_id": {"type": "string"},
                    "filters": {"type": "object"},
                    "limit": {"type": "integer"}
                },
                "additionalProperties": False
            },
            InputChannel.AUDIT_APPEND.value: {
                "required": ["operation_type", "artifact_id", "requester_id"],
                "properties": {
                    "operation_type": {"type": "string"},
                    "artifact_id": {"type": "string"},
                    "requester_id": {"type": "string"},
                    "data_before": {"type": "object"},
                    "data_after": {"type": "object"}
                },
                "additionalProperties": True
            },
            InputChannel.RETENTION_REQUEST.value: {
                "required": ["artifact_id", "action"],
                "properties": {
                    "artifact_id": {"type": "string"},
                    "action": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "additionalProperties": False
            }
        }
    
    def _define_output_schemas(self) -> Dict[str, Dict]:
        """Define schemas for output channels"""
        return {
            OutputChannel.ARTIFACT_READ.value: {
                "required": ["artifact_id", "data"],
                "properties": {
                    "artifact_id": {"type": "string"},
                    "artifact_type": {"type": "string"},
                    "data": {"type": "object"},
                    "metadata": {"type": "object"},
                    "created_at": {"type": "string"}
                }
            },
            OutputChannel.QUERY_RESULT.value: {
                "required": ["results", "count"],
                "properties": {
                    "results": {"type": "array"},
                    "count": {"type": "integer"},
                    "has_more": {"type": "boolean"}
                }
            },
            OutputChannel.AUDIT_CONFIRMATION.value: {
                "required": ["audit_id", "status"],
                "properties": {
                    "audit_id": {"type": "string"},
                    "status": {"type": "string"},
                    "timestamp": {"type": "string"}
                }
            },
            OutputChannel.RETENTION_STATUS.value: {
                "required": ["artifact_id", "status"],
                "properties": {
                    "artifact_id": {"type": "string"},
                    "status": {"type": "string"},
                    "retention_date": {"type": "string"}
                }
            },
            OutputChannel.PROVENANCE_DATA.value: {
                "required": ["artifact_id", "provenance"],
                "properties": {
                    "artifact_id": {"type": "string"},
                    "provenance": {"type": "object"},
                    "verified": {"type": "boolean"}
                }
            }
        }
    
    def get_contract_documentation(self) -> Dict[str, Any]:
        """Get complete contract documentation"""
        return {
            "version": "1.0",
            "input_channels": {
                channel.value: {
                    "description": self._get_channel_description(channel.value, "input"),
                    "schema": self.input_schemas.get(channel.value)
                }
                for channel in InputChannel
            },
            "output_channels": {
                channel.value: {
                    "description": self._get_channel_description(channel.value, "output"),
                    "schema": self.output_schemas.get(channel.value)
                }
                for channel in OutputChannel
            }
        }
    
    def _get_channel_description(self, channel: str, direction: str) -> str:
        """Get human-readable description of channel"""
        descriptions = {
            "artifact_write": "Write new artifact to Bucket",
            "metadata_query": "Query artifact metadata",
            "audit_append": "Append entry to audit trail",
            "retention_request": "Request artifact retention/deletion",
            "artifact_read": "Read artifact from Bucket",
            "query_result": "Return query results",
            "audit_confirmation": "Confirm audit entry created",
            "retention_status": "Return retention status",
            "provenance_data": "Return provenance information"
        }
        return descriptions.get(channel, "No description available")

# Global contract validator instance
core_api_contract = CoreAPIContract()
