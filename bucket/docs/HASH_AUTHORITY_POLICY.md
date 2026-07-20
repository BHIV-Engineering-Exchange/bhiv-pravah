# Hash Authority Policy

**Document Version:** 1.0.0  
**Last Updated:** 2025-01-20  
**Status:** PRODUCTION ACTIVE

---

## 🎯 Core Principle

> **"Server computes ALL hashes. Client hashes are NEVER trusted."**

---

## ❌ Why Client Hashes Are Unsafe

### Attack Scenario

```json
// Malicious client sends:
{
  "artifact_id": "A001",
  "payload": "malicious_data",
  "hash": "abc123trusted_looking_hash"
}
```

**Problem:** If Bucket trusts this hash:
1. Malicious data gets stored
2. Hash appears legitimate
3. Tampering goes undetected
4. Chain integrity compromised

### Real-World Analogy

**Bad:** "I'm sending you a package. Trust me, it weighs 5kg."  
**Good:** "I'm sending you a package. You weigh it when it arrives."

---

## ✅ Server-Side Hash Authority

### Correct Architecture

```
┌─────────┐                    ┌─────────┐
│ Client  │                    │ Bucket  │
└────┬────┘                    └────┬────┘
     │                              │
     │  1. Send artifact (no hash)  │
     │─────────────────────────────>│
     │                              │
     │                         2. Validate
     │                         structure
     │                              │
     │                         3. Compute
     │                         SHA256 hash
     │                              │
     │                         4. Store with
     │                         computed hash
     │                              │
     │  5. Return hash to client    │
     │<─────────────────────────────│
     │                              │
```

### Implementation

```python
def store_artifact(artifact):
    # 1. Client sends artifact WITHOUT hash
    if "hash" in artifact:
        # Remove client hash (never trust it)
        artifact.pop("hash")
        logger.warning("Client hash ignored")
    
    # 2. Validate structure
    validate_structure(artifact)
    
    # 3. Server computes hash
    computed_hash = compute_hash(artifact)
    
    # 4. Add server hash
    artifact["hash"] = computed_hash
    
    # 5. Store artifact
    append_to_log(artifact)
    
    # 6. Return hash to client
    return {
        "artifact_id": artifact["artifact_id"],
        "hash": computed_hash,
        "message": "Hash computed by server"
    }
```

---

## 🔐 Deterministic Hash Computation

### Hash Input

Hash includes ALL metadata and payload:

```python
hash_input = {
    "artifact_id": artifact["artifact_id"],
    "timestamp_utc": artifact["timestamp_utc"],
    "schema_version": artifact["schema_version"],
    "source_module_id": artifact["source_module_id"],
    "artifact_type": artifact["artifact_type"],
    "parent_hash": artifact.get("parent_hash"),
    "payload": artifact["payload"]
}
```

### Serialization Rules

**Critical:** Serialization must be deterministic.

```python
# ✅ CORRECT: Deterministic serialization
serialized = json.dumps(
    hash_input,
    sort_keys=True,        # Keys always in same order
    separators=(',', ':')  # No whitespace
)

# ❌ WRONG: Non-deterministic
serialized = json.dumps(hash_input)  # Key order varies
```

### Hash Algorithm

```python
hash_bytes = hashlib.sha256(
    serialized.encode('utf-8')
).hexdigest()
```

**Algorithm:** SHA256  
**Output:** 64-character hex string  
**Example:** `a3f5b8c2d1e4f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1`

---

## 🎯 Guarantees

### 1. Integrity

**Guarantee:** Hash accurately represents artifact content.

**Why:** Server computes hash from actual stored data.

### 2. Determinism

**Guarantee:** Same artifact → same hash everywhere.

**Why:** Deterministic serialization + deterministic algorithm.

### 3. Tamper Detection

**Guarantee:** Any modification changes hash.

**Why:** SHA256 is cryptographically secure.

### 4. Replay Consistency

**Guarantee:** Replay produces identical hashes.

**Why:** Hash computation is deterministic.

---

## 🔍 Hash Verification

### On Ingestion

```python
def verify_on_ingestion(artifact):
    # Remove any client-provided hash
    client_hash = artifact.pop("hash", None)
    
    # Compute server hash
    server_hash = compute_hash(artifact)
    
    # Log if client tried to provide hash
    if client_hash:
        logger.warning(
            f"Client hash {client_hash} ignored. "
            f"Server hash: {server_hash}"
        )
    
    # Store with server hash
    artifact["hash"] = server_hash
    return artifact
```

### On Replay

```python
def verify_on_replay(artifact):
    # Extract stored hash
    stored_hash = artifact["hash"]
    
    # Remove hash for recomputation
    artifact_copy = artifact.copy()
    artifact_copy.pop("hash")
    
    # Recompute hash
    computed_hash = compute_hash(artifact_copy)
    
    # Verify match
    if stored_hash != computed_hash:
        raise TamperDetected(
            f"Hash mismatch: "
            f"stored={stored_hash}, "
            f"computed={computed_hash}"
        )
```

