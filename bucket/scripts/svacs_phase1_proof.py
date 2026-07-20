"""
SVACS Phase 1 Live Proof Script
Purpose: Execute representative SVACS → Bucket write → read-back → verify flow
Produces: Evidence for SVACS_BUCKET_LIVE_PROOF.md
"""
import requests
import uuid
import time
import json
import hashlib
import sys
from datetime import datetime, timezone

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8005"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
EXEC_TIME = datetime.now(timezone.utc).isoformat()

print("=" * 60)
print("SVACS → BUCKET LIVE PROOF — PHASE 1")
print(f"Execution timestamp: {EXEC_TIME}")
print(f"Target: {BASE}")
print("=" * 60)

# ──────────────────────────────────────────────
# STEP 0: Get current chain head
# ──────────────────────────────────────────────
print("\n[STEP 0] Fetching current chain head...")
try:
    lh_resp = requests.get(f"{BASE}/bucket/latest-hash", timeout=30)
    lh = lh_resp.json()
    prev_hash = lh.get("last_hash")
    prev_count = lh.get("artifact_count", 0)
    print(f"  Chain head: {prev_hash}")
    print(f"  Artifact count before: {prev_count}")
except Exception as e:
    print(f"  WARNING: Could not fetch chain head: {e}")
    prev_hash = None
    prev_count = 0

# ──────────────────────────────────────────────
# STEP 1: Compose SVACS representative artifact
# ──────────────────────────────────────────────
TRACE_ID = f"svacs-tantra-{int(time.time())}"
ARTIFACT_ID = str(uuid.uuid4())

artifact = {
    "artifact_id": ARTIFACT_ID,
    "trace_id": TRACE_ID,
    "timestamp_utc": TIMESTAMP,
    "schema_version": "1.0.0",
    "source_module_id": "svacs.perception",
    "artifact_type": "perception",
    "parent_hash": prev_hash,
    "payload": {
        "trace_id": TRACE_ID,
        "vessel_type": "cargo",
        "confidence_score": 0.9418,
        "dominant_freq_hz": 166.0,
        "anomaly_flag": False,
        "stage": "perception",
        "pipeline": "SVACS",
        "producer": "svacs_team_representative",
        "tantra_phase": "phase1_live_proof"
    }
}

print(f"\n[STEP 1] SVACS artifact composed:")
print(f"  artifact_id: {ARTIFACT_ID}")
print(f"  trace_id:    {TRACE_ID}")
print(f"  source:      svacs.perception")
print(f"  parent_hash: {prev_hash}")

# ──────────────────────────────────────────────
# STEP 2: Write to Bucket
# ──────────────────────────────────────────────
print(f"\n[STEP 2] Writing to Bucket: POST {BASE}/bucket/artifact")
write_start = time.time()
write_resp = requests.post(f"{BASE}/bucket/artifact", json=artifact, timeout=60)
write_latency = round((time.time() - write_start) * 1000, 1)

print(f"  HTTP Status: {write_resp.status_code}  ({write_latency}ms)")
print(f"  Response body:\n{json.dumps(write_resp.json(), indent=4)}")

if write_resp.status_code != 200:
    print("\n[FAIL] Write rejected. Phase 1 cannot be completed until write succeeds.")
    sys.exit(1)

write_data = write_resp.json()
server_hash = write_data.get("hash")
returned_artifact_id = write_data.get("artifact_id", ARTIFACT_ID)

# ──────────────────────────────────────────────
# STEP 3: Compute local hash and compare
# ──────────────────────────────────────────────
print(f"\n[STEP 3] Computing local hash for verification...")
hash_input = {
    "artifact_id": artifact["artifact_id"],
    "trace_id": artifact["trace_id"],
    "timestamp_utc": artifact["timestamp_utc"],
    "schema_version": artifact["schema_version"],
    "source_module_id": artifact["source_module_id"],
    "artifact_type": artifact["artifact_type"],
    "parent_hash": artifact["parent_hash"],
    "payload": artifact["payload"],
}
serialized = json.dumps(hash_input, sort_keys=True, separators=(',', ':'))
local_hash = hashlib.sha256(serialized.encode('utf-8')).hexdigest()

print(f"  Server hash: {server_hash}")
print(f"  Local hash:  {local_hash}")

if server_hash == local_hash:
    print("  HASH PROOF: ✅ MATCH — deterministic hash confirmed")
    hash_proof = "PASS"
else:
    print("  HASH PROOF: ⚠  MISMATCH (server may use different canonical fields)")
    hash_proof = "MISMATCH"

