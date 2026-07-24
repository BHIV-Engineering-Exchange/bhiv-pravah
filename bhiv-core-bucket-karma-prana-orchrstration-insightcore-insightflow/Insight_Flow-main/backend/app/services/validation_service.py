"""
Validation Service for InsightFlow.

This service provides high-level validation operations for packets,
requests, and responses across different formats.
"""

import logging
from typing import Dict, Any, Tuple, List, Optional
from app.validators.packet_validator import PacketValidator, ValidationResult

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for packet and data validation"""
    
    def __init__(self):
        self.validator = PacketValidator
    
    def validate_incoming_request(
        self, 
        request_data: Dict[str, Any], 
        format_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate incoming request based on format type.
        
        Args:
            request_data: Request data to validate
            format_type: Format type ('ksml', 'core', 'insightflow')
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            if format_type == "ksml":
                return self.validator.validate_ksml_packet(request_data)
            elif format_type == "core":
                return self.validator.validate_core_routing_request(request_data)
            elif format_type == "insightflow":
                # Basic InsightFlow validation
                return self._validate_insightflow_request(request_data)
            else:
                return False, [f"Unknown format type: {format_type}"]
                
        except Exception as e:
            logger.error(f"Validation error for {format_type}: {e}")
            return False, [f"Validation exception: {str(e)}"]
    
    def validate_outgoing_response(
        self, 
        response_data: Dict[str, Any], 
        format_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate outgoing response based on format type.
        
        Args:
            response_data: Response data to validate
            format_type: Format type ('ksml', 'core', 'insightflow')
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            if format_type == "ksml":
                return self.validator.validate_ksml_packet(response_data)
            elif format_type == "core":
                return self.validator.validate_core_routing_response(response_data)
            elif format_type == "insightflow":
                # Basic InsightFlow validation
                return self._validate_insightflow_response(response_data)
            else:
                return False, [f"Unknown format type: {format_type}"]
                
        except Exception as e:
            logger.error(f"Response validation error for {format_type}: {e}")
            return False, [f"Validation exception: {str(e)}"]
    
    def validate_routing_decision(
        self, 
        decision_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate routing decision data.
        
        Args:
            decision_data: Routing decision to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self.validator.validate_routing_decision(decision_data)
    
    def _validate_insightflow_request(
        self, 
        request: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate InsightFlow format request.
        
        Args:
            request: InsightFlow request to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(request, dict):
            return False, ["Request must be a dictionary"]
        
        # Check for required InsightFlow fields
        required_fields = ["input_data", "input_type"]
        
        for field in required_fields:
            if field not in request:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate field types
        if "input_type" in request:
            if not isinstance(request["input_type"], str):
                errors.append("'input_type' must be a string")
        
        if "strategy" in request:
            if not isinstance(request["strategy"], str):
                errors.append("'strategy' must be a string")
        
        if errors:
            return False, errors
        
        return True, []
    
    def _validate_insightflow_response(
        self, 
        response: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate InsightFlow format response.
        
        Args:
            response: InsightFlow response to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not isinstance(response, dict):
            return False, ["Response must be a dictionary"]
        
        # Check for required InsightFlow response fields
        required_fields = ["agent_id", "confidence_score"]
        
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate field types and ranges
        if "confidence_score" in response:
            score = response["confidence_score"]
            if not isinstance(score, (int, float)):
                errors.append("'confidence_score' must be a number")
            elif not (0.0 <= score <= 1.0):
                errors.append(
                    f"'confidence_score' must be 0.0-1.0, got {score}"
                )
        
        if errors:
            return False, errors
        
        return True, []
    
    def get_validation_summary(
        self, 
        validation_results: List[Tuple[bool, List[str]]]
    ) -> Dict[str, Any]:
        """
        Generate validation summary from multiple validation results.
        
        Args:
            validation_results: List of validation result tuples
            
        Returns:
            Validation summary dictionary
        """
        total_validations = len(validation_results)
        successful_validations = sum(1 for valid, _ in validation_results if valid)
        failed_validations = total_validations - successful_validations
        
        all_errors = []
        for valid, errors in validation_results:
            if not valid:
                all_errors.extend(errors)
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": failed_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0,
            "all_errors": all_errors,
            "overall_valid": failed_validations == 0
        }


# Global validation service instance
validation_service = ValidationService()