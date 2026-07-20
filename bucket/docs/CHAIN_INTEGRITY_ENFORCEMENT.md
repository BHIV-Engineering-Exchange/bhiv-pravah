# Chain Integrity Enforcement

**Document Version:** 1.0.0  
**Last Updated:** 2025-01-20  
**Status:** PRODUCTION ACTIVE

---

## 🎯 Purpose

Ensure artifacts form a **tamper-evident, deterministic chain** that can be replayed to reconstruct exact system state.

---

## 🔗 Hash Chain Mechanics

### Chain Structure

```
┌─────────────────┐
│   Artifact 1    │
│  hash: H1       │
│  parent: null   │ ← First artifact (genesis)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Artifact 2    │
│  hash: H2       │
│  parent: H1     │ ← Links to previous
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Artifact 3    │
│  hash: H3       │
│  parent: H2     │ ← Links to previous
└─────────────────┘
```

### Chain Properties

| Property | Description |
|----------|-------------|
| **Immutable** | Once written, cannot be changed |
| **Linked** | Each artifact references previous |
| **Tamper-evident** | Modification breaks chain |
| **Deterministic** | Replay always produces same result |

---

## 🔐 Parent Hash Validation

### Validation Rules

#### Rule 1: First Artifact

```python
if artifact_count == 0:
    # First artifact (genesis)
    assert artifact.parent_hash is None
    # OR
    assert "parent_hash" not in artifact
```

**Rationale:** Genesis artifact has no parent.

#### Rule 2: Subsequent Artifacts

```python
if artifact_count > 0:
    # Must have parent_hash
    assert "parent_hash" in artifact
    
    # Must link to previous artifact
    assert artifact.parent_hash == previous_artifact.hash
```

**Rationale:** Maintains chain continuity.

### Validation Flow

```python
def validate_parent_hash(artifact, chain_state):
    artifact_count = chain_state["artifact_count"]
    last_hash = chain_state["last_hash"]
    
    if artifact_count == 0:
        # First artifact
        if artifact.get("parent_hash") is not None:
            raise ValueError("First artifact must not have parent_hash")
    else:
        # Subsequent artifact
        if "parent_hash" not in artifact:
            raise ValueError("parent_hash required")
        
        if artifact["parent_hash"] != last_hash:
            raise ValueError(
                f"Invalid parent_hash. "
                f"Expected: {last_hash}, "
                f"Got: {artifact['parent_hash']}"
            )
    
    return True
```

---

## 🚫 Orphan Detection

### What is an Orphan Artifact?

An artifact whose `parent_hash` doesn't exist in the chain.

```
┌─────────────────┐
│   Artifact 1    │
│  hash: H1       │
└─────────────────┘

┌─────────────────┐
│   Artifact 3    │  ← ORPHAN!
│  hash: H3       │
│  parent: H2     │  ← H2 doesn't exist
└─────────────────┘
```

### Prevention Strategy

**Rule:** Parent must exist before child can be added.

```python
def prevent_orphans(artifact, chain_state):
    if chain_state["artifact_count"] > 0:
        expected_parent = chain_state["last_hash"]
        actual_parent = artifact.get("parent_hash")
        
        if actual_parent != expected_parent:
            raise ValueError(
                f"Orphan artifact detected. "
                f"Parent {actual_parent} does not exist."
            )
```

### Why Orphans are Dangerous

1. **Break replay** - Cannot reconstruct state
2. **Indicate tampering** - Missing artifacts
3. **Violate determinism** - Unpredictable ordering

---

## 🔄 Deterministic Replay

### Replay Ordering

Artifacts are replayed in **strict chronological order**:

1. **Primary sort:** `timestamp_utc` (ascending)
2. **Secondary sort:** `parent_hash` chain

### Replay Algorithm

```python
def replay_chain():
    """
    Replay entire artifact chain to reconstruct system state.
    
    Guarantees:
    - Same input → same output
    - Every node produces identical result
    - Tampering is detected
    """
    state = {}
    previous_hash = None
    
    with open("artifact_log.jsonl", "r") as f:
        for line_num, line in enumerate(f, 1):
            artifact = json.loads(line)
            
            # Verify hash
            computed_hash = compute_hash(artifact)
            if artifact["hash"] != computed_hash:
                raise TamperDetected(
                    f"Line {line_num}: Hash mismatch"
                )
            
            # Verify parent chain
            if line_num == 1:
                if artifact.get("parent_hash") is not None:
                    raise ChainBroken(
                        "First artifact has parent_hash"
                    )
            else:
                if artifact["parent_hash"] != previous_hash:
                    raise ChainBroken(
                        f"Line {line_num}: Parent mismatch"
                    )
            
            # Apply artifact to state
            state = apply_artifact(state, artifact)
            previous_hash = artifact["hash"]
    
    return state
```

### Replay Guarantees

| Guarantee | Description |
|-----------|-------------|
| **Deterministic** | Same log → same state |
| **Complete** | All artifacts processed |
| **Ordered** | Chronological sequence |
| **Verified** | Hashes checked |
| **Tamper-evident** | Modifications detected |

---

## 🛡️ Tamper Detection

### How Tampering is Detected

#### Scenario 1: Modified Artifact

```
Original:
Artifact 2: hash=H2, parent=H1, payload={...}

Modified:
Artifact 2: hash=H2', parent=H1, payload={CHANGED}

Detection:
Artifact 3: parent=H2 (expects original)
Actual hash: H2' (modified)
Result: CHAIN BROKEN
```

