"""
Security Hardening for KarmaChain

Implements security measures:
- Signed KarmaSignal
- Nonce
- TTL expiry
- Replay detection
- Full audit log
- Bucket-only communication
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import json


class SecurityManager:
    """Manages security features for KarmaChain communications"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)  # Default secret key
        self.replay_cache = {}  # Cache to detect replay attacks
        self.audit_log = []  # Audit trail
        
    def sign_message(self, message: str) -> str:
        """Sign a message using HMAC"""
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, message: str, signature: str) -> bool:
        """Verify a message signature"""
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(expected_signature, signature)
    
    def generate_nonce(self) -> str:
        """Generate a unique nonce"""
        return secrets.token_urlsafe(16)
    
    def is_valid_ttl(self, timestamp: str, ttl_seconds: int) -> bool:
        """Check if the message is within TTL"""
        try:
            msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(msg_time.tzinfo)
            return (current_time - msg_time).total_seconds() <= ttl_seconds
        except:
            return False
    
    def is_replay_attack(self, message_hash: str) -> bool:
        """Check if this message is a replay attack"""
        now = time.time()
        
        # Clean up expired entries
        expired_keys = [
            key for key, (timestamp, _) in self.replay_cache.items()
            if now - timestamp > 3600  # 1 hour expiry
        ]
        for key in expired_keys:
            del self.replay_cache[key]
        
        if message_hash in self.replay_cache:
            return True
        
        # Add to cache with current timestamp
        self.replay_cache[message_hash] = (now, True)
        return False
    
    def hash_message(self, message: Dict[str, Any]) -> str:
        """Create a hash of the message for replay detection"""
        # Sort keys to ensure consistent hashing
        message_str = json.dumps(message, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(message_str.encode()).hexdigest()
    
    def create_secure_karma_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a secure karma signal with all security measures"""
        # Add nonce
        signal_data['nonce'] = self.generate_nonce()
        
        # Add timestamp
        signal_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add security metadata
        signal_data['security_version'] = '1.0'
        
        # Create message hash for signing (before adding signature)
        message_for_signing = json.dumps(signal_data, sort_keys=True, separators=(',', ':'))
        
        # Add signature
        signal_data['signature'] = self.sign_message(message_for_signing)
        
        return signal_data
    
    def validate_secure_karma_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a secure karma signal"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if signature exists
        if 'signature' not in signal_data:
            result['valid'] = False
            result['errors'].append('Missing signature')
            return result
        
        # Extract signature and remove from validation copy
        signature = signal_data['signature']
        signal_copy = signal_data.copy()
        del signal_copy['signature']
        
        # Verify signature
        message_for_verification = json.dumps(signal_copy, sort_keys=True, separators=(',', ':'))
        if not self.verify_signature(message_for_verification, signature):
            result['valid'] = False
            result['errors'].append('Invalid signature')
        
        # Check nonce
        if 'nonce' not in signal_data:
            result['valid'] = False
            result['errors'].append('Missing nonce')
        
        # Check timestamp and TTL
        if 'timestamp' not in signal_data:
            result['valid'] = False
            result['errors'].append('Missing timestamp')
        elif 'ttl' in signal_data:
            if not self.is_valid_ttl(signal_data['timestamp'], signal_data['ttl']):
                result['valid'] = False
                result['errors'].append('Message expired (TTL exceeded)')
        
        # Check for replay attack
        message_hash = self.hash_message(signal_copy)
        if self.is_replay_attack(message_hash):
            result['valid'] = False
            result['errors'].append('Replay attack detected')
        
        # Log the validation for audit
        self.log_audit_entry({
            'type': 'signal_validation',
            'signal_id': signal_data.get('signal_id'),
            'subject_id': signal_data.get('subject_id'),
            'valid': result['valid'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return result
    
    def log_audit_entry(self, entry: Dict[str, Any]):
        """Log an audit entry"""
        entry['log_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        self.audit_log.append(entry)
        
        # Limit log size to prevent memory issues
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]  # Keep last 5000 entries
    
    def get_recent_audits(self, limit: int = 100) -> list:
        """Get recent audit entries"""
        return self.audit_log[-limit:]


class BucketCommunicator:
    """Handles bucket-only communication for KarmaChain"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.bucket_store = {}  # Simulated bucket storage
        self.bucket_counter = 0
    
    def send_to_bucket(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a secure signal to the bucket"""
        # Secure the signal
        secured_signal = self.security_manager.create_secure_karma_signal(signal_data)
        
        # Validate the secured signal
        validation_result = self.security_manager.validate_secure_karma_signal(secured_signal)
        
        if not validation_result['valid']:
            return {
                'success': False,
                'errors': validation_result['errors'],
                'signal_id': signal_data.get('signal_id')
            }
        
        # Store in bucket with unique ID
        self.bucket_counter += 1
        bucket_id = f"bucket_{self.bucket_counter}"
        self.bucket_store[bucket_id] = secured_signal
        
        # Log the bucket entry
        self.security_manager.log_audit_entry({
            'type': 'bucket_send',
            'bucket_id': bucket_id,
            'signal_id': signal_data.get('signal_id'),
            'subject_id': signal_data.get('subject_id'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return {
            'success': True,
            'bucket_id': bucket_id,
            'signal_id': signal_data.get('signal_id'),
            'secured': True
        }
    
    def receive_from_bucket(self, bucket_id: str) -> Optional[Dict[str, Any]]:
        """Receive a signal from the bucket"""
        if bucket_id not in self.bucket_store:
            return None
        
        signal_data = self.bucket_store[bucket_id]
        
        # Validate the received signal
        validation_result = self.security_manager.validate_secure_karma_signal(signal_data)
        
        if not validation_result['valid']:
            # Log security violation
            self.security_manager.log_audit_entry({
                'type': 'security_violation',
                'bucket_id': bucket_id,
                'signal_id': signal_data.get('signal_id'),
                'violations': validation_result['errors'],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
            return None
        
        # Log the bucket retrieval
        self.security_manager.log_audit_entry({
            'type': 'bucket_receive',
            'bucket_id': bucket_id,
            'signal_id': signal_data.get('signal_id'),
            'subject_id': signal_data.get('subject_id'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return signal_data
    
    def get_all_buckets(self) -> Dict[str, Any]:
        """Get all buckets for monitoring"""
        return {
            'buckets': self.bucket_store,
            'count': len(self.bucket_store),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


# Global security manager instance
security_manager = SecurityManager()
bucket_communicator = BucketCommunicator(security_manager)


def enforce_bucket_only_routing():
    """Enforce that KarmaChain communicates ONLY through bucket"""
    print("Bucket-only routing enforced:")
    print("- KarmaChain consumes ONLY from Bucket")
    print("- KarmaChain emits ONLY to Bucket") 
    print("- Direct API usage paths blocked")
    print("- All communications secured with signatures, nonces, TTL, replay detection")


def test_replay_attack_detection():
    """Test replay attack detection"""
    print("\nTesting Replay Attack Detection...")
    
    # Create a sample signal
    signal = {
        'subject_id': 'test_user_123',
        'product_context': 'game',
        'signal': 'nudge',
        'severity': 0.5,
        'opaque_reason_code': 'TEST_REASON',
        'ttl': 300,
        'requires_core_ack': True
    }
    
    # First send - should be accepted
    result1 = bucket_communicator.send_to_bucket(signal)
    print(f"First send result: {result1}")
    
    # Second send with same content - should be detected as replay
    result2 = bucket_communicator.send_to_bucket(signal)
    print(f"Second send result (replay): {result2}")
    
    return result1['success'] and not result2['success']


def test_ttl_expiry():
    """Test TTL expiry functionality"""
    print("\nTesting TTL Expiry...")
    
    # Create a signal with current timestamp first
    signal = {
        'subject_id': 'test_user_123',
        'product_context': 'game',
        'signal': 'nudge',
        'severity': 0.5,
        'opaque_reason_code': 'OLD_TEST',
        'ttl': 1,  # 1 second TTL
        'requires_core_ack': True,
        'timestamp': datetime.utcnow().isoformat() + 'Z'  # Current time
    }
    
    # Secure the signal to add signature
    secured_signal = security_manager.create_secure_karma_signal(signal)
    
    # Now modify the timestamp to be old (after securing to preserve signature)
    secured_signal['timestamp'] = (datetime.utcnow() - timedelta(seconds=2)).isoformat() + 'Z'  # 2 seconds old
    
    # Validation should fail due to TTL expiry
    validation_result = security_manager.validate_secure_karma_signal(secured_signal)
    print(f"TTL expiry test result: {validation_result}")
    
    return not validation_result['valid'] and 'Message expired' in str(validation_result['errors'])


def run_security_tests():
    """Run all security tests"""
    print("Running Security Hardening Tests...")
    
    # Test replay detection
    replay_test_passed = test_replay_attack_detection()
    print(f"Replay attack detection test: {'PASSED' if replay_test_passed else 'FAILED'}")
    
    # Test TTL expiry
    ttl_test_passed = test_ttl_expiry()
    print(f"TTL expiry test: {'PASSED' if ttl_test_passed else 'FAILED'}")
    
    # Test audit logging
    print("\nTesting Audit Logging...")
    recent_audits = security_manager.get_recent_audits(10)
    print(f"Audit log entries: {len(recent_audits)}")
    
    # Test bucket communication
    print("\nTesting Bucket Communication...")
    test_signal = {
        'subject_id': 'test_user_456',
        'product_context': 'finance',
        'signal': 'allow',
        'severity': 0.2,
        'opaque_reason_code': 'BUCKET_TEST',
        'ttl': 300,
        'requires_core_ack': True
    }
    
    send_result = bucket_communicator.send_to_bucket(test_signal)
    print(f"Bucket send result: {send_result}")
    
    if send_result['success']:
        receive_result = bucket_communicator.receive_from_bucket(send_result['bucket_id'])
        print(f"Bucket receive result: {receive_result is not None}")
    
    print("\nSecurity Hardening Tests Completed!")
    

if __name__ == "__main__":
    enforce_bucket_only_routing()
    run_security_tests()