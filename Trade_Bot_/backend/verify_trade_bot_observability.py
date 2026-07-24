#!/usr/bin/env python3
"""
verify_trade_bot_observability.py
==================================
Standalone verification script to validate that Pravah can observe the
trade-bot runtime without interfering with it.

What this script does:
  1. Constructs a signed telemetry payload with app = "trade-bot"
  2. POSTs it to the Pravah Control Plane at http://localhost:7000/api/runtime
  3. Prints the Decision Brain's response (trace resolved, policy decision)
  4. Exits cleanly.
"""

import hashlib
import hmac
import json
import os
import sys
import time
import uuid

try:
    import requests
except ImportError:
    print("[ERROR] 'requests' library not found. Run: pip install requests")
    sys.exit(1)

# Configuration
PRAVAH_URL = os.getenv("PRAVAH_URL", "http://localhost:7000/api/runtime")
SSPL_SECRET = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
APP_NAME = "trade-bot"


def build_signed_payload(trace_id: str, state: str = "running", latency_ms: float = 0.0) -> tuple[dict, dict]:
    """Construct and sign a Pravah runtime telemetry payload for trade-bot."""
    payload = {
        "app": APP_NAME,
        "env": "dev",
        "state": state,
        "latency_ms": round(latency_ms, 2),
        "errors_last_min": 0,
        "workers": 1,
    }

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    body_hash = hashlib.sha256(canonical.encode()).hexdigest()
    timestamp = str(int(time.time()))

    sig_data = f"{trace_id}:{timestamp}:{body_hash}"
    signature = hmac.new(
        SSPL_SECRET.encode(),
        sig_data.encode(),
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "X-Trace-Id": trace_id,
        "X-Timestamp": timestamp,
        "X-Trace-Signature": signature,
        "Content-Type": "application/json",
    }

    return payload, headers


def main():
    trace_id = f"trade-bot-verify-{uuid.uuid4().hex[:12]}"

    print("=" * 70)
    print("  Pravah Observer -- Trade Bot Observability Verification")
    print("=" * 70)
    print(f"  Target  : {PRAVAH_URL}")
    print(f"  App     : {APP_NAME}")
    print(f"  Trace   : {trace_id}")
    print("=" * 70)

    payload, headers = build_signed_payload(
        trace_id=trace_id,
        state="running",
        latency_ms=85.0,
    )

    print("\n[1/3] Sending telemetry to Pravah Control Plane...")
    print(f"      Payload : {json.dumps(payload)}")

    try:
        resp = requests.post(PRAVAH_URL, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            print(f"\n[2/3] Pravah responded with HTTP 200")
            print(f"      Status  : {resp.json().get('status')}")
            print(f"      Decision: {json.dumps(resp.json().get('decision', 'noop'))}")
            print(f"\n[3/3] Verification PASSED [OK]")
            print(f"      Trace '{trace_id}' resolved by Decision Brain.")
            print(f"      Pravah now has execution visibility into '{APP_NAME}'.")
        else:
            print(f"\n[ERROR] Request failed with HTTP {resp.status_code}")
            print(f"        Detail: {resp.text}")
            sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Failed to connect to Pravah: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
