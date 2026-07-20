import unittest
import json
import hmac
import hashlib
import time
from src.utils.hmac_signer import sign_payload, generate_jwt

class TestHMACSigner(unittest.TestCase):
    def test_sign_payload_deterministic(self):
        payload = {"game_mode": "sidescroller", "entities": [{"id": "p1"}]}
        secret = "test_shared_secret"
        nonce = "static_nonce_123"
        ts = 1777353996503
        
        envelope = sign_payload(payload, secret, nonce, ts)
        
        self.assertEqual(envelope["payload"], payload)
        self.assertEqual(envelope["nonce"], nonce)
        self.assertEqual(envelope["ts"], ts)
        
        # Verify manually computed signature
        serialized = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        message = serialized + nonce + str(ts)
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        self.assertEqual(envelope["sig"], expected_sig)

    def test_sign_payload_auto_gen(self):
        payload = {"x": 1}
        secret = "secret"
        envelope = sign_payload(payload, secret)
        
        self.assertIsNotNone(envelope["nonce"])
        self.assertIsNotNone(envelope["ts"])
        self.assertIsNotNone(envelope["sig"])
        self.assertEqual(envelope["payload"], payload)

    def test_generate_jwt(self):
        payload = {"iss": "bhiv_core", "exp": int(time.time()) + 3600}
        secret = "jwt_secret_key"
        token = generate_jwt(payload, secret)
        
        parts = token.split(".")
        self.assertEqual(len(parts), 3)

if __name__ == "__main__":
    unittest.main()