# ──────────────────────────────────────────────
# STEP 4: Read back the artifact
# ──────────────────────────────────────────────
print(f"\n[STEP 4] Reading back artifact: GET {BASE}/bucket/artifact/{returned_artifact_id}")
read_resp = requests.get(f"{BASE}/bucket/artifact/{returned_artifact_id}", timeout=30)
print(f"  HTTP Status: {read_resp.status_code}")
print(f"  Response body:\n{json.dumps(read_resp.json(), indent=4)}")

if read_resp.status_code != 200:
    print("\n[FAIL] Read-back failed.")
    sys.exit(2)

read_body = read_resp.json()
stored = read_body.get("artifact") if isinstance(read_body, dict) and read_body.get("artifact") else read_body

# ──────────────────────────────────────────────
# STEP 5: Verify trace_id preserved
# ──────────────────────────────────────────────
print(f"\n[STEP 5] Verifying trace continuity...")
stored_trace = stored.get("trace_id")
print(f"  Original trace_id:  {TRACE_ID}")
print(f"  Stored trace_id:    {stored_trace}")

if stored_trace == TRACE_ID:
    print("  TRACE PROOF: ✅ trace_id preserved exactly")
    trace_proof = "PASS"
else:
    print("  TRACE PROOF: ❌ trace_id MUTATED")
    trace_proof = "FAIL"

# ──────────────────────────────────────────────
# STEP 6: Lineage check
# ──────────────────────────────────────────────
print(f"\n[STEP 6] Verifying lineage...")
stored_parent = stored.get("parent_hash")
print(f"  Expected parent_hash: {prev_hash}")
print(f"  Stored parent_hash:   {stored_parent}")

if stored_parent == prev_hash:
    print("  LINEAGE PROOF: ✅ parent_hash matches chain head at time of write")
    lineage_proof = "PASS"
else:
    print("  LINEAGE PROOF: ❌ parent_hash mismatch")
    lineage_proof = "FAIL"

# ──────────────────────────────────────────────
# STEP 7: Confirm chain advanced
# ──────────────────────────────────────────────
print(f"\n[STEP 7] Confirming chain advanced...")
new_lh = requests.get(f"{BASE}/bucket/latest-hash", timeout=30).json()
print(f"  New chain head: {new_lh.get('last_hash')}")
print(f"  Artifact count: {new_lh.get('artifact_count')}")

# ──────────────────────────────────────────────
# STEP 8: FAILURE INJECTION TEST
# ──────────────────────────────────────────────
print(f"\n[STEP 8] Failure injection — broken lineage test...")
bad_artifact = {
    "artifact_id": str(uuid.uuid4()),
    "trace_id": f"svacs-bad-{int(time.time())}",
    "timestamp_utc": TIMESTAMP,
    "schema_version": "1.0.0",
    "source_module_id": "svacs.perception",
    "artifact_type": "perception",
    "parent_hash": "INVALID_HASH_INTENTIONAL",
    "payload": {"test": "failure_injection"}
}
fail_resp = requests.post(f"{BASE}/bucket/artifact", json=bad_artifact, timeout=30)
print(f"  HTTP Status (expected 400): {fail_resp.status_code}")
print(f"  Rejection body: {fail_resp.text}")
lineage_fail_visible = fail_resp.status_code in (400, 422)
print(f"  FAILURE VISIBILITY: {'✅ Rejection visible' if lineage_fail_visible else '❌ Not rejected'}")

# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("PHASE 1 PROOF SUMMARY")
print("=" * 60)
print(f"  Execution timestamp:     {EXEC_TIME}")
print(f"  artifact_id:             {ARTIFACT_ID}")
print(f"  trace_id:                {TRACE_ID}")
print(f"  server_hash:             {server_hash}")
print(f"  parent_hash:             {prev_hash}")
print(f"  Hash proof:              {hash_proof}")
print(f"  Trace proof:             {trace_proof}")
print(f"  Lineage proof:           {lineage_proof}")
print(f"  Failure visibility:      {'PASS' if lineage_fail_visible else 'FAIL'}")
print("=" * 60)

# Output JSON for proof document
proof = {
    "phase": "Phase 1 — SVACS Live Proof",
    "execution_time_utc": EXEC_TIME,
    "target": BASE,
    "artifact_id": ARTIFACT_ID,
    "trace_id": TRACE_ID,
    "server_hash": server_hash,
    "local_hash": local_hash,
    "parent_hash": prev_hash,
    "hash_proof": hash_proof,
    "trace_proof": trace_proof,
    "lineage_proof": lineage_proof,
    "failure_injection_visible": lineage_fail_visible,
    "write_response": write_data,
    "read_response": read_body,
    "failure_rejection": {"status": fail_resp.status_code, "body": fail_resp.text}
}

with open("data/svacs_phase1_proof.json", "w") as f:
    json.dump(proof, f, indent=2)

print(f"\n  Proof JSON saved: data/svacs_phase1_proof.json")
