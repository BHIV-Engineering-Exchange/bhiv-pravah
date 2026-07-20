import requests
import uuid
import time
import sys

def main(base):
    TRACE_ID = f"trace-test-{int(time.time())}"
    # fetch current chain head and use as parent_hash when present
    try:
        lh = requests.get(f"{base}/bucket/latest-hash", timeout=60).json()
        parent = lh.get("last_hash") if isinstance(lh, dict) else None
    except Exception:
        parent = None

    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "trace_id": TRACE_ID,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema_version": "1.0.0",
        "source_module_id": "test.runner",
        "artifact_type": "ingestion",
        "parent_hash": parent,
        "payload": {"test": "trace-continuity"}
    }

    print("Posting artifact to:", base)
    r = requests.post(f"{base}/bucket/artifact", json=artifact, timeout=60)
    print("POST status:", r.status_code)
    try:
        print("POST response:", r.text)
    except Exception:
        pass
    r.raise_for_status()
    res = r.json()
    artifact_id = res.get("artifact_id") or artifact["artifact_id"]
    print("Stored artifact_id:", artifact_id)

    print("Fetching artifact back")
    r2 = requests.get(f"{base}/bucket/artifact/{artifact_id}", timeout=60)
    print("GET status:", r2.status_code)
    r2.raise_for_status()
    body = r2.json()
    # response shape may be {"artifact": {...}}
    stored = body.get("artifact") if isinstance(body, dict) and body.get("artifact") else body
    stored_trace = stored.get("trace_id")
    print("Stored trace_id:", stored_trace)
    if stored_trace != TRACE_ID:
        raise SystemExit(f"Trace continuity failed: expected {TRACE_ID}, got {stored_trace}")
    print("Trace continuity OK")


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8005"
    main(base)
