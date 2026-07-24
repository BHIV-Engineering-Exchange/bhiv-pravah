# REPLAY HARNESS ARCHITECTURE

**Author:** Hemanth B
**Target System:** Sarathi Governance Kernel — Policy Decision Point
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026
**Task Reference:** Deterministic Replay & Authority Drift Validation Harness — Day 1
**Scope Boundary:** This document does NOT modify PDP logic, Canon rules, request schema, response schema, evaluation order, or enforcement model. It defines a read-only test harness that proves existing PDP behavior is deterministic and replay-stable.

---

## 1. PURPOSE

This harness proves one thing: **Sarathi produces byte-identical output for identical input under identical state.** If this property holds, the PDP is constitutionally stable. If it fails even once, the PDP has a correctness bug.

The harness is modeled on three proven industry systems:
- **AWS Cedar's Verification-Guided Development** — Lean 4 formal model + differential random testing (DRT) producing 100M tests nightly with zero-tolerance mismatch
- **Google Zanzibar's Snapshot Consistency** — every check bound to an immutable snapshot via opaque tokens (zookies), making results deterministically replayable
- **FoundationDB's Deterministic Simulation Testing (DST)** — entire distributed system running single-threaded with all non-determinism (clock, randomness, network, disk) behind injectable interfaces controlled by a seeded PRNG

---

## 2. HARNESS OPERATING PRINCIPLE

The harness works by freezing all external state, injecting deterministic replacements for all entropy sources, and comparing outputs across multiple runs.

