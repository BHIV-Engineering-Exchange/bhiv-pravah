# PRANA Tamper-Evident Architecture

**Status:** Architecture Specification  
**Version:** 1.0.0  
**Objective:** Cryptographic proof of non-repudiation and structural integrity.

## 1. Design Principles
To justify complexity, every mechanism must prevent a specific threat identified in the PRANA_THREAT_MODEL_CANON.md (e.g., T3: Bucket Data Modification).

### 1.1 Hash Chaining (The "Ledger Backbone")
Every packet stored in the Bucket must contain a hash of the previous packet.
- **Algorithm:** SHA-256 (PQC-resistant for collision resistance).
- **Structure:** `current_hash = SHA256(packet_content + previous_hash)`
- **Detection:** Prevents reordering and deletion. If packet $N$ is deleted, the chain from $N+1$ onwards breaks.

### 1.2 Merkle Tree Verification (Batch Integrity)
For high-performance audit, packets are aggregated into "Blocks" (e.g., hourly or every 1000 packets).
- **Root Hash:** The Merkle Root of the block is signed by a Custodian Key.
- **Proof:** Any single packet can be verified against the signed Root with $O(\log N)$ complexity.
- **Detection:** Detects single-packet modification without re-scanning the entire chain.

### 1.3 Append-Only Log Structure
The physical storage layer must enforce write-once-read-many (WORM) semantics.
- **Implementation:** Database triggers or cloud-level Object Lock (e.g., S3 Object Lock).
- **Validation:** Periodic "Snap Audit" by the Core Layer to verify the head of the chain matches the expected hash.

## 2. Cryptographic Packet Signing
Each PRANA emission must be signed at the source.
- **Scheme:** Ed25519 (Classical) with transition path to SPHINCS+ (PQC).
- **Packet Structure:**
```json
{
  "payload": { ... },
  "prev_hash": "...",
  "signature": "...",
  "signer_id": "prana-sensor-idx-01"
}
```

## 3. Explicit Detection Matrix

| Attack               | Detection Mechanism                   | Verification Point                            |
| :------------------- | :------------------------------------ | :-------------------------------------------- |
| **Reordering**       | Hash Chaining                         | Sequence validation during ingestion & audit. |
| **Deletion**         | Hash Chaining + Block Height          | Continuous counter validation.                |
| **Modification**     | Packet Signatures + Merkle Proof      | Runtime validation on retrieval.              |
| **Replay Injection** | Nonce + Strictly Increasing Timestamp | API-level idempotency check.                  |

## 4. Verification Audit Flow
The **Audit Trail** is not a passive log; it is an active validation API.

1. **Proof Generation:** Bucket generates a Merkle Proof for a requested `packet_id`.
2. **Independent Verification:** The Auditor (external or Core) fetches the signed Block Root and verifies the Merkle Path.
3. **Chain Crawl:** Periodic verification of the entire hash chain from the last "Genesis Snapshot".

## 5. Integrity Validation API (Non-Runtime Altering)
- `GET /api/v1/audit/verify-integrity`: Returns status of the hash chain.
- `GET /api/v1/audit/get-proof/{packet_id}`: Returns Merkle Proof for a specific packet.
- **Constraint:** This API does not affect the observation window or signal emission. It is for structural fortification.

## 6. Justification of Complexity
- **Why Hash Chaining?** Necessary to prevent "Silent Schema Mutation" or selective data deletion by internal rogues.
- **Why Merkle Trees?** Enables scalable decentralized verification without requiring the Auditor to store the entire dataset.
- **Why Signatures?** Establishes non-repudiation; even an admin cannot forge a PRANA packet without the private sensor key.

## 7. Operational Status
PRANA remains a "boring infrastructure" component, but with a **cryptographic seal**. This ensures that even if the infrastructure is compromised, the telemetry remains a source of objective truth.
