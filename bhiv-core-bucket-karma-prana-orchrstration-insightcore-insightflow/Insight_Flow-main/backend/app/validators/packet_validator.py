# app/validators/packet_validator.py
"""
Packet Validator: Validate KSML and Core format packets.

Ensures all incoming/outgoing data conforms to standards:
- KSML packet structure
- Core API schema
- Required fields
- Data types
- Value ranges
"""

import logging
from typing import Dict, Any, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result statuses"""
    VALID = "valid"
    INVALID_STRUCTURE = "invalid_structure"
    INVALID_FIELDS = "invalid_fields"
    INVALID_TYPES = "invalid_types"
    INVALID_RANGES = "invalid_ranges"
    MISSING_REQUIRED = "missing_required"


class PacketValidator:
    """Validates KSML and Core format packets"""
    
    # KSML Required Fields
    KSML_META_REQUIRED = [
        "version",
        "packet_type",
        "timestamp",
        "source",
        "destination",
        "message_id",
        "checksum"
    ]
    
    # Core Routing Request Required Fields
    CORE_ROUTING_REQUEST_REQUIRED = [
        "task_type",
        "min_confidence"
    ]
    
    # Core Routing Response Required Fields
    CORE_ROUTING_RESPONSE_REQUIRED = [
        "selected_agent_id",
        "agent_category",
        "confidence_level",
        "timestamp"
    ]
    
    @staticmethod
    def validate_ksml_packet(packet: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate KSML packet structure.
        
        Args:
            packet: KSML packet to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check top-level structure
        if not isinstance(packet, dict):
            errors.append("Packet must be a dictionary")
            return False, errors
        
        if "meta" not in packet:
            errors.append("Missing 'meta' in packet")
        if "payload" not in packet:
            errors.append("Missing 'payload' in packet")
        
        if errors:
            return False, errors
        
        # Validate meta section
        meta = packet.get("meta", {})
        if not isinstance(meta, dict):
            errors.append("'meta' must be a dictionary")
        
        for required_field in PacketValidator.KSML_META_REQUIRED:
            if required_field not in meta:
                errors.append(
                    f"Missing required meta field: '{required_field}'"
                )
        
        # Validate meta field types
        if "version" in meta and not isinstance(meta["version"], str):
            errors.append("'version' must be a string")
        
        if "packet_type" in meta and not isinstance(meta["packet_type"], str):
            errors.append("'packet_type' must be a string")
        
        if "message_id" in meta and not isinstance(meta["message_id"], str):
            errors.append("'message_id' must be a string")
        
        # Validate payload section
        payload = packet.get("payload", {})
        if not isinstance(payload, dict):
            errors.append("'payload' must be a dictionary")
        
        if "data" not in payload:
            errors.append("Missing 'data' in payload")
        
        if errors:
            logger.warning(f"KSML packet validation errors: {errors}")
            return False, errors
        
        logger.debug("KSML packet validation passed")
        return True, []
    
    @staticmethod
    def validate_core_routing_request(
        request: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Core routing request format.
        
        Args:
            request: Core routing request to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(request, dict):
            errors.append("Request must be a dictionary")
            return False, errors
        
        # Check required fields
        for field in PacketValidator.CORE_ROUTING_REQUEST_REQUIRED:
            if field not in request:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate field types
        if "task_type" in request:
            if not isinstance(request["task_type"], str):
                errors.append("'task_type' must be a string")
        
        if "min_confidence" in request:
            if not isinstance(request["min_confidence"], (int, float)):
                errors.append("'min_confidence' must be a number")
        
        # Validate value ranges
        if "min_confidence" in request:
            confidence = request["min_confidence"]
            if not (0.0 <= confidence <= 1.0):
                errors.append(
                    f"'min_confidence' must be between 0.0 and 1.0, "
                    f"got {confidence}"
                )
        
        if errors:
            logger.warning(
                f"Core routing request validation errors: {errors}"
            )
            return False, errors
        
        logger.debug("Core routing request validation passed")
        return True, []
    
    @staticmethod
    def validate_core_routing_response(
        response: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Core routing response format.
        
        Args:
            response: Core routing response to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(response, dict):
            errors.append("Response must be a dictionary")
            return False, errors
        
        # Check required fields
        for field in PacketValidator.CORE_ROUTING_RESPONSE_REQUIRED:
            if field not in response:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate field types
        if "selected_agent_id" in response:
            if not isinstance(response["selected_agent_id"], str):
                errors.append("'selected_agent_id' must be a string")
        
        if "agent_category" in response:
            if not isinstance(response["agent_category"], str):
                errors.append("'agent_category' must be a string")
        
        if "confidence_level" in response:
            if not isinstance(response["confidence_level"], (int, float)):
                errors.append("'confidence_level' must be a number")
        
        # Validate value ranges
        if "confidence_level" in response:
            confidence = response["confidence_level"]
            if not (0.0 <= confidence <= 1.0):
                errors.append(
                    f"'confidence_level' must be between 0.0 and 1.0, "
                    f"got {confidence}"
                )
        
        if errors:
            logger.warning(
                f"Core routing response validation errors: {errors}"
            )
            return False, errors
        
        logger.debug("Core routing response validation passed")
        return True, []
    
    @staticmethod
    def validate_routing_decision(
        decision: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate routing decision packet.
        
        Args:
            decision: Routing decision to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(decision, dict):
            errors.append("Decision must be a dictionary")
            return False, errors
        
        # Required decision fields
        required_decision_fields = [
            "agent_selected",
            "confidence_score"
        ]
        
        for field in required_decision_fields:
            if field not in decision:
                errors.append(f"Missing required decision field: '{field}'")
        
        # Validate types
        if "confidence_score" in decision:
            score = decision["confidence_score"]
            if not isinstance(score, (int, float)):
                errors.append("'confidence_score' must be a number")
            elif not (0.0 <= score <= 1.0):
                errors.append(
                    f"'confidence_score' must be 0.0-1.0, got {score}"
                )
        
        if errors:
            logger.warning(
                f"Routing decision validation errors: {errors}"
            )
            return False, errors
        
        logger.debug("Routing decision validation passed")
        return True, []