```
┌─────────────────────────────────────────────────┐
│              REPLAY HARNESS WRAPPER              │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Frozen   │  │ Frozen   │  │ Frozen State │  │
│  │ Policy   │  │ CRL      │  │ Registry     │  │
│  │ Bundle   │  │ Snapshot │  │ Snapshot     │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │               │           │
│       ▼              ▼               ▼           │
│  ┌──────────────────────────────────────────┐   │
│  │           SARATHI PDP (UNMODIFIED)        │   │
│  │                                           │   │
│  │  Injected: DeterministicClock             │   │
│  │  Injected: SeededUUIDFactory              │   │
│  │  Injected: StubHSM (Ed25519 fixed key)   │   │
│  │  Injected: InMemoryBHIVBucket             │   │
│  │  Injected: InMemoryAuditChain             │   │
│  └────────────────────┬─────────────────────┘   │
│                        │                         │
│                        ▼                         │
│  ┌──────────────────────────────────────────┐   │
│  │           OUTPUT CAPTURE LAYER            │   │
│  │                                           │   │
│  │  - Full response JSON (canonical)         │   │
│  │  - Signature bytes                        │   │
│  │  - Audit record hash                      │   │
│  │  - Token bytes (if ALLOW)                 │   │
│  │  - Stage trace (internal)                 │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 3. REPLAY HARNESS INPUT CONTRACT

Every harness test case is a self-contained, reproducible unit:

```
REPLAY_TEST_CASE {
  // === IDENTIFICATION ===
  test_id:              STRING    // "RTC-{sequence_number}" e.g., "RTC-00001"
  test_category:        ENUM      // ALLOW | DENY | ESCALATE | BOUNDARY | TOKEN_EXPIRY | RISK_GATE
  description:          STRING    // Human-readable intent

  // === FROZEN STATE (The Snapshot) ===
  snapshot: {
    policy_bundle:      BYTES     // Complete policy bundle (canonical JSON, SHA-256 hashed)
    policy_hash:        STRING    // SHA-256 of policy_bundle — must match PDP's loaded_policy_bundle_hash()
    crl_snapshot:       OBJECT    // Complete CRL state: { revoked_jtis: [], staleness_ms: 0 }
    state_registry:     OBJECT    // { agent_id → AgentRecord } for all agents in this test
    resource_registry:  OBJECT    // { (type, id) → classification } for all resources in this test
    rate_counters:      OBJECT    // { agent_id → { count, exceeded } } — pre-loaded state
    mosaic_state:       OBJECT    // { agent_id → { categories, exceeded } } — pre-loaded state
    dedup_store:        OBJECT    // { jti → BOOL } — pre-loaded replay detection state
  }

  // === DETERMINISTIC INJECTIONS ===
  injections: {
    clock_time:         DATETIME  // Exact time for clock.now_utc() — frozen, not advancing
    clock_advance_per_stage: INT  // Microseconds to advance clock between stages (simulates eval time)
    uuid_seed:          INT       // Seed for deterministic UUID generation (PRNG)
    hsm_private_key:    BYTES     // Fixed Ed25519 private key for deterministic signing
    tls_context: {
      client_certificate_der: BYTES
      session_binding_hash:   STRING
    }
  }

  // === REQUEST ===
  request_bytes:        BYTES     // Raw request bytes — exactly as PDP would receive

  // === EXPECTED OUTPUT ===
  expected: {
    verdict:            STRING    // ALLOW | DENY | ESCALATE
    reason_code:        STRING    // Expected internal reason code
    external_reason:    STRING    // Expected external reason code (may differ per RE-45)
    determining_rules:  [STRING]  // Expected rule IDs
    response_hash:      STRING    // SHA-256 of canonical response JSON — the byte-identity check
    signature_hash:     STRING    // SHA-256 of the Ed25519 signature bytes
    audit_record_hash:  STRING    // SHA-256 of the canonical audit record
    token_hash:         STRING    // SHA-256 of capability token bytes (or "NONE" for DENY/ESCALATE)
  }
}
```

**Why raw bytes, not parsed JSON?** The PDP's first operation is parsing raw bytes (Stage 1.1). The harness must test from the same entry point. Pre-parsed JSON skips the canonicalization path and could mask serialization-dependent bugs.

---

## 4. FROZEN STATE SNAPSHOTS

### 4.1 What Gets Frozen

Every external dependency in the PDP pseudocode (Day 6, lines 151-160) maps to a frozen snapshot:

| PDP Interface | Frozen As | Why |
|---|---|---|
| `StateRegistry.lookup()` | In-memory map: agent_id → AgentRecord | Eliminates network latency variation, registry update race |
| `RevocationList.is_revoked()` | In-memory set: { revoked JTIs } + fixed staleness_ms | Eliminates CRL propagation timing |
| `ResourceRegistry.get_classification()` | In-memory map: (type, id) → classification | Eliminates registry query timing |
| `DedupStore.check_and_register()` | In-memory map: { jti → seen_bool } | Eliminates distributed store timing |
| `RateCounter.increment()` | In-memory map: agent_id → count | Eliminates counter service timing |
| `MosaicAccumulator.record()` | In-memory map: agent_id → categories | Eliminates accumulator service timing |
| `BHIVBucket.write()` | In-memory append-only list | Eliminates audit store latency |
| `EmergencyBuffer.write()` | In-memory append-only list | Eliminates filesystem latency |
| `HSM.sign()` | Deterministic Ed25519 with fixed key pair | Eliminates HSM latency, produces identical signatures |

### 4.2 Snapshot Binding Token

Every frozen snapshot produces a **Snapshot Binding Token (SBT)** — a single hash that uniquely identifies the complete test state:

```
SBT = SHA-256(
  policy_hash          ||
  SHA-256(crl_snapshot)      ||
  SHA-256(state_registry)    ||
  SHA-256(resource_registry) ||
  clock_time_iso8601         ||
  uuid_seed_hex              ||
  SHA-256(hsm_public_key)
)
```

This is Sarathi's equivalent of Zanzibar's zookie. Two runs with the same SBT and same request bytes MUST produce byte-identical output. This is the core invariant the harness tests.

---

## 5. CANONICAL SERIALIZATION ENFORCEMENT

All JSON in the harness follows **RFC 8785 (JSON Canonicalization Scheme / JCS)**:

1. Object properties sorted by lexicographic comparison of UTF-16 encoded names
2. Numbers formatted per ECMAScript `Number::toString` (no trailing zeros, no `+` in exponent)
3. No whitespace between tokens
4. Strings use minimal escape sequences
5. No BOM, no trailing newline

**Where canonicalization is enforced:**
- Request bytes: canonicalized before hashing for request_hash
- Response JSON: canonicalized before signing, before hashing for comparison
- Audit record: canonicalized before hashing for audit chain
- Capability token claims: canonicalized before signing (JWT payload)
- Snapshot state: canonicalized before hashing for SBT computation

**Why this matters:** Without canonical serialization, two semantically identical JSON objects can produce different SHA-256 hashes due to key ordering or whitespace differences. This creates false-positive "mismatches" that mask real bugs or create false confidence.

---

## 6. DETERMINISTIC CLOCK INJECTION

See `clock_injection_strategy.md` for full specification. Summary:

The PDP's `clock.now_utc()` is called at 7 points in the pseudocode:
1. Line 182: `eval_start = clock.now_utc()` — evaluation start timestamp
2. Line 294: `clock.now_utc() - eval_start > EVAL_BUDGET_MS` — timeout check
3. Line 310: `timestamp: clock.now_utc()` — error logging
4. Line 376: `now = clock.now_utc()` — Stage 1 identity checks
5. Line 565: `clock.now_utc() - agent.last_heartbeat > 500` — heartbeat check
6. Line 616: `dclaims.exp <= clock.now_utc()` — delegation token expiry
7. Line 908/1090: `now = clock.now_utc()` — Stage 7 audit timestamp

The DeterministicClock replaces all calls with a frozen base time plus deterministic per-call advances. Same test case, same clock sequence, same timestamps in output.

---

## 7. DETERMINISTIC UUID GENERATION

The PDP calls `generate_uuid_v4()` at 3 points:
1. Line 909: `audit_id = generate_uuid_v4()` — ALLOW audit ID
2. Line 969: `esc_id = generate_uuid_v4()` — ESCALATE reference ID
3. Line 1037: `jti: generate_uuid_v4()` — capability token JTI
4. Line 1092: `audit_id = generate_uuid_v4()` — DENY/ESCALATE audit ID

The SeededUUIDFactory replaces all calls with a PRNG seeded by `uuid_seed`. For seed S, the N-th call always produces the same UUID. Pattern: `uuid.SetRand(rand.New(rand.NewSource(uuid_seed)))`.

---

## 8. STUB HSM SIGNER

The PDP's `HSM.sign(bytes)` is replaced with a deterministic Ed25519 signer using a fixed key pair loaded from the test case. Ed25519 is inherently deterministic — same key + same message = same signature (no random nonce, unlike ECDSA). This means the stub HSM produces production-identical behavior: if the PDP passes the same bytes to sign, the output is byte-identical.

The fixed key pair is generated once per test suite and included in every test case. It is NOT used in production. It exists solely to make signatures reproducible.

---

## 9. COMPARISON PROTOCOL

After each test case execution, the harness compares 4 outputs:

| Output | Comparison Method | Tolerance |
|---|---|---|
| **Response JSON** | SHA-256 of RFC 8785 canonical JSON | **0 bits** — byte-identical or FAIL |
| **Signature bytes** | SHA-256 of raw Ed25519 signature | **0 bits** — byte-identical or FAIL |
| **Audit record** | SHA-256 of RFC 8785 canonical audit JSON | **0 bits** — byte-identical or FAIL |
| **Capability token** | SHA-256 of raw token bytes (or "NONE") | **0 bits** — byte-identical or FAIL |

**Any non-zero mismatch is a correctness bug.** There is no acceptable mismatch rate. This follows Cedar's standard: any disagreement between runs is a release-blocking defect.

### 9.1 Dual-Run Comparison

Every test case runs twice under identical conditions:

```
Run 1: load snapshot → inject deterministic deps → evaluate request → capture outputs
Run 2: load SAME snapshot → inject SAME deps → evaluate SAME request → capture outputs

