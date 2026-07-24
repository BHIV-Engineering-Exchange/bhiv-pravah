"""
KSML Adapter for wrapping/unwrapping InsightFlow data to Core's KSML format.

KSML (Knowledge Stream Message Language) is Core's standard message format.
This adapter handles serialization and deserialization of KSML packets.
"""

import json
import logging
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class KSMLPacketType(str, Enum):
    """KSML packet types"""
    ROUTING_REQUEST = "routing_request"
    ROUTING_RESPONSE = "routing_response"
    FEEDBACK_LOG = "feedback_log"
    METRICS_UPDATE = "metrics_update"
    HEALTH_CHECK = "health_check"


class KSMLFormatError(Exception):
    """Raised when KSML packet format is invalid"""
    pass


class KSMLAdapter:
    """
    Adapter for KSML message format conversion.
    
    KSML packet structure:
    {
        "meta": {
            "version": "1.0",
            "packet_type": "routing_request",
            "timestamp": "2025-10-29T15:10:00Z",
            "source": "insightflow",
            "destination": "core",
            "message_id": "msg-abc123def456",
            "checksum": "hash123"
        },
        "payload": {
            "data": {...}
        }
    }
    """
    
    KSML_VERSION = "1.0"
    SOURCE = "insightflow"
    DESTINATION = "core"
    
    @staticmethod
    def generate_message_id() -> str:
        """Generate unique message ID"""
        timestamp = datetime.utcnow().isoformat()
        hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:12]
        return f"msg-{hash_val}"
    
    @staticmethod
    def calculate_checksum(data: Dict) -> str:
        """Calculate checksum for packet integrity verification"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    @classmethod
    def wrap(cls, data: Dict[str, Any], packet_type: str) -> Dict[str, Any]:
        """
        Wrap InsightFlow data into KSML format.
        
        Args:
            data: InsightFlow data to wrap
            packet_type: Type of packet (from KSMLPacketType)
        
        Returns:
            KSML-formatted packet
            
        Raises:
            KSMLFormatError: If packet_type is invalid
        """
        # Validate packet type
        try:
            _ = KSMLPacketType(packet_type)
        except ValueError:
            raise KSMLFormatError(f"Invalid packet type: {packet_type}")
        
        # Create KSML packet
        ksml_packet = {
            "meta": {
                "version": cls.KSML_VERSION,
                "packet_type": packet_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": cls.SOURCE,
                "destination": cls.DESTINATION,
                "message_id": cls.generate_message_id(),
            },
            "payload": {
                "data": data
            }
        }
        
        # Add checksum
        ksml_packet["meta"]["checksum"] = cls.calculate_checksum(
            ksml_packet["payload"]
        )
        
        logger.info(
            f"Wrapped KSML packet: {ksml_packet['meta']['message_id']} "
            f"(type: {packet_type})"
        )
        
        return ksml_packet
    
    @classmethod
    def unwrap(cls, ksml_packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unwrap KSML packet back to InsightFlow format.
        
        Args:
            ksml_packet: KSML-formatted packet
        
        Returns:
            Original InsightFlow data
            
        Raises:
            KSMLFormatError: If packet structure is invalid
        """
        # Validate packet structure
        try:
            assert "meta" in ksml_packet, "Missing 'meta' in KSML packet"
            assert "payload" in ksml_packet, "Missing 'payload' in KSML packet"
            
            meta = ksml_packet["meta"]
            assert "version" in meta, "Missing 'version' in meta"
            assert "packet_type" in meta, "Missing 'packet_type' in meta"
            assert "message_id" in meta, "Missing 'message_id' in meta"
            
            payload = ksml_packet["payload"]
            assert "data" in payload, "Missing 'data' in payload"
            
        except AssertionError as e:
            raise KSMLFormatError(f"Invalid KSML packet structure: {str(e)}")
        
        # Verify checksum
        expected_checksum = meta.get("checksum")
        calculated_checksum = cls.calculate_checksum(ksml_packet["payload"])
        
        if expected_checksum != calculated_checksum:
            logger.warning(
                f"Checksum mismatch for {meta['message_id']}: "
                f"expected {expected_checksum}, got {calculated_checksum}"
            )
        
        logger.info(
            f"Unwrapped KSML packet: {meta['message_id']} "
            f"(type: {meta['packet_type']})"
        )
        
        return ksml_packet["payload"]["data"]
    
    @classmethod
    def validate_ksml_structure(cls, ksml_packet: Dict[str, Any]) -> bool:
        """
        Validate KSML packet structure without unwrapping.
        
        Args:
            ksml_packet: KSML packet to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            required_meta_fields = ["version", "packet_type", "timestamp", 
                                   "source", "destination", "message_id", "checksum"]
            
            meta = ksml_packet.get("meta", {})
            for field in required_meta_fields:
                if field not in meta:
                    logger.error(f"Missing required field in meta: {field}")
                    return False
            
            if "payload" not in ksml_packet:
                logger.error("Missing 'payload' in KSML packet")
                return False
            
            if "data" not in ksml_packet["payload"]:
                logger.error("Missing 'data' in payload")
                return False
            
            return True
        except Exception as e:
            logger.error(f"KSML validation error: {str(e)}")
            return False
    
    @classmethod
    def convert_to_ksml_bytes(cls, data: Dict[str, Any], 
                             packet_type: str) -> bytes:
        """
        Wrap data and convert to JSON bytes for transmission.
        
        Args:
            data: Data to wrap
            packet_type: Type of packet
        
        Returns:
            KSML packet as JSON bytes
        """
        ksml_packet = cls.wrap(data, packet_type)
        return json.dumps(ksml_packet).encode('utf-8')
    
    @classmethod
    def convert_from_ksml_bytes(cls, ksml_bytes: bytes) -> Dict[str, Any]:
        """
        Convert JSON bytes to KSML packet and unwrap.
        
        Args:
            ksml_bytes: KSML packet as JSON bytes
        
        Returns:
            Unwrapped InsightFlow data
        """
        ksml_packet = json.loads(ksml_bytes.decode('utf-8'))
        return cls.unwrap(ksml_packet)