# app/telemetry_bus/telemetry_security.py
"""
Telemetry Security Module

Implements packet signing for receiver-side verification.
Prepares InsightFlow for SSPL Phase III secure telemetry.

Features:
- HMAC packet signing using Sovereign JWT secret
- Nonce generation for replay protection
- Timestamp verification (<5 seconds drift)
- Agent fingerprinting
"""

import logging
import hmac
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TelemetrySecurityError(Exception):
    """Raised when telemetry security operations fail"""
    pass


class TelemetrySigner:
    """
    Telemetry packet signing and verification.
    
    Uses HMAC-SHA256 with Sovereign JWT secret for packet integrity.
    """
    
    def __init__(
        self,
        jwt_secret: str,
        max_timestamp_drift_seconds: int = None
    ):
        """
        Initialize telemetry signer.
        
        Args:
            jwt_secret: Sovereign JWT secret for HMAC signing
            max_timestamp_drift_seconds: Maximum allowed timestamp drift (uses config if None)
        """
        self.jwt_secret = jwt_secret.encode('utf-8')
        
        # Use configuration value if not specified
        if max_timestamp_drift_seconds is None:
            from app.core.config import settings
            max_timestamp_drift_seconds = getattr(settings, 'TELEMETRY_MAX_TIMESTAMP_DRIFT', 5)
        
        self.max_drift = max_timestamp_drift_seconds
        
        # Track used nonces (prevent replay attacks)
        self._used_nonces = set()
        self._nonce_cleanup_interval = 300  # Clean every 5 minutes
        self._last_cleanup = time.time()
        
        logger.info(
            f"TelemetrySigner initialized "
            f"(max_drift={max_timestamp_drift_seconds}s)"
        )
    
    def sign_packet(
        self,
        packet: Dict[str, Any],
        agent_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sign telemetry packet with HMAC signature.
        
        Args:
            packet: Original telemetry packet
            agent_fingerprint: Optional agent identifier
        
        Returns:
            Signed packet with security fields
        """
        try:
            # Generate nonce
            nonce = self._generate_nonce()
            
            # Get current timestamp
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Create signature payload
            signature_payload = self._create_signature_payload(
                packet=packet,
                nonce=nonce,
                timestamp=timestamp,
                agent_fingerprint=agent_fingerprint
            )
            
            # Generate HMAC signature
            signature = self._generate_signature(signature_payload)
            
            # Add security fields to packet
            signed_packet = packet.copy()
            signed_packet.update({
                "security": {
                    "nonce": nonce,
                    "timestamp": timestamp,
                    "packet_signature": signature,
                    "agent_fingerprint": agent_fingerprint or "unknown",
                    "version": "v1"
                }
            })
            
            # Track nonce
            self._used_nonces.add(nonce)
            
            # Periodic nonce cleanup
            self._cleanup_nonces_if_needed()
            
            logger.debug(
                f"Signed packet: nonce={nonce[:8]}..., "
                f"signature={signature[:8]}..."
            )
            
            return signed_packet
        
        except Exception as e:
            logger.error(f"Error signing packet: {str(e)}")
            raise TelemetrySecurityError(f"Signing failed: {str(e)}")
    
    def verify_packet(
        self,
        signed_packet: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify signed telemetry packet.
        
        Args:
            signed_packet: Packet with security fields
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check security section exists
            if "security" not in signed_packet:
                return (False, "Missing security section")
            
            security = signed_packet["security"]
            
            # Check required fields
            required = ["nonce", "timestamp", "packet_signature"]
            for field in required:
                if field not in security:
                    return (False, f"Missing field: {field}")
            
            nonce = security["nonce"]
            timestamp_str = security["timestamp"]
            provided_signature = security["packet_signature"]
            agent_fingerprint = security.get("agent_fingerprint", "unknown")
            
            # Check nonce uniqueness (replay protection)
            if nonce in self._used_nonces:
                return (False, f"Nonce already used (replay attack?): {nonce}")
            
            # Verify timestamp drift
            try:
                packet_time = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
                current_time = datetime.utcnow()
                drift = abs((current_time - packet_time).total_seconds())
                
                if drift > self.max_drift:
                    return (
                        False,
                        f"Timestamp drift too large: {drift:.1f}s > {self.max_drift}s"
                    )
            
            except Exception as e:
                return (False, f"Invalid timestamp format: {str(e)}")
            
            # Remove security section for signature verification
            packet_copy = signed_packet.copy()
            del packet_copy["security"]
            
            # Recreate signature payload
            signature_payload = self._create_signature_payload(
                packet=packet_copy,
                nonce=nonce,
                timestamp=timestamp_str,
                agent_fingerprint=agent_fingerprint
            )
            
            # Generate expected signature
            expected_signature = self._generate_signature(signature_payload)
            
            # Compare signatures (constant-time comparison)
            if not hmac.compare_digest(expected_signature, provided_signature):
                return (False, "Signature mismatch")
            
            # Track nonce after successful verification
            self._used_nonces.add(nonce)
            
            logger.debug(f"Packet verified: nonce={nonce[:8]}...")
            
            return (True, None)
        
        except Exception as e:
            logger.error(f"Error verifying packet: {str(e)}")
            return (False, f"Verification error: {str(e)}")
    
    def _generate_nonce(self) -> str:
        """
        Generate cryptographically secure nonce.
        
        Returns:
            32-character hex nonce
        """
        return secrets.token_hex(16)
    
    def _create_signature_payload(
        self,
        packet: Dict[str, Any],
        nonce: str,
        timestamp: str,
        agent_fingerprint: Optional[str]
    ) -> str:
        """
        Create canonical signature payload.
        
        Args:
            packet: Packet data (without security section)
            nonce: Unique nonce
            timestamp: ISO timestamp
            agent_fingerprint: Agent identifier
        
        Returns:
            Canonical string for signing
        """
        import json
        
        # Create deterministic JSON (sorted keys)
        packet_json = json.dumps(packet, sort_keys=True, separators=(',', ':'))
        
        # Concatenate fields
        payload = (
            f"{nonce}|"
            f"{timestamp}|"
            f"{agent_fingerprint or 'unknown'}|"
            f"{packet_json}"
        )
        
        return payload
    
    def _generate_signature(self, payload: str) -> str:
        """
        Generate HMAC-SHA256 signature.
        
        Args:
            payload: String to sign
        
        Returns:
            Hex signature
        """
        signature = hmac.new(
            self.jwt_secret,
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _cleanup_nonces_if_needed(self):
        """Periodic cleanup of old nonces"""
        current_time = time.time()
        
        if current_time - self._last_cleanup > self._nonce_cleanup_interval:
            # Clear nonce set (they're time-limited by timestamp verification)
            self._used_nonces.clear()
            self._last_cleanup = current_time
            
            logger.debug("Cleaned up nonce cache")


# Global telemetry signer instance
_telemetry_signer: Optional[TelemetrySigner] = None


def get_telemetry_signer() -> TelemetrySigner:
    """
    Get or create global telemetry signer instance.
    
    Returns:
        TelemetrySigner instance
    """
    global _telemetry_signer
    
    if _telemetry_signer is None:
        from app.core.config import settings
        
        _telemetry_signer = TelemetrySigner(
            jwt_secret=settings.SOVEREIGN_JWT_SECRET,
            max_timestamp_drift_seconds=settings.TELEMETRY_MAX_TIMESTAMP_DRIFT
        )
    
    return _telemetry_signer