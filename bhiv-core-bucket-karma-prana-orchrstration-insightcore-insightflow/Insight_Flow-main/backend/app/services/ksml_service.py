"""
KSML Service for handling KSML message operations in InsightFlow.

This service provides high-level operations for KSML message handling,
including routing integration and external system communication.
"""

import logging
from typing import Dict, Any, Optional
from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType, KSMLFormatError
from app.schemas.routing import RouteRequest, RouteResponse, FeedbackRequest
from app.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)


class KSMLService:
    """Service for KSML message operations"""
    
    def __init__(self):
        self.adapter = KSMLAdapter
    
    async def process_routing_request(self, ksml_packet: Dict[str, Any], 
                                    user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a KSML routing request and return KSML response.
        
        Args:
            ksml_packet: KSML-formatted routing request
            user_context: Optional user context
            
        Returns:
            KSML-formatted routing response
            
        Raises:
            KSMLFormatError: If packet format is invalid
            ValueError: If request data is invalid
        """
        try:
            # Validate and unwrap KSML packet
            if not self.adapter.validate_ksml_structure(ksml_packet):
                raise KSMLFormatError("Invalid KSML packet structure")
            
            request_data = self.adapter.unwrap(ksml_packet)
            logger.info(f"Processing KSML routing request: {ksml_packet['meta']['message_id']}")
            
            # Convert to RouteRequest
            route_request = RouteRequest(**request_data)
            
            # Add user context
            context = route_request.context or {}
            if user_context:
                context.update(user_context)
            
            # Route the request
            routing_decision = await decision_engine.route_request(
                input_data=route_request.input_data,
                input_type=route_request.input_type,
                context=context,
                strategy=route_request.strategy
            )
            
            # Wrap response in KSML format
            response_data = RouteResponse(**routing_decision).model_dump()
            ksml_response = self.adapter.wrap(
                data=response_data,
                packet_type=KSMLPacketType.ROUTING_RESPONSE
            )
            
            logger.info(f"Generated KSML routing response: {ksml_response['meta']['message_id']}")
            return ksml_response
            
        except Exception as e:
            logger.error(f"KSML routing processing error: {e}", exc_info=True)
            raise
    
    async def process_feedback_log(self, ksml_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a KSML feedback log and return acknowledgment.
        
        Args:
            ksml_packet: KSML-formatted feedback log
            
        Returns:
            KSML-formatted acknowledgment
            
        Raises:
            KSMLFormatError: If packet format is invalid
        """
        try:
            # Validate and unwrap KSML packet
            if not self.adapter.validate_ksml_structure(ksml_packet):
                raise KSMLFormatError("Invalid KSML packet structure")
            
            feedback_data = self.adapter.unwrap(ksml_packet)
            logger.info(f"Processing KSML feedback: {ksml_packet['meta']['message_id']}")
            
            # Convert to FeedbackRequest
            feedback_request = FeedbackRequest(**feedback_data)
            
            # Process feedback
            await decision_engine.process_feedback(
                routing_log_id=feedback_request.routing_log_id,
                feedback_data=feedback_request.model_dump(exclude={"routing_log_id"})
            )
            
            # Create acknowledgment response
            ack_data = {
                "status": "processed",
                "routing_log_id": feedback_request.routing_log_id,
                "message": "Feedback processed successfully"
            }
            
            ksml_ack = self.adapter.wrap(
                data=ack_data,
                packet_type=KSMLPacketType.FEEDBACK_LOG
            )
            
            logger.info(f"Generated KSML feedback acknowledgment: {ksml_ack['meta']['message_id']}")
            return ksml_ack
            
        except Exception as e:
            logger.error(f"KSML feedback processing error: {e}", exc_info=True)
            raise
    
    def create_metrics_update(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a KSML metrics update packet.
        
        Args:
            metrics_data: Metrics data to send
            
        Returns:
            KSML-formatted metrics update
        """
        try:
            ksml_metrics = self.adapter.wrap(
                data=metrics_data,
                packet_type=KSMLPacketType.METRICS_UPDATE
            )
            
            logger.info(f"Created KSML metrics update: {ksml_metrics['meta']['message_id']}")
            return ksml_metrics
            
        except Exception as e:
            logger.error(f"KSML metrics creation error: {e}", exc_info=True)
            raise
    
    def create_health_check(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a KSML health check packet.
        
        Args:
            health_data: Health status data
            
        Returns:
            KSML-formatted health check
        """
        try:
            ksml_health = self.adapter.wrap(
                data=health_data,
                packet_type=KSMLPacketType.HEALTH_CHECK
            )
            
            logger.info(f"Created KSML health check: {ksml_health['meta']['message_id']}")
            return ksml_health
            
        except Exception as e:
            logger.error(f"KSML health check creation error: {e}", exc_info=True)
            raise


# Global service instance
ksml_service = KSMLService()