# app/services/stp_service.py
"""
STP Service Integration

Integrates STP middleware with InsightFlow routing and feedback systems.
Provides high-level STP operations for routing decisions and feedback packets.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from app.middleware.stp_middleware import get_stp_middleware, STPPacketType, STPPriority
from app.core.config import settings

logger = logging.getLogger(__name__)


class STPService:
    """
    Service layer for STP operations.
    
    Provides high-level methods for wrapping routing decisions and feedback
    packets in STP format while maintaining backward compatibility.
    """
    
    def __init__(self):
        """Initialize STP service with configuration from settings"""
        self.stp_middleware = get_stp_middleware(enable_stp=settings.STP_ENABLED)
        self.default_destination = settings.STP_DESTINATION
        self.default_priority = settings.STP_DEFAULT_PRIORITY
        self.default_require_ack = settings.STP_REQUIRE_ACK
        
        # Acknowledgment tracking
        self.pending_acks: Dict[str, Dict[str, Any]] = {}  # token -> {timestamp, packet_data, retries}
        self.ack_timeout = 30  # seconds
        self.max_retries = 3
        
        # Failure rate thresholds for alerts
        self.failure_rate_warning_threshold = 0.1  # 10%
        self.failure_rate_critical_threshold = 0.25  # 25%
        
        logger.info(
            f"STPService initialized (enabled={settings.STP_ENABLED}, "
            f"destination={self.default_destination}, require_ack={self.default_require_ack})"
        )
    
    async def wrap_routing_decision(
        self,
        routing_decision: Dict[str, Any],
        priority: str = None,
        destination: str = None,
        requires_ack: bool = None
    ) -> Dict[str, Any]:
        """
        Wrap routing decision in STP format.
        
        Args:
            routing_decision: Original routing decision data
            priority: STP priority (normal/high/critical)
            destination: Target system
            requires_ack: Whether acknowledgment is required
        
        Returns:
            STP-wrapped routing decision
        """
        try:
            # Determine priority based on confidence score
            if priority is None:
                confidence = routing_decision.get("confidence_score", 0.5)
                if confidence >= 0.9:
                    priority = STPPriority.HIGH.value
                elif confidence <= 0.3:
                    priority = STPPriority.CRITICAL.value
                else:
                    priority = self.default_priority
            
            requires_ack_final = requires_ack if requires_ack is not None else self.default_require_ack
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=routing_decision,
                packet_type=STPPacketType.ROUTING_DECISION.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=requires_ack_final
            )
            
            # Track packet for acknowledgment if required
            if requires_ack_final:
                await self._track_for_acknowledgment(
                    wrapped_packet.get('stp_token'),
                    wrapped_packet,
                    'routing_decision'
                )
            
            logger.debug(
                f"Wrapped routing decision: {routing_decision.get('request_id')} "
                f"-> {wrapped_packet.get('stp_token')} (ack_required={requires_ack_final})"
            )
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap routing decision: {str(e)}")
            # Track failure metrics
            self.stp_middleware.metrics["wrapping_failures"] += 1
            self.stp_middleware.metrics["fallback_responses"] += 1
            
            # Add failure indicator to response
            fallback_response = routing_decision.copy()
            fallback_response["stp_wrapping_failed"] = True
            fallback_response["stp_error"] = str(e)
            
            logger.warning(
                f"STP wrapping failed for routing decision {routing_decision.get('request_id')}, "
                f"returning unwrapped response with failure indicator"
            )
            
            return fallback_response
    
    async def wrap_feedback_packet(
        self,
        feedback_data: Dict[str, Any],
        priority: str = None,
        destination: str = None,
        requires_ack: bool = None
    ) -> Dict[str, Any]:
        """
        Wrap feedback data in STP format.
        
        Args:
            feedback_data: Original feedback data
            priority: STP priority (normal/high/critical)
            destination: Target system
            requires_ack: Whether acknowledgment is required (default True for feedback)
        
        Returns:
            STP-wrapped feedback packet
        """
        try:
            # Determine priority based on feedback success and metrics
            if priority is None:
                success = feedback_data.get("success", True)
                latency = feedback_data.get("latency_ms", 0)
                
                if not success or latency > 5000:  # Failed or very slow
                    priority = STPPriority.CRITICAL.value
                elif latency > 1000:  # Slow response
                    priority = STPPriority.HIGH.value
                else:
                    priority = self.default_priority
            
            requires_ack_final = requires_ack if requires_ack is not None else True  # Feedback typically requires ACK
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=feedback_data,
                packet_type=STPPacketType.FEEDBACK_PACKET.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=requires_ack_final
            )
            
            # Track packet for acknowledgment if required
            if requires_ack_final:
                await self._track_for_acknowledgment(
                    wrapped_packet.get('stp_token'),
                    wrapped_packet,
                    'feedback_packet'
                )
            
            logger.debug(
                f"Wrapped feedback packet: {feedback_data.get('routing_log_id')} "
                f"-> {wrapped_packet.get('stp_token')} (ack_required={requires_ack_final})"
            )
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap feedback packet: {str(e)}")
            # Track failure metrics
            self.stp_middleware.metrics["wrapping_failures"] += 1
            self.stp_middleware.metrics["fallback_responses"] += 1
            
            # Add failure indicator to response
            fallback_response = feedback_data.copy()
            fallback_response["stp_wrapping_failed"] = True
            fallback_response["stp_error"] = str(e)
            
            logger.warning(
                f"STP wrapping failed for feedback packet {feedback_data.get('routing_log_id')}, "
                f"returning unwrapped response with failure indicator"
            )
            
            return fallback_response
    
    async def wrap_health_check(
        self,
        health_data: Dict[str, Any],
        priority: str = STPPriority.NORMAL.value,
        destination: str = None
    ) -> Dict[str, Any]:
        """
        Wrap health check data in STP format.
        
        Args:
            health_data: Health check data
            priority: STP priority
            destination: Target system
        
        Returns:
            STP-wrapped health check packet
        """
        try:
            # Adjust priority based on health status
            if health_data.get("status") == "unhealthy":
                priority = STPPriority.CRITICAL.value
            elif health_data.get("status") == "degraded":
                priority = STPPriority.HIGH.value
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=health_data,
                packet_type=STPPacketType.HEALTH_CHECK.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=False
            )
            
            logger.debug(f"Wrapped health check -> {wrapped_packet.get('stp_token')}")
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap health check: {str(e)}")
            # Track failure metrics
            self.stp_middleware.metrics["wrapping_failures"] += 1
            self.stp_middleware.metrics["fallback_responses"] += 1
            
            # Add failure indicator to response
            fallback_response = health_data.copy()
            fallback_response["stp_wrapping_failed"] = True
            fallback_response["stp_error"] = str(e)
            
            logger.warning(
                f"STP wrapping failed for health check, "
                f"returning unwrapped response with failure indicator"
            )
            
            return fallback_response
    
    async def unwrap_packet(
        self,
        stp_packet: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Unwrap STP packet to extract payload and metadata.
        
        Args:
            stp_packet: STP-wrapped packet
        
        Returns:
            Tuple of (payload, metadata)
        """
        try:
            payload, metadata = await self.stp_middleware.unwrap_async(stp_packet)
            
            logger.debug(
                f"Unwrapped STP packet: {metadata.get('stp_token')} "
                f"(type={metadata.get('stp_type')})"
            )
            
            return payload, metadata
        
        except Exception as e:
            logger.error(f"Failed to unwrap STP packet: {str(e)}")
            # Track failure metrics
            self.stp_middleware.metrics["unwrapping_failures"] += 1
            self.stp_middleware.metrics["fallback_responses"] += 1
            
            logger.warning(
                f"STP unwrapping failed, returning original packet as payload"
            )
            
            # Return original packet as payload with error metadata
            error_metadata = {
                "stp_unwrapping_failed": True,
                "stp_error": str(e)
            }
            
            return stp_packet, error_metadata
    
    def is_stp_packet(self, data: Dict[str, Any]) -> bool:
        """
        Check if data is an STP packet.
        
        Args:
            data: Data to check
        
        Returns:
            True if STP packet, False otherwise
        """
        return self.stp_middleware.validate_stp_packet(data)
    
    def get_stp_metrics(self) -> Dict[str, Any]:
        """
        Get STP middleware metrics with failure analysis.
        
        Returns:
            STP metrics dictionary with failure rates
        """
        metrics = self.stp_middleware.get_metrics()
        
        # Calculate failure rates
        total_wrap_attempts = metrics["packets_wrapped"] + metrics.get("wrapping_failures", 0)
        total_unwrap_attempts = metrics["packets_unwrapped"] + metrics.get("unwrapping_failures", 0)
        
        metrics["wrap_success_rate"] = (
            metrics["packets_wrapped"] / total_wrap_attempts 
            if total_wrap_attempts > 0 else 1.0
        )
        metrics["unwrap_success_rate"] = (
            metrics["packets_unwrapped"] / total_unwrap_attempts 
            if total_unwrap_attempts > 0 else 1.0
        )
        metrics["overall_failure_rate"] = (
            (metrics.get("wrapping_failures", 0) + metrics.get("unwrapping_failures", 0)) / 
            (total_wrap_attempts + total_unwrap_attempts)
            if (total_wrap_attempts + total_unwrap_attempts) > 0 else 0.0
        )
        
        return metrics
    
    def reset_stp_metrics(self):
        """Reset STP metrics counters"""
        self.stp_middleware.reset_metrics()
    
    def clear_pending_acknowledgments(self) -> int:
        """Clear all pending acknowledgments (for testing/maintenance)"""
        count = len(self.pending_acks)
        self.pending_acks.clear()
        logger.info(f"Cleared {count} pending acknowledgments")
        return count
    
    def check_failure_rates(self) -> Dict[str, Any]:
        """
        Check STP failure rates and generate alerts if thresholds exceeded.
        
        Returns:
            Dictionary with failure rate status and alerts
        """
        metrics = self.get_stp_metrics()
        failure_rate = metrics.get("overall_failure_rate", 0.0)
        
        status = {
            "failure_rate": failure_rate,
            "status": "healthy",
            "alerts": []
        }
        
        if failure_rate >= self.failure_rate_critical_threshold:
            status["status"] = "critical"
            status["alerts"].append({
                "level": "critical",
                "message": f"STP failure rate is critically high: {failure_rate:.1%}",
                "threshold": self.failure_rate_critical_threshold,
                "recommendation": "Check STP middleware configuration and network connectivity"
            })
            logger.critical(
                f"STP failure rate critical: {failure_rate:.1%} "
                f"(threshold: {self.failure_rate_critical_threshold:.1%})"
            )
        elif failure_rate >= self.failure_rate_warning_threshold:
            status["status"] = "warning"
            status["alerts"].append({
                "level": "warning",
                "message": f"STP failure rate is elevated: {failure_rate:.1%}",
                "threshold": self.failure_rate_warning_threshold,
                "recommendation": "Monitor STP performance and investigate if rate continues to increase"
            })
            logger.warning(
                f"STP failure rate elevated: {failure_rate:.1%} "
                f"(threshold: {self.failure_rate_warning_threshold:.1%})"
            )
        
        return status
    
    async def _track_for_acknowledgment(
        self,
        stp_token: str,
        packet_data: Dict[str, Any],
        packet_type: str
    ):
        """Track packet for acknowledgment handling"""
        self.pending_acks[stp_token] = {
            'timestamp': datetime.utcnow(),
            'packet_data': packet_data,
            'packet_type': packet_type,
            'retries': 0
        }
        
        logger.debug(f"Tracking packet {stp_token} for acknowledgment")
    
    async def handle_acknowledgment(self, stp_token: str) -> bool:
        """Handle received acknowledgment for STP packet"""
        if stp_token in self.pending_acks:
            packet_info = self.pending_acks.pop(stp_token)
            logger.info(
                f"Received acknowledgment for {stp_token} "
                f"(type={packet_info['packet_type']}, "
                f"age={datetime.utcnow() - packet_info['timestamp']})"
            )
            return True
        else:
            logger.warning(f"Received acknowledgment for unknown token: {stp_token}")
            return False
    
    async def check_pending_acknowledgments(self):
        """Check for timed-out acknowledgments and handle retries"""
        current_time = datetime.utcnow()
        timeout_threshold = current_time - timedelta(seconds=self.ack_timeout)
        
        timed_out_tokens = []
        
        for token, info in self.pending_acks.items():
            if info['timestamp'] < timeout_threshold:
                timed_out_tokens.append(token)
        
        for token in timed_out_tokens:
            await self._handle_ack_timeout(token)
    
    async def _handle_ack_timeout(self, stp_token: str):
        """Handle acknowledgment timeout for a packet"""
        if stp_token not in self.pending_acks:
            return
        
        packet_info = self.pending_acks[stp_token]
        packet_info['retries'] += 1
        
        if packet_info['retries'] <= self.max_retries:
            # Retry sending the packet
            logger.warning(
                f"Acknowledgment timeout for {stp_token}, retrying "
                f"({packet_info['retries']}/{self.max_retries})"
            )
            
            # Update timestamp for next timeout check
            packet_info['timestamp'] = datetime.utcnow()
            
            # In a real implementation, you would resend the packet here
            # For now, we just log the retry attempt
            
        else:
            # Max retries exceeded, remove from tracking
            self.pending_acks.pop(stp_token)
            logger.error(
                f"Max retries exceeded for {stp_token}, giving up on acknowledgment"
            )
    
    def get_acknowledgment_status(self) -> Dict[str, Any]:
        """Get acknowledgment tracking status"""
        current_time = datetime.utcnow()
        
        pending_count = len(self.pending_acks)
        overdue_count = sum(
            1 for info in self.pending_acks.values()
            if current_time - info['timestamp'] > timedelta(seconds=self.ack_timeout)
        )
        
        return {
            'pending_acknowledgments': pending_count,
            'overdue_acknowledgments': overdue_count,
            'ack_timeout_seconds': self.ack_timeout,
            'max_retries': self.max_retries,
            'pending_tokens': list(self.pending_acks.keys())
        }


# Global STP service instance
_stp_service: Optional[STPService] = None


def get_stp_service() -> STPService:
    """
    Get or create STP service singleton.
    
    Returns:
        STPService instance
    """
    global _stp_service
    
    if _stp_service is None:
        _stp_service = STPService()
    
    return _stp_service