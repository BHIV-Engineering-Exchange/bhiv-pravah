# PRANA Hash Chain Specification (Deterministic)

**Status:** FINALIZED  
**Version:** 1.0.1  
**Target Tables:** `prana_packets`, `review_output_versions`, `next_task_versions`

## 1. Objective
Define a deterministic, verifiable cryptographic hash chain for the PRANA Ledger to ensure data integrity and tamper-evidence across primary telemetry and versioned outputs.

## 2. Cryptographic Primitive
*   **Algorithm**: SHA-256
*   **Canonicalization**: Data must be serialized to a canonical UTF-8 JSON string (sorted keys, no spaces) before hashing.

## 3. Chaining Structure
Each record `R(n)` in the target tables will contain:
1.  `previous_hash`: The `current_hash` of the preceding record `R(n-1)` in the same chain (e.g., same `submission_id` or global sequence).
2.  `current_hash`: The hash of the current record's content combined with the `previous_hash`.

### 3.1 Genesis Record
The first record in any chain will have a `previous_hash` of:
`0000000000000000000000000000000000000000000000000000000000000000` (64 zeros).

## 4. Hash Formulas

### 4.1 PranaPacket Chain
```python
data_to_hash = {
    "packet_id": R.packet_id,
    "user_id": R.user_id,
    "client_timestamp": R.client_timestamp.isoformat(),
    "cognitive_state": R.cognitive_state,
    "active_seconds": R.active_seconds,
    "idle_seconds": R.idle_seconds,
    "away_seconds": R.away_seconds,
    "integrity_score": R.integrity_score,
    "raw_signals": R.raw_signals,
    "previous_hash": R.previous_hash
}
```

### 4.2 ReviewOutputVersions Chain (Linked by `submission_id`)
```python
data_to_hash = {
    "submission_id": R.submission_id,
    "version": R.version,
    "review_json": R.review_json,
    "created_at": R.created_at.isoformat(),
    "previous_hash": R.previous_hash
}
```

### 4.3 NextTaskVersions Chain (Linked by `submission_id`)
```python
data_to_hash = {
    "submission_id": R.submission_id,
    "version": R.version,
    "next_task_json": R.next_task_json,
    "created_at": R.created_at.isoformat(),
    "previous_hash": R.previous_hash
}
```

## 5. Implementation Rules
1.  **Immutability**: Once a hash is committed, the record is locked.
2.  **Deterministic Sort**: `raw_signals` and nested JSON must use `sort_keys=True`.
3.  **Atomic commit**: Repository must calculate the hash of the *last* known version before inserting the new one, ensuring a strict linear chain.

## 6. Verification Logic
Verification will be performed by re-traversing the chain from Genesis or a known checkpoint and re-calculating hashes. Any mismatch flags a **Tamper Event**.
