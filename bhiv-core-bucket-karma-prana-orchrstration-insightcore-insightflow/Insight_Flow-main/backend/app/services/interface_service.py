"""
Interface Service for handling format conversions in InsightFlow.

This service provides high-level operations for converting between
InsightFlow and Core API formats, integrating with existing routing.
"""

import logging
from typing import Dict, Any, Optional
from app.adapters.interface_converter import InterfaceConverter
from app.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)


class InterfaceService:
    """Service for interface format conversions and routing"""
    
    def __init__(self):
        self.converter = InterfaceConverter
    
    async def process_core_routing_request(
        self, 
        core_request: Dict[str, Any],
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a Core format routing request.
        
        Args:
            core_request: Core API format request
            user_context: Optional user context
            
        Returns:
            Core format response
        """
        try:
            # Convert Core request to InsightFlow format
            insight_request = self.converter.core_to_insight_flow({
                "selected_agent_id": "temp",  # Will be filled by routing
                "agent_category": core_request.get("task_type"),
                "confidence_level": core_request.get("min_confidence", 0.5),
                "correlation_id": core_request.get("correlation_id")
            })
            
            # Create InsightFlow routing request
            routing_request = {
                "input_data": core_request.get("task_context", {}),
                "input_type": core_request.get("task_type"),
                "strategy": "q_learning",
                "context": core_request.get("task_context", {})
            }
            
            # Add user context
            if user_context:
                routing_request["context"].update(user_context)
            
            # Route using existing decision engine
            routing_result = await decision_engine.route_request(
                input_data=routing_request["input_data"],
                input_type=routing_request["input_type"],
                context=routing_request["context"],
                strategy=routing_request["strategy"]
            )
            
            # Convert result to Core format
            core_response = self.converter.insight_flow_to_core({
                "agent_type": routing_result.get("agent_name", "unknown"),
                "confidence_threshold": routing_result.get("confidence_score", 0.5),
                "request_id": core_request.get("correlation_id"),
                "context": routing_result
            })
            
            # Format as proper Core response
            formatted_response = {
                "selected_agent_id": routing_result.get("agent_id"),
                "agent_category": routing_result.get("agent_name", "unknown"),
                "confidence_level": routing_result.get("confidence_score", 0.5),
                "correlation_id": core_request.get("correlation_id"),
                "score_breakdown": {
                    "routing_confidence": routing_result.get("confidence_score", 0.5),
                    "agent_performance": routing_result.get("agent_performance", 0.5)
                },
                "timestamp": routing_result.get("timestamp", "")
            }
            
            logger.info(f"Processed Core routing request: {core_request.get('correlation_id')}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing Core routing request: {e}", exc_info=True)
            raise
    
    def convert_legacy_request(
        self, 
        legacy_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert legacy InsightFlow request to Core format.
        
        Args:
            legacy_request: Legacy InsightFlow format
            
        Returns:
            Core format request
        """
        try:
            return self.converter.insight_flow_to_core(legacy_request)
        except Exception as e:
            logger.error(f"Error converting legacy request: {e}")
            raise
    
    def convert_core_response(
        self, 
        core_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert Core response to InsightFlow format.
        
        Args:
            core_response: Core format response
            
        Returns:
            InsightFlow format response
        """
        try:
            return self.converter.core_to_insight_flow(core_response)
        except Exception as e:
            logger.error(f"Error converting Core response: {e}")
            raise
    
    def validate_request_format(
        self, 
        request_data: Dict[str, Any], 
        expected_format: str
    ) -> bool:
        """
        Validate request format.
        
        Args:
            request_data: Request to validate
            expected_format: 'insightflow' or 'core'
            
        Returns:
            True if valid
        """
        try:
            return self.converter.validate_field_mapping(request_data, expected_format)
        except ValueError as e:
            logger.warning(f"Request validation failed: {e}")
            return False


# Global interface service instance
interface_service = InterfaceService()