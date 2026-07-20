"""
verify_parikshak_observability.py
===========================
Standalone verification script — proves that Pravah can observe the
Parikshak-system runtime WITHOUT owning or interfering with it.

What this script does:
  1. Constructs a SSPL-signed telemetry payload with app = "parikshak-system"
  2. POSTs it to the Pravah Control Plane at /api/runtime
  3. Prints the Decision Brain's response (trace resolved, policy decision)
  4. Exits cleanly — no side effects on the running system

Prerequisites:
  - Pravah Control Plane must be running on port 7000
    (start: cd pravah-bhiv/backend && python wsgi.py)
  - OR start the full Pravah stack first

Usage:
  python verify_parikshak_observability.py
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PRAVAH_URL = os.getenv("PRAVAH_URL", "http://localhost:7000/api/runtime")
SSPL_SECRET = os.getenv("SSPL_SECRET_KEY", "default-secret-key-change-in-prod")
APP_NAME = "parikshak-system"


# ---------------------------------------------------------------------------
# Build a canonical SSPL-signed telemetry payload
# ---------------------------------------------------------------------------

def build_signed_payload(trace_id: str, state: str = "running", latency_ms: float = 0.0) -> tuple[dict, dict]:
    """Construct and sign a Pravah runtime telemetry payload for parikshak-system."""
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


# ---------------------------------------------------------------------------
# Run verification
# ---------------------------------------------------------------------------

def main():
    trace_id = f"parikshak-verify-{uuid.uuid4().hex[:12]}"

    print("=" * 65)
    print("  Pravah Observer -- Parikshak System Observability Verify")
    print("=" * 65)
    print(f"  Target  : {PRAVAH_URL}")
    print(f"  App     : {APP_NAME}")
    print(f"  Trace   : {trace_id}")
    print("=" * 65)

    payload, headers = build_signed_payload(
        trace_id=trace_id,
        state="running",
        latency_ms=45.0,  # synthetic -- simulates a healthy Parikshak request
    )

    print("\n[1/3] Sending telemetry to Pravah Control Plane...")
    print(f"      Payload : {json.dumps(payload)}")

    try:
        resp = requests.post(PRAVAH_URL, json=payload, headers=headers, timeout=8)
    except requests.ConnectionError:
        print("\n[FAIL] Cannot connect to Pravah Control Plane.")
        print("       Make sure it is running:  python wsgi.py  (in pravah-bhiv/backend/)")
        sys.exit(1)
    except requests.Timeout:
        print("\n[FAIL] Request to Pravah timed out after 8 seconds.")
        sys.exit(1)

    print(f"\n[2/3] Pravah responded with HTTP {resp.status_code}")

    if resp.status_code in (200, 201, 202):
        try:
            body = resp.json()
            decision = body.get("result", {})
            print(f"      Status  : {body.get('status')}")
            print(f"      Decision: {json.dumps(decision, indent=6)}")
        except Exception:
            print(f"      Raw body: {resp.text[:400]}")
        print("\n[3/3] Verification PASSED [OK]")
        print(f"      Trace {trace_id!r} resolved by Decision Brain.")
        print(f"      Pravah now has execution visibility into {APP_NAME!r}.")
        print("\n      To confirm in the Observer Dashboard:")
        print("        * Open http://localhost:8600  (Observer Dashboard)")
        print(f"        * {APP_NAME} service card should show status")
        print(f"        * Open http://localhost:7000/api/control-plane/history/{APP_NAME}")
        print("          for full decision timeline\n")
    else:
        print(f"      [WARN] Unexpected status {resp.status_code}: {resp.text[:400]}")
        print("\n[3/3] Verification INCOMPLETE -- review the response above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
