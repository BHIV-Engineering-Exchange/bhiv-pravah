import requests
import uuid
import time
import sys

base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8005'
TRACE_ID = f"trace-debug-{int(time.time())}"
artifact = {
  "artifact_id": str(uuid.uuid4()),
  "trace_id": TRACE_ID,
  "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "schema_version": "1.0.0",
  "source_module_id": "test.debug",
  "artifact_type": "ingestion",
  "parent_hash": None,
  "payload": {"test": "trace-debug"}
}

print('POSTing to', base)
resp = requests.post(f"{base}/bucket/artifact", json=artifact, timeout=15)
print('status', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