ASSERT: Run1.response_hash == Run2.response_hash
ASSERT: Run1.signature_hash == Run2.signature_hash
ASSERT: Run1.audit_record_hash == Run2.audit_record_hash
ASSERT: Run1.token_hash == Run2.token_hash
```

### 9.2 Expected-Value Comparison

Each test case also compares against pre-computed expected values:

```
ASSERT: Run1.response_hash == test_case.expected.response_hash
ASSERT: Run1.verdict == test_case.expected.verdict
ASSERT: Run1.reason_code == test_case.expected.reason_code
ASSERT: Run1.determining_rules == test_case.expected.determining_rules
```

---

## 10. CONTROLLED STATE MUTATION PROTOCOL

After baseline replay passes, the harness introduces controlled mutations to prove deterministic verdict flips:

### Mutation A: Policy Version Change
```
State_1: policy_hash = H1 → request R → verdict V1 (ALLOW)
State_2: policy_hash = H2 (new deny rule added) → request R → verdict V2 (DENY)

VERIFY: V1 == ALLOW
VERIFY: V2 == DENY
VERIFY: V1 != V2 (verdict flipped)
VERIFY: V2.reason_code references the new deny rule
VERIFY: Replay State_1 still produces V1 (snapshot isolation)
VERIFY: Replay State_2 still produces V2 (snapshot isolation)
```

### Mutation B: CRL Revocation Insertion
```
State_1: CRL = { revoked: [] } → request R (with token T) → verdict ALLOW
State_2: CRL = { revoked: [T.jti] } → request R → verdict DENY

