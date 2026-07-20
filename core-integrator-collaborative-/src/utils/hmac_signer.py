import hmac
import hashlib
import json
import uuid
import time
import base64
from typing import Dict, Any, Optional

def generate_jwt(payload: Dict[str, Any], secret: str) -> str:
    """
    Generates a minimal HS256 JWT token without external libraries.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode('utf-8')).rstrip(b"=").decode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).rstrip(b"=").decode('utf-8')
    
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode('utf-8')
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def sign_payload(payload: Dict[str, Any], secret: str, nonce: Optional[str] = None, ts: Optional[int] = None) -> Dict[str, Any]:
    """
    Signs a payload using HMAC-SHA256 as required by the TTV/TTG engine integration specifications.
    """
    if nonce is None:
        nonce = uuid.uuid4().hex
        
    if ts is None:
        ts = int(time.time() * 1000)
        
    # Serialize the payload deterministically without whitespaces, sorting keys to match JSON.stringify() output
    serialized_payload = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    
    # Message to sign: JSON.stringify(payload) + nonce + ts
    message = serialized_payload + str(nonce) + str(ts)
    
    # Compute signature
    sig = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "payload": payload,
        "nonce": nonce,
        "ts": ts,
        "sig": sig
    }
