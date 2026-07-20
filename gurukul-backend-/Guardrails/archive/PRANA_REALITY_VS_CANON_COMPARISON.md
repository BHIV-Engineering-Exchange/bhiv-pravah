# PRANA Reality vs. Canon Comparison

**Audit Date**: 2026-02-17  
**Canon Source**: `PRANA_BUCKET_CONTRACT.md` (v1.0.0)  
**Reality Source**: `prana-core` Unified Implementation (2026)

## Strategic Alignment Map

| Feature               | Canon (Spec)         | Reality (Code)            | Alignment |
|-----------------------|----------------------|---------------------------|-----------|
| **Window Duration**   | 2000ms (2s)          | 5000ms (5s)               | **DEVIATED** |
| **Emission Policy**   | Synchronous          | Asynchronous (Queue)      | **DEVIATED** |
| **Retry Posture**     | No Retries (Discard) | 3 Retries + Offline Queue | **DEVIATED** |
| **Storage Backend**   | MongoDB (Bucket)     | PostgreSQL (SQL)          | **DEVIATED** |
| **Payload Integrity** | No PII / Content     | No PII / Content          | **MATCHED** |
| **Append-Only**       | Immutability Guaranteed | Immutability Implemented | **MATCHED** |
| **Failure Mode**      | Fail-Open (Silent)   | Fail-Safe (buffered)      | **DEVIATED** |

## Critical Evaluation

### What Matched Exactly
- **Sovereignty Boundaries**: PRANA does not attempt to control the application. It remains a purely observational telemetry system.
- **Privacy Invariants**: High-integrity adherence to the non-invasive pledge. No keystroke content or mouse coordinates are transmitted.
- **Packet Invariants**: The core data fields (signals, time accounting) are present and correctly validated.

### What Deviated
1. **Timing Window**: The increase from 2s to 5s is a major divergence. While it reduces network load, it reduces the temporal resolution of cognitive state tracking.
2. **Reliability Model**: The "Canon" specifies a discard-on-failure policy to ensure zero system impact. The reality implements a heavy-duty reliability layer (localStorage, retries) which prioritizes data survival over "boring infrastructure" silence.
3. **Database Selection**: The transition to PostgreSQL provides higher integrity but moves away from the flexible document schema often assumed for PRANA buckets.

### Documentation Requirements
- `PRANA_BUCKET_CONTRACT.md` is **OBSOLETE**. It refers to a 2s window and 13-field schema that is no longer in use.
- The failure posture documentation needs to be updated to reflect **Durable Ingestion** rather than ephemeral packet dropping.

---

## FINAL REQUIRED DECLARATION

**Is PRANA Ledger behaving exactly as canon states?**  
**Answer**: **NO**

**Justification**:  
The system's fundamental operational parameters (Window Duration, Retry Posture, and Failure Mode) have fundamentally changed from the Documented Canon (v1.0.0). While the **Privacy and Observational** invariants are perfectly maintained, the **Transmission and Reliability** reality is significantly more complex and durable than the "boring, ephemeral" infrastructure described in the spec. PRANA in reality is a high-availability telemetry ledger, not the simple discard-on-failure signal emitter stated in the canon.