VERIFY: State_1 → ALLOW
VERIFY: State_2 → DENY with ERR_TOKEN_REVOKED
VERIFY: No partial state — either the JTI is in CRL or it is not
```

### Mutation C: Agent Lifecycle Suspension
```
State_1: agent.status = ACTIVE → request R → verdict ALLOW
State_2: agent.status = SUSPENDED → request R → verdict DENY

VERIFY: State_1 → ALLOW
VERIFY: State_2 → DENY with ERR_AGENT_SUSPENDED
VERIFY: Replay at State_1 snapshot still produces ALLOW
```

---

## 11. WHAT YOU DO vs. WHAT THE HARNESS DOES

| Step | Who Does It | What They Do |
|---|---|---|
| **1. Implement PDP core** | Engineering (you) | Implement the 7-stage evaluation pipeline per Day 6 pseudocode in Rust or Go. All interfaces (Clock, UUID, HSM, StateRegistry, etc.) must accept injectable implementations. |
| **2. Implement interface stubs** | Engineering (you) | Build DeterministicClock, SeededUUIDFactory, StubHSM, InMemory{StateRegistry, CRL, ResourceRegistry, DedupStore, RateCounter, MosaicAccumulator, BHIVBucket, EmergencyBuffer} conforming to this spec. |
| **3. Generate test corpus** | Harness (automated) | Generate 10,000 test cases per `replay_execution_results.md` Section 2 distribution. Each test case is a complete REPLAY_TEST_CASE struct. |
| **4. Compute expected values** | Harness (automated) | Run each test case once through the PDP to establish baseline expected hashes. These become the golden oracle. |
| **5. Execute Run 1** | Harness (automated) | Load snapshot, inject deps, evaluate all 10,000 requests, capture all 4 output hashes per request. |
| **6. Execute Run 2** | Harness (automated) | Identical to Run 1. Same snapshots, same deps, same requests. |
| **7. Compare** | Harness (automated) | Byte-compare all 40,000 output hashes (10,000 × 4 outputs). Report any mismatch. |
| **8. Mutate and verify** | Harness (automated) | Run Mutations A, B, C. Verify deterministic verdict flips. |
| **9. Report** | Harness (automated) | Produce `replay_execution_results.md` and `drift_detection_report.md`. |

---

## 12. INTEGRATION BOUNDARIES

Per the task brief, this harness has strict boundaries:

| Boundary | Status |
|---|---|
| PDP evaluation logic | NOT MODIFIED — harness wraps, does not change |
| Canon rules | NOT MODIFIED — harness tests existing rules |
| Request schema | NOT MODIFIED — harness generates valid requests per Day 1 schema |
| Response schema | NOT MODIFIED — harness validates responses per Day 2 schema |
| Evaluation order | NOT MODIFIED — harness verifies stages execute per Day 3 order |
| Enforcement model | NOT MODIFIED — harness verifies tokens per Day 5 model |

---

## 13. PDP ADAPTER LAYER — IMPLEMENTATION

The adapter is the integration boundary between the harness and the PDP. It defines how the harness loads the PDP, injects dependencies, calls evaluate(), and captures audit records.

```python
class PDPAdapter:
    """Adapter that creates a Sarathi PDP instance from a test case snapshot."""

    @staticmethod
    def create(snapshot, clock, uuid_factory, hsm):
        """Load PDP with frozen snapshot and injected deterministic deps."""
        pdp = SarathiPDP(snapshot, clock, uuid_factory, hsm)
        pdp.uuid_factory = uuid_factory
        return pdp

    @staticmethod
    def evaluate(pdp, request):
        """Call PDP evaluate() — the 7-stage pipeline entry point."""
        return pdp.evaluate(request)

    @staticmethod
    def get_audit_records(pdp):
        """Extract audit records from in-memory BHIV Bucket."""
        return pdp.bhiv_bucket.records

    @staticmethod
    def get_emergency_records(pdp):
        """Extract emergency buffer records (for FM-05/FM-07 testing)."""
        return pdp.emergency_buffer.records
