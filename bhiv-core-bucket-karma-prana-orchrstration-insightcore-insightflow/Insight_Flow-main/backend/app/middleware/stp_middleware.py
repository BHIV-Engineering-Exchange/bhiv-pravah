# app/middleware/stp_middleware.py
"""
STP-Layer (Structured Token Protocol) Middleware

Wraps routing decisions and feedback packets using STP format.
Provides JSON ↔ STP ↔ JSON translation for interoperability.
Lightweight and non-blocking design.

STP Packet Format:
{
    "stp_version": "1.0",
    "stp_token": "stp-abc123def456",
    "stp_timestamp": "2025-11-08T09:00:00.000Z",
    "stp_type": "routing_decision" | "feedback_packet" | "health_check",
    "stp_metadata": {
        "source": "insightflow",
        "destination": "sovereign_core",
        "priority": "normal" | "high" | "critical",
        "requires_ack": true | false
    },
    "payload": {
        // Original JSON data
    },
    "stp_checksum": "hash_value"
}
"""

import json
import logging
import hashlib
import time
import secrets
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class STPPacketType(str, Enum):
    """STP packet types"""
    ROUTING_DECISION = "routing_decision"
    FEEDBACK_PACKET = "feedback_packet"
    HEALTH_CHECK = "health_check"
    METRICS_UPDATE = "metrics_update"
    KARMA_SYNC = "karma_sync"


class STPPriority(str, Enum):
    """STP priority levels"""
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class STPLayerError(Exception):
    """Raised when STP layer operations fail"""
    pass