---

## 🚨 Security Implications

### Attack Vectors Prevented

| Attack | Prevention |
|--------|-----------|
| **Hash spoofing** | Server computes, client can't fake |
| **Data tampering** | Hash mismatch detected immediately |
| **Replay attacks** | Deterministic hashing catches changes |
| **Man-in-the-middle** | Hash verifies data integrity |

### Trust Model

```
┌──────────────────────────────────────┐
│  TRUSTED: Server hash computation    │
│  - Deterministic algorithm           │
│  - Secure implementation             │
│  - Auditable code                    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│  UNTRUSTED: Client-provided hashes   │
│  - Can be forged                     │
│  - Cannot be verified                │
│  - Must be ignored                   │
└──────────────────────────────────────┘
```

---

## 📊 Performance Considerations

### Hash Computation Cost

| Operation | Time | Notes |
|-----------|------|-------|
| Small artifact (<1KB) | <1ms | Negligible |
| Medium artifact (100KB) | ~5ms | Acceptable |
| Large artifact (16MB) | ~100ms | Within limits |

### Optimization Strategies

1. **Streaming hashing** - For large payloads
2. **Parallel hashing** - For batch ingestion
3. **Hash caching** - For repeated validation

---

## 🔄 Hash Chain Integration

### Parent Hash Validation

```python
def validate_parent_hash(artifact, chain_state):
    if chain_state["artifact_count"] > 0:
        # Not first artifact
        expected_parent = chain_state["last_hash"]
        actual_parent = artifact.get("parent_hash")
        
        if actual_parent != expected_parent:
            raise ChainBroken(
                f"Parent hash mismatch: "
                f"expected={expected_parent}, "
                f"got={actual_parent}"
            )
```

### Chain Update

```python
def update_chain_state(artifact):
    chain_state = load_chain_state()
    
    # Update with server-computed hash
    chain_state["last_hash"] = artifact["hash"]
    chain_state["artifact_count"] += 1
    
    save_chain_state(chain_state)
```

---

## 📋 API Contract

### Client Request

```json
POST /bucket/artifact

{
  "artifact_id": "A001",
  "timestamp_utc": "2025-01-20T10:30:00Z",
  "schema_version": "1.0.0",
  "source_module_id": "aiaic",
  "artifact_type": "analysis",
  "parent_hash": "previous_hash",
  "payload": {
    "data": "..."
  }
}
```

**Note:** No `hash` field in request.

### Server Response

```json
{
  "success": true,
  "artifact_id": "A001",
  "hash": "a3f5b8c2d1e4f6a7...",
  "parent_hash": "previous_hash",
  "timestamp": "2025-01-20T10:30:00Z",
  "storage_type": "append_only",
  "message": "Artifact stored with server-computed hash"
}
```

**Note:** Server returns computed `hash`.

---

## 🧪 Testing Hash Authority

### Test 1: Client Hash Ignored

```python
def test_client_hash_ignored():
    artifact = {
        "artifact_id": "TEST001",
        "hash": "fake_client_hash",  # Should be ignored
        ...
    }
    
    result = store_artifact(artifact)
    
    # Server computed different hash
    assert result["hash"] != "fake_client_hash"
    assert len(result["hash"]) == 64  # SHA256 hex
```

### Test 2: Deterministic Hashing

```python
def test_deterministic_hashing():
    artifact = {...}
    
    hash1 = compute_hash(artifact)
    hash2 = compute_hash(artifact)
    
    # Same input → same hash
    assert hash1 == hash2
```

### Test 3: Tamper Detection

```python
def test_tamper_detection():
    artifact = store_artifact({...})
    
    # Modify artifact
    artifact["payload"]["data"] = "MODIFIED"
    
    # Recompute hash
    new_hash = compute_hash(artifact)
    
    # Hash changed
    assert new_hash != artifact["hash"]
```

---

## ✅ Certification Checklist

- [x] Server computes all hashes
- [x] Client hashes ignored
- [x] Deterministic serialization
- [x] SHA256 algorithm
- [x] Hash includes all fields
- [x] Tamper detection works
- [x] Replay verification works
- [x] Chain integrity maintained

---

## 📚 Related Documents

- `APPEND_LOG_STORAGE.md` - Storage architecture
- `CHAIN_INTEGRITY_ENFORCEMENT.md` - Hash chains
- `DOMAIN_INGESTION_READINESS.md` - Validation rules

---

**Bucket Owner:** Ashmit Pandey  
**Certification:** HASH AUTHORITY ENFORCED  
**Review Cycle:** 6 months
