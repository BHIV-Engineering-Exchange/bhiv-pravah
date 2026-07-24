"""
STP Bridge Module

Configurable bridge to forward karmic feedback signals to InsightFlow.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import requests
from fastapi import HTTPException
import hashlib
import hmac
import time
import ssl
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import threading

# Setup logging
logger = logging.getLogger(__name__)

class STPBridge:
    """STP (Signal Transmission Protocol) Bridge for forwarding signals to InsightFlow"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the STP bridge"""
        self.config = config or {}
        self.insightflow_endpoint = self.config.get(
            "insightflow_endpoint", 
            "http://localhost:8001/api/v1/insightflow/receive"
        )
        self.insightflow_health_endpoint = self.config.get(
            "insightflow_health_endpoint", 
            "http://localhost:8001/api/v1/insightflow/health"
        )
        self.retry_attempts = self.config.get("retry_attempts", 3)
        self.timeout = self.config.get("timeout", 10)
        self.enabled = self.config.get("enabled", True)
        
        # Security configuration
        self.use_mtls = self.config.get("use_mtls", False)
        self.cert_file = self.config.get("cert_file")
        self.key_file = self.config.get("key_file")
        self.ca_bundle = self.config.get("ca_bundle")
        
        # Signing configuration
        self.signing_method = self.config.get("signing_method", "hmac-sha256")
        self.secret_key = self.config.get("secret_key", "default-secret-key")
        
        # Replay protection
        self.nonce_store = set()
        self.nonce_lock = threading.Lock()
        self.nonce_cleanup_interval = self.config.get("nonce_cleanup_interval", 3600)  # 1 hour
        self.last_nonce_cleanup = time.time()
        
        # ACK/NACK configuration
        self.await_ack = self.config.get("await_ack", True)
        self.ack_timeout = self.config.get("ack_timeout", 30)
        
        # TTL (Time To Live) configuration
        self.ttl_seconds = self.config.get("ttl_seconds", 300)  # 5 minutes default
        
        # Status tracking
        self.status = "active"
        
        # Session for connection reuse
        self.session = requests.Session()
        if self.use_mtls and self.cert_file and self.key_file:
            self.session.cert = (self.cert_file, self.key_file)
            if self.ca_bundle:
                self.session.verify = self.ca_bundle
    
    def forward_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Forward karmic feedback signal to InsightFlow
        
        Args:
            signal: Karmic feedback signal to forward
            
        Returns:
            Dict with forwarding result
        """
        if not self.enabled:
            return {
                "status": "skipped",
                "message": "STP bridge is disabled",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        signal_id = signal.get("signal_id", str(uuid.uuid4()))
        
        try:
            # Clean up old nonces periodically
            self._cleanup_nonces()
            
            # Prepare the payload for InsightFlow
            payload = {
                "transmission_id": str(uuid.uuid4()),
                "source": "karmachain_feedback_engine",
                "signal": signal,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nonce": str(uuid.uuid4()),  # For replay protection
                "ttl": self.ttl_seconds  # Time to live
            }
            
            # Add signature
            payload["signature"] = self._sign_payload(payload)
            
            # Send to InsightFlow with retry logic
            response = self._send_with_retry(payload)
            
            # Handle ACK/NACK if required
            if self.await_ack:
                ack_result = self._wait_for_ack(response.get("transmission_id"))
                if ack_result.get("status") == "nack":
                    raise Exception(f"NACK received: {ack_result.get('reason', 'Unknown reason')}")
            
            # Log successful transmission
            logger.info(f"Signal {signal_id} forwarded to InsightFlow successfully")
            
            return {
                "status": "success",
                "signal_id": signal_id,
                "transmission_id": payload["transmission_id"],
                "response": response,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error forwarding signal {signal_id} to InsightFlow: {str(e)}"
            logger.error(error_msg)
            self.status = "degraded"
            
            return {
                "status": "error",
                "signal_id": signal_id,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _send_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send payload with retry logic
        
        Args:
            payload: Payload to send
            
        Returns:
            Dict with response details
        """
        last_exception = Exception("Unknown error")
        
        for attempt in range(self.retry_attempts):
            try:
                # Validate nonce to prevent replay attacks
                if "nonce" in payload:
                    is_valid_nonce = self._validate_nonce(payload["nonce"])
                    if not is_valid_nonce:
                        raise Exception("Duplicate nonce detected - possible replay attack")
                
                response = self.session.post(
                    self.insightflow_endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                
                response_data = response.json() if response.content else {}
                
                if response.status_code in [200, 201]:
                    return {
                        "status_code": response.status_code,
                        "response": response_data,
                        "attempt": attempt + 1
                    }
                else:
                    # Only remove the nonce from store if it's a permanent error
                    # For temporary errors, we want to keep the nonce to prevent replays
                    if response.status_code not in [429, 500, 502, 503, 504]:  # Don't remove for temporary errors
                        if "nonce" in payload:
                            with self.nonce_lock:
                                self.nonce_store.discard(payload["nonce"])
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed with status {response.status_code}"
                    )
                    last_exception = HTTPException(
                        status_code=response.status_code,
                        detail=f"InsightFlow returned status {response.status_code}"
                    )
                    
            except Exception as e:
                # For connection errors, keep the nonce in store to prevent replays
                # Only remove for definitive errors
                is_connection_error = "Max retries exceeded" in str(e) or "Connection refused" in str(e)
                if not is_connection_error:
                    if "nonce" in payload:
                        with self.nonce_lock:
                            self.nonce_store.discard(payload["nonce"])
                        
                logger.warning(f"Attempt {attempt + 1} failed with exception: {str(e)}")
                last_exception = e
        
        # If we get here, all attempts failed
        self.status = "degraded"
        raise last_exception
    
    def batch_forward_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Forward multiple signals in batch
        
        Args:
            signals: List of signals to forward
            
        Returns:
            List of forwarding results
        """
        results = []
        
        for signal in signals:
            result = self.forward_signal(signal)
            results.append(result)
            
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the STP bridge connection
        
        Returns:
            Dict with health status
        """
        try:
            # Send a simple health check ping to the correct endpoint
            health_payload = {
                "transmission_id": str(uuid.uuid4()),
                "source": "karmachain_feedback_engine",
                "type": "health_check",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nonce": str(uuid.uuid4()),
                "ttl": self.ttl_seconds
            }
            
            # Add signature
            health_payload["signature"] = self._sign_payload(health_payload)
            
            response = self.session.post(
                self.insightflow_health_endpoint,  # Use the correct health endpoint
                json=health_payload,
                timeout=self.timeout
            )
            
            # Update status based on health check result
            if response.status_code in [200, 201]:
                self.status = "active"
                status = "healthy"
            else:
                self.status = "degraded"
                status = "unhealthy"
            
            return {
                "status": status,
                "endpoint": self.insightflow_health_endpoint,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.status = "offline"
            return {
                "status": "unhealthy",
                "endpoint": self.insightflow_health_endpoint,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _sign_payload(self, payload: Dict[str, Any]) -> str:
        """
        Sign payload using configured method
        
        Args:
            payload: Payload to sign
            
        Returns:
            Signature string
        """
        payload_str = json.dumps(payload, sort_keys=True)
        
        if self.signing_method == "hmac-sha256":
            return hmac.new(
                self.secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
        elif self.signing_method == "ed25519":
            # For Ed25519, we would need a private key
            # This is a placeholder implementation
            return f"ed25519_signature_placeholder_{hashlib.sha256(payload_str.encode()).hexdigest()}"
        else:
            raise ValueError(f"Unsupported signing method: {self.signing_method}")
    
    def _cleanup_nonces(self):
        """
        Clean up old nonces periodically to prevent memory leaks
        """
        # Simple implementation - in a production system, you might want
        # to use a more sophisticated approach with timestamps
        if time.time() - self.last_nonce_cleanup > self.nonce_cleanup_interval:
            with self.nonce_lock:
                # Keep only the most recent 10000 nonces
                if len(self.nonce_store) > 10000:
                    # Convert to list, sort, and keep the last 10000
                    nonce_list = list(self.nonce_store)
                    self.nonce_store = set(nonce_list[-10000:])
            self.last_nonce_cleanup = time.time()
    
    def _validate_nonce(self, nonce: str) -> bool:
        """
        Validate that a nonce hasn't been used before (replay attack protection)
        
        Args:
            nonce: The nonce to validate
            
        Returns:
            bool: True if nonce is valid (not used before), False if it's a replay
        """
        with self.nonce_lock:
            if nonce in self.nonce_store:
                # Nonce already exists - this is a replay attack
                return False
            # Nonce is new, add it to the store
            self.nonce_store.add(nonce)
            return True
    
    def validate_ttl(self, packet: Dict[str, Any]) -> bool:
        """
        Validate that a packet hasn't expired based on TTL
            
        Args:
            packet: The packet to validate
                
        Returns:
            bool: True if packet is still valid, False if expired
        """
        import re
        timestamp_val = packet.get('timestamp', '')
            
        # Handle case where timestamp might be a float (epoch) or other type
        try:
            if isinstance(timestamp_val, float) or (isinstance(timestamp_val, str) and timestamp_val.replace('.', '').isdigit()):
                # Handle float epoch timestamp
                timestamp_val = float(timestamp_val)
                packet_timestamp = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
            elif isinstance(timestamp_val, str):
                # Handle ISO format with or without timezone
                timestamp_str = timestamp_val
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str[:-1] + '+00:00'
                elif '+' not in timestamp_str and not timestamp_str.endswith(('Z', '+00:00')):
                    timestamp_str += '+00:00'
                    
                # Parse the timestamp
                # Remove timezone info for parsing and add it separately
                clean_timestamp = re.sub(r'[+-]\\d{2}:\\d{2}$', '', timestamp_str)
                naive_dt = datetime.fromisoformat(clean_timestamp)
                packet_timestamp = naive_dt.replace(tzinfo=timezone.utc)
            else:
                # If parsing fails, use current time as fallback
                packet_timestamp = datetime.now(timezone.utc)
        except (ValueError, TypeError, OSError):
            # If parsing fails, use current time as fallback
            packet_timestamp = datetime.now(timezone.utc)
            
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - packet_timestamp).total_seconds()
        ttl = packet.get('ttl', self.ttl_seconds)
        return elapsed_time <= ttl
    
    def verify_signature(self, packet: Dict[str, Any]) -> bool:
        """
        Verify the signature of a packet
        
        Args:
            packet: The packet to verify
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        original_signature = packet.get('signature', '')
        if not original_signature:
            return False
        
        # Temporarily remove signature from packet for verification
        temp_packet = packet.copy()
        if 'signature' in temp_packet:
            del temp_packet['signature']
        # Recreate signature and compare
        recreated_signature = self._sign_payload(temp_packet)
        return original_signature == recreated_signature
    
    def _wait_for_ack(self, transmission_id: str) -> Dict[str, Any]:
        """
        Wait for ACK/NACK for a transmission with proper timeout and retry logic
        
        Args:
            transmission_id: ID of transmission to wait for
            
        Returns:
            Dict with ACK/NACK result
        """
        import time
        import threading
        
        # Create a unique endpoint for this transmission ACK
        ack_endpoint = f"{self.insightflow_endpoint}/ack/{transmission_id}"
        
        start_time = time.time()
        while time.time() - start_time < self.ack_timeout:
            try:
                # Poll for ACK/NACK response
                response = self.session.get(
                    ack_endpoint,
                    timeout=min(5, self.ack_timeout)  # Short timeout for polling
                )
                
                if response.status_code == 200:
                    ack_response = response.json()
                    return ack_response
                elif response.status_code == 404:
                    # ACK not ready yet, continue waiting
                    time.sleep(0.5)  # Wait before next poll
                    continue
                else:
                    logger.warning(f"Unexpected response status when waiting for ACK: {response.status_code}")
                    time.sleep(0.5)
                    continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error polling for ACK: {str(e)}")
                time.sleep(0.5)
                continue
        
        # If we get here, timeout occurred
        logger.warning(f"Timeout waiting for ACK/NACK for transmission {transmission_id}")
        return {
            "status": "timeout",
            "transmission_id": transmission_id,
            "reason": f"ACK/NACK timeout after {self.ack_timeout} seconds"
        }
        
    def create_packet(self, signal: 'KarmaSignal', source: str, destination: str) -> Dict[str, Any]:
        """
        Create a packet containing the karma signal
        
        Args:
            signal: The karma signal to wrap
            source: Source of the packet
            destination: Destination of the packet
            
        Returns:
            Dict representing the packet
        """
        # Create packet without signature initially
        packet = {
            'source': source,
            'destination': destination,
            'payload': signal.to_dict(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'nonce': str(uuid.uuid4()),
            'ttl': signal.ttl
        }
        # Add signature
        packet['signature'] = self._sign_payload(packet)
        return packet
    
    def send_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a packet containing a karma signal
        
        Args:
            packet: The packet to send
            
        Returns:
            Dict with sending result
        """
        # Validate TTL
        if not self.validate_ttl(packet):
            return {
                'status': 'REJECTED',
                'reason': 'TTL_EXPIRED',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Validate nonce to prevent replay attacks
        if not self._validate_nonce(packet['nonce']):
            return {
                'status': 'REJECTED',
                'reason': 'REPLAY_ATTACK_DETECTED',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Send to destination
        try:
            response = self.session.post(
                self.insightflow_endpoint,
                json=packet,
                timeout=self.timeout
            )
            
            return {
                'status': 'SUCCESS' if response.status_code in [200, 201] else 'ERROR',
                'response_status': response.status_code,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        

    def register_ack_handler(self, transmission_id: str, callback: callable):
        """
        Register a callback to handle ACK/NACK responses asynchronously
        
        Args:
            transmission_id: ID of transmission to monitor
            callback: Function to call with ACK/NACK result
        """
        def ack_monitor():
            result = self._wait_for_ack(transmission_id)
            callback(result)
        
        # Run ACK monitoring in background thread
        thread = threading.Thread(target=ack_monitor, daemon=True)
        thread.start()

# Global instance
stp_bridge = STPBridge()

# Convenience functions
def forward_karmic_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a karmic signal to InsightFlow"""
    return stp_bridge.forward_signal(signal)

def batch_forward_karmic_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Forward multiple karmic signals to InsightFlow"""
    return stp_bridge.batch_forward_signals(signals)

def check_stp_bridge_health() -> Dict[str, Any]:
    """Check the health of the STP bridge"""
    return stp_bridge.health_check()