#### Scenario 2: Deleted Artifact

```
Original Chain:
A1 → A2 → A3 → A4

After Deletion:
A1 → A3 → A4

Detection:
A3.parent_hash = H2 (missing)
Result: ORPHAN DETECTED
```

#### Scenario 3: Inserted Artifact

```
Original Chain:
A1 → A2 → A3

After Insertion:
A1 → A2 → A2.5 → A3

Detection:
A3.parent_hash = H2
A2.5.hash = H2.5
Result: PARENT MISMATCH
```

### Tamper Detection Algorithm

```python
def detect_tampering():
    """
    Scan entire chain for tampering.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    previous_hash = None
    
    for line_num, artifact in enumerate(read_log(), 1):
        # Check 1: Hash integrity
        stored_hash = artifact["hash"]
        computed_hash = compute_hash(artifact)
        
        if stored_hash != computed_hash:
            errors.append(
                f"Line {line_num}: Artifact modified. "
                f"Hash mismatch: {stored_hash} != {computed_hash}"
            )
        
        # Check 2: Parent chain
        if line_num == 1:
            if artifact.get("parent_hash") is not None:
                errors.append(
                    f"Line {line_num}: First artifact has parent"
                )
        else:
            if artifact["parent_hash"] != previous_hash:
                errors.append(
                    f"Line {line_num}: Chain broken. "
                    f"Expected parent: {previous_hash}, "
                    f"Got: {artifact['parent_hash']}"
                )
        
        previous_hash = stored_hash
    
    return len(errors) == 0, errors
```

---

## 📊 Chain State Management

### Chain State Structure

```json
{
  "last_hash": "abc123...",
  "artifact_count": 1234,
  "last_updated": "2025-01-20T10:30:00Z"
}
```

### State Updates

```python
def update_chain_state(artifact):
    """Update chain state after artifact storage."""
    state = load_chain_state()
    
    state["last_hash"] = artifact["hash"]
    state["artifact_count"] += 1
    state["last_updated"] = datetime.utcnow().isoformat()
    
    save_chain_state(state)
```

### State Validation

```python
def validate_chain_state():
    """Verify chain state matches actual log."""
    state = load_chain_state()
    
    # Count artifacts in log
    actual_count = count_artifacts_in_log()
    
    if state["artifact_count"] != actual_count:
        raise StateCorrupted(
            f"State count {state['artifact_count']} "
            f"!= actual count {actual_count}"
        )
    
    # Verify last hash
    last_artifact = read_last_artifact()
    
    if state["last_hash"] != last_artifact["hash"]:
        raise StateCorrupted(
            f"State hash {state['last_hash']} "
            f"!= last artifact hash {last_artifact['hash']}"
        )
```

---

## 🔍 Validation Endpoints

### 1. Validate Entire Chain

```python
POST /bucket/validate-replay

Response:
{
  "valid": true,
  "artifact_count": 1234,
  "errors": []
}
```

### 2. Validate From Specific Artifact

```python
POST /bucket/validate-chain/{artifact_id}

Response:
{
  "valid": true,
  "artifact_id": "A001",
  "chain_length": 100,
  "errors": []
}
```

### 3. Get Chain State

```python
GET /bucket/chain-state

Response:
{
  "last_hash": "abc123...",
  "artifact_count": 1234,
  "last_updated": "2025-01-20T10:30:00Z"
}
```

---

## 🚨 Error Handling

### Error Types

| Error | Cause | Action |
|-------|-------|--------|
| `HashMismatch` | Artifact modified | Reject, log critical |
| `ParentMismatch` | Chain broken | Reject, halt ingestion |
| `OrphanDetected` | Missing parent | Reject, investigate |
| `StateCorrupted` | State/log mismatch | Halt, manual recovery |

### Error Response Format

```json
{
  "error": "ChainIntegrityViolation",
  "message": "Parent hash mismatch",
  "details": {
    "artifact_id": "A123",
    "expected_parent": "H1",
    "actual_parent": "H2",
    "line_number": 456
  },
  "severity": "CRITICAL",
  "action_required": "HALT_INGESTION"
}
```

---

## 📈 Performance Considerations

### Chain Validation Cost

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Append artifact | O(1) | O(1) |
| Validate single | O(1) | O(1) |
| Validate chain | O(n) | O(1) |
| Replay chain | O(n) | O(n) |

### Optimization Strategies

1. **Incremental validation** - Validate only new artifacts
2. **Periodic full validation** - Daily/weekly full chain check
3. **Parallel replay** - Split chain for parallel processing
4. **Checkpoints** - Store validated state snapshots

---

## ✅ Certification Checklist

- [x] First artifact has no parent
- [x] Subsequent artifacts link to previous
- [x] Orphan artifacts rejected
- [x] Hash chain validated on ingestion
- [x] Full chain validation available
- [x] Tampering detected immediately
- [x] Deterministic replay guaranteed
- [x] Chain state synchronized

---

## 📚 Related Documents

- `APPEND_LOG_STORAGE.md` - Storage architecture
- `HASH_AUTHORITY_POLICY.md` - Hash computation
- `REPLAY_PROOF_VALIDATION.md` - Replay mechanics

---

**Bucket Owner:** Ashmit Pandey  
**Certification:** CHAIN INTEGRITY ENFORCED  
**Review Cycle:** 6 months