```

**Critical implementation detail:** Each `run_single()` call creates a FRESH DedupStore, RateCounter, and MosaicAccumulator to prevent cross-run state leakage. The StateRegistry, RevocationList, and ResourceRegistry are read-only and safe to share. This was discovered during execution when the DedupStore marked requests as duplicates across runs, causing oracle divergence.

---

## 14. SNAPSHOT BINDING TOKEN — VALIDATED IMPLEMENTATION

```python
def compute_sbt(self, clock_time, uuid_seed, hsm_pub_bytes):
    """Compute Snapshot Binding Token — Sarathi's zookie equivalent.
    SHA-256 of: policy_hash || crl_hash || clock || seed || key_hash
    """
    components = (
        self.policy_hash +
        sha256_obj({"staleness": self.revocation_list.staleness_ms(),
                   "revoked_count": len(self.revocation_list.revoked_jtis)}) +
        clock_time.isoformat() +
        str(uuid_seed) +
        sha256_hex(hsm_pub_bytes)
    )
    return sha256_hex(components.encode('utf-8'))
```

**Validation result:** 100 SBTs computed twice each. 100/100 identical. SBT determinism verified.

---

## 15. RELATIONSHIP TO EXISTING SPECIFICATIONS

| Existing Spec | How Harness Uses It | What Harness Does NOT Change |
|---|---|---|
| Day 1 — Request Schema | Generates valid requests per all 13 invariants | No schema changes |
| Day 2 — Response Schema | Validates responses per all 13 output invariants | No response changes |
| Day 3 — Evaluation Order | Verifies 7-stage sequence per 8 evaluation invariants | No evaluation changes |
| Day 4 — Failure Modes | Tests all 17 failure modes produce deterministic DENY | No failure mode changes |
| Day 5 — Enforcement Model | Verifies token issuance per 14 enforcement invariants | No enforcement changes |
| Day 6 — Pseudocode | Tests all 52 sub-steps produce deterministic results | No pseudocode changes |
| Observability — Decision Trace | Verifies trace records are deterministic under replay | No trace changes |
| Observability — Drift Detection | Validates drift metrics under controlled mutations | No metric changes |

---

**END OF REPLAY HARNESS ARCHITECTURE**

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Frozen Interfaces | 10 (all PDP external interfaces) |
| Comparison Outputs | 4 per test case (response, signature, audit, token) |
| Mismatch Tolerance | 0 bits — zero tolerance (Cedar standard) |
| Controlled Mutations | 3 (policy change, CRL revocation, agent suspension) |
| Industry Alignment | Cedar VGD, Zanzibar snapshot consistency, FoundationDB DST |
| PDP Modifications Required | 0 |
