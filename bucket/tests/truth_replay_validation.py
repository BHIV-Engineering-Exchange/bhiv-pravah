import requests
import uuid
import time
import json
import hashlib
import sys


def compute_hash(artifact: dict) -> str:
    hash_input = {
        "artifact_id": artifact.get("artifact_id"),
        "trace_id": artifact.get("trace_id"),
        "timestamp_utc": artifact.get("timestamp_utc"),
        "schema_version": artifact.get("schema_version"),
        "source_module_id": artifact.get("source_module_id"),
        "artifact_type": artifact.get("artifact_type"),
        "parent_hash": artifact.get("parent_hash"),
        "payload": artifact.get("payload"),
    }
    serialized = json.dumps(hash_input, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def main(base: str):
    print("Running truth & replay validation against:", base)

    # fetch current chain head
    lh = requests.get(f"{base}/bucket/latest-hash", timeout=30).json()
    prev_last = lh.get("last_hash")
    prev_count = lh.get("artifact_count", 0)
    print("Previous chain:", lh)

    TRACE_ID = f"truth-replay-{int(time.time())}"
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "trace_id": TRACE_ID,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema_version": "1.0.0",
        "source_module_id": "test.truth_replay",
        "artifact_type": "truth_event",
        "parent_hash": prev_last if prev_last else None,
        "payload": {"example": "truth replay validation", "step": "write"},
    }

    # Compute the expected local hash (for verification against server's returned hash)
    expected_local_hash = compute_hash(artifact)

    # POST artifact
    print("Posting artifact to:", base)
    r = requests.post(f"{base}/bucket/artifact", json=artifact, timeout=60)
    print("POST status:", r.status_code)
    print("POST response:", r.text)
    r.raise_for_status()
    res = r.json()
    server_hash = res.get("hash")
    artifact_id = res.get("artifact_id") or artifact["artifact_id"]

    print(f"Server returned hash: {server_hash}")
    print(f"Local computed hash: {expected_local_hash}")

    if server_hash != expected_local_hash:
        print("FAIL: server hash does not match local computed hash")
        sys.exit(2)

    # Read back the artifact
    print("Fetching artifact back")
    rr = requests.get(f"{base}/bucket/artifact/{artifact_id}", timeout=30)
    print("GET status:", rr.status_code)
    rr.raise_for_status()
    body = rr.json()
    stored = body.get("artifact") if isinstance(body, dict) and body.get("artifact") else body

    # Recompute hash on read-back
    read_back_hash = compute_hash(stored)
    print(f"Read-back computed hash: {read_back_hash}")

    if read_back_hash != server_hash:
        print("FAIL: read-back hash does not match server hash")
        sys.exit(3)

    # Validate lineage: parent_hash must match previous chain head (if previous existed)
    stored_parent = stored.get("parent_hash")
    print(f"Stored parent_hash: {stored_parent}")
    if prev_last and stored_parent != prev_last:
        print("FAIL: parent_hash mismatch against previous chain head")
        sys.exit(4)

    # Validate chain advanced
    new_lh = requests.get(f"{base}/bucket/latest-hash", timeout=30).json()
    print("New chain:", new_lh)
    new_last = new_lh.get("last_hash")
    new_count = new_lh.get("artifact_count", 0)
    if new_last != server_hash:
        print("FAIL: chain head was not updated to stored hash")
        sys.exit(5)
    if new_count != prev_count + 1:
        print("WARN: artifact_count did not increase by 1 (prev, new):", prev_count, new_count)

    print("PASS: write integrity, read-back integrity, lineage continuity verified")
    # Print artifact location info
    print("artifact_id:", artifact_id)
    print("hash:", server_hash)


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9005"
    main(base)