class STPMiddleware:
    """
    STP-Layer middleware for wrapping and unwrapping packets.
    
    This middleware ensures all routing decisions and feedback packets
    conform to the Structured Token Protocol (STP) format.
    
    Features:
    - Lightweight wrapping/unwrapping
    - Non-blocking async operations
    - Checksum verification
    - Token generation
    - Backward compatible with non-STP systems
    """
    
    STP_VERSION = "1.0"
    SOURCE = "insightflow"
    
    def __init__(self, enable_stp: bool = True, strict_checksum: bool = True):
        """
        Initialize STP middleware.
        
        Args:
            enable_stp: Enable/disable STP wrapping (for gradual rollout)
            strict_checksum: Reject packets with invalid checksums (True) or warn only (False)
        """
        self.enable_stp = enable_stp
        self.strict_checksum = strict_checksum
        self.metrics = {
            "packets_wrapped": 0,
            "packets_unwrapped": 0,
            "errors": 0,
            "checksum_failures": 0,
        }
        
        logger.info(
            f"STPMiddleware initialized (enabled={enable_stp}, strict_checksum={strict_checksum})"
        )
    
    @staticmethod
    def generate_stp_token() -> str:
        """
        Generate cryptographically secure unique STP token.
        
        Format: stp-{secure_random_hex}
        Returns: Unique STP token string with 128 bits of entropy
        """
        # Generate 16 bytes (128 bits) of cryptographically secure random data
        random_bytes = secrets.token_bytes(16)
        # Convert to hex for readability
        random_hex = random_bytes.hex()
        return f"stp-{random_hex}"
    
    @staticmethod
    def calculate_checksum(payload: Dict[str, Any]) -> str:
        """
        Calculate checksum for payload integrity verification.
        
        Args:
            payload: Payload data to checksum
        
        Returns:
            Hex checksum string
        """
        json_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def wrap(
        self,
        payload: Dict[str, Any],
        packet_type: str,
        destination: str = "sovereign_core",
        priority: str = STPPriority.NORMAL.value,
        requires_ack: bool = False
    ) -> Dict[str, Any]:
        """
        Wrap JSON payload into STP format.
        
        Args:
            payload: Original JSON data to wrap
            packet_type: Type of packet (from STPPacketType)
            destination: Target system
            priority: Packet priority (normal/high/critical)
            requires_ack: Whether acknowledgment is required
        
        Returns:
            STP-wrapped packet
        
        Raises:
            STPLayerError: If wrapping fails
        """
        if not self.enable_stp:
            # Pass-through mode: return original payload
            logger.debug("STP disabled, returning unwrapped payload")
            return payload
        
        try:
            # Validate packet type
            _ = STPPacketType(packet_type)
            
            # Create STP packet
            stp_packet = {
                "stp_version": self.STP_VERSION,
                "stp_token": self.generate_stp_token(),
                "stp_timestamp": datetime.utcnow().isoformat() + "Z",
                "stp_type": packet_type,
                "stp_metadata": {
                    "source": self.SOURCE,
                    "destination": destination,
                    "priority": priority,
                    "requires_ack": requires_ack,
                },
                "payload": payload,
            }
            
            # Add checksum
            stp_packet["stp_checksum"] = self.calculate_checksum(payload)
            
            self.metrics["packets_wrapped"] += 1
            
            logger.debug(
                f"Wrapped STP packet: {stp_packet['stp_token']} "
                f"(type={packet_type}, priority={priority})"
            )
            
            return stp_packet
        
        except ValueError as e:
            self.metrics["errors"] += 1
            raise STPLayerError(f"Invalid packet type: {packet_type}") from e
        
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error wrapping STP packet: {str(e)}")
            raise STPLayerError(f"Failed to wrap packet: {str(e)}") from e
    
    def unwrap(self, stp_packet: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Unwrap STP packet back to original JSON payload.
        
        Args:
            stp_packet: STP-wrapped packet
        
        Returns:
            Tuple of (payload, metadata)
            - payload: Original JSON data
            - metadata: STP metadata (token, timestamp, type, etc.)
        
        Raises:
            STPLayerError: If unwrapping fails or checksum invalid
        """
        if not self.enable_stp:
            # Pass-through mode
            return stp_packet, {}
        
        try:
            # Validate STP structure
            required_fields = [
                "stp_version", "stp_token", "stp_timestamp",
                "stp_type", "stp_metadata", "payload", "stp_checksum"
            ]
            
            for field in required_fields:
                if field not in stp_packet:
                    raise STPLayerError(f"Missing required field: {field}")
            
            # Verify checksum
            payload = stp_packet["payload"]
            expected_checksum = stp_packet["stp_checksum"]
            calculated_checksum = self.calculate_checksum(payload)
            
            if expected_checksum != calculated_checksum:
                self.metrics["checksum_failures"] += 1
                error_msg = (
                    f"Checksum mismatch for {stp_packet['stp_token']}: "
                    f"expected {expected_checksum}, got {calculated_checksum}"
                )
                
                if self.strict_checksum:
                    logger.error(f"REJECTED: {error_msg}")
                    raise STPLayerError(f"Packet rejected due to checksum failure: {error_msg}")
                else:
                    logger.warning(f"WARNING: {error_msg} (continuing with corrupted data)")
            
            # Extract metadata
            metadata = {
                "stp_token": stp_packet["stp_token"],
                "stp_timestamp": stp_packet["stp_timestamp"],
                "stp_type": stp_packet["stp_type"],
                "stp_version": stp_packet["stp_version"],
                **stp_packet["stp_metadata"]
            }
            
            self.metrics["packets_unwrapped"] += 1
            
            logger.debug(
                f"Unwrapped STP packet: {stp_packet['stp_token']}"
            )
            
            return payload, metadata
        
        except KeyError as e:
            self.metrics["errors"] += 1
            raise STPLayerError(f"Invalid STP packet structure: {str(e)}") from e
        
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error unwrapping STP packet: {str(e)}")
            raise STPLayerError(f"Failed to unwrap packet: {str(e)}") from e
    
    def validate_stp_packet(self, packet: Dict[str, Any]) -> bool:
        """
        Validate STP packet structure without unwrapping.
        
        Args:
            packet: Packet to validate
        
        Returns:
            True if valid STP packet, False otherwise
        """
        if not self.enable_stp:
            return True  # Pass-through
        
        try:
            required_fields = [
                "stp_version", "stp_token", "stp_timestamp",
                "stp_type", "stp_metadata", "payload"
            ]
            
            for field in required_fields:
                if field not in packet:
                    logger.debug(f"Validation failed: missing {field}")
                    return False
            
            # Validate packet type
            try:
                _ = STPPacketType(packet["stp_type"])
            except ValueError:
                logger.debug(f"Invalid packet type: {packet['stp_type']}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating STP packet: {str(e)}")
            return False
    
    async def wrap_async(
        self,
        payload: Dict[str, Any],
        packet_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async version of wrap() for non-blocking operations.
        
        Args:
            payload: Original JSON data
            packet_type: Type of packet
            **kwargs: Additional wrap() arguments
        
        Returns:
            STP-wrapped packet
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.wrap,
            payload,
            packet_type,
            kwargs.get("destination", "sovereign_core"),
            kwargs.get("priority", STPPriority.NORMAL.value),
            kwargs.get("requires_ack", False)
        )
    
    async def unwrap_async(
        self,
        stp_packet: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Async version of unwrap() for non-blocking operations.
        
        Args:
            stp_packet: STP-wrapped packet
        
        Returns:
            Tuple of (payload, metadata)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.unwrap,
            stp_packet
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get STP middleware metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            **self.metrics,
            "enabled": self.enable_stp,
        }
    
    def reset_metrics(self):
        """Reset all metrics counters"""
        self.metrics = {
            "packets_wrapped": 0,
            "packets_unwrapped": 0,
            "errors": 0,
            "checksum_failures": 0,
            "wrapping_failures": 0,
            "unwrapping_failures": 0,
            "fallback_responses": 0,
        }
        logger.info("STP metrics reset")


# Global STP middleware instance
_stp_middleware: Optional[STPMiddleware] = None


def get_stp_middleware(enable_stp: bool = True) -> STPMiddleware:
    """
    Get or create STP middleware singleton.
    
    Args:
        enable_stp: Enable/disable STP wrapping
    
    Returns:
        STPMiddleware instance
    """
    global _stp_middleware
    
    if _stp_middleware is None:
        _stp_middleware = STPMiddleware(enable_stp=enable_stp)
    
    return _stp_middleware