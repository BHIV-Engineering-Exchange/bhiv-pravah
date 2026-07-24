# DECISION TRACE SPECIFICATION

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Policy Decision Point
**Version:** 1.0.0

---

## 1. PURPOSE

Every Sarathi PDP decision emits an immutable, hash-chained decision trace. The trace is the governance flight recorder. If it breaks, governance is blind. An untraced decision is an ungoverned decision.

Aligns with: Day 7 lock guarantee G-05 (Mandatory Audit), Day 2 OUT-07 (Audit-Coupled), Day 3 EVAL-05 (Stage 7 never skipped), observability decision_trace_spec.md (DT-01 through DT-10).

---

## 2. TRACE SCHEMA

```json
{
  "decision_id":        "string — UUIDv5 deterministic from request content",
  "policy_hash":        "string — SHA-256 of Authority Matrix rules",
  "policy_version":     "string — semantic version (1.0.0)",
  "request_hash":       "string — SHA-256 of canonical request JSON",
  "verdict":            "string — ALLOW or DENY",
  "determining_rules":  ["string — rule IDs"],
  "truth_classification": "string — resource truth level (L0-L4)",
  "reason":             "string — machine-readable reason code",
  "timestamp":          "string — ISO-8601 UTC",
  "agent_id":           "string — requesting agent identifier",
  "resource_id":        "string — target resource identifier",
  "action":             "string — requested action",
  "prev_trace_hash":    "string — SHA-256 of previous trace (hash chain)",
  "trace_hash":         "string — SHA-256 of this trace"
}
```

---

## 3. MANDATORY FIELDS

Every decision trace MUST contain these fields. No field may be null or absent.

| Field | Source | Purpose |
|---|---|---|
| `decision_id` | PDP Stage 5 | Unique identifier for this decision |
| `policy_hash` | PolicyStore | Anchors decision to exact policy version |
| `policy_version` | PolicyStore | Human-readable policy version |
| `request_hash` | SHA-256 of request | Fingerprint of input (without logging raw request) |
| `verdict` | PDP Stage 4 | The authority decision |
| `determining_rules` | PDP Stage 4 | Which rules produced the verdict |
| `truth_classification` | Registry | Resource's truth level |
| `reason` | PDP Stages 1-4 | Machine-readable reason code |
| `timestamp` | System clock | When the decision was rendered |
| `agent_id` | Request | Who requested (for audit correlation) |
| `resource_id` | Request | What was targeted |
| `action` | Request | What was requested |
| `prev_trace_hash` | Trace chain | Link to previous trace (tamper detection) |
| `trace_hash` | SHA-256 of this trace | This trace's fingerprint |

---

## 4. HASH CHAIN INTEGRITY

Traces are linked in a chain where each trace includes the hash of the previous trace:

```
GENESIS → trace_1 → trace_2 → trace_3 → ...
           │          │          │
           └─ prev_trace_hash = "GENESIS"
                      └─ prev_trace_hash = SHA-256(trace_1)
                                 └─ prev_trace_hash = SHA-256(trace_2)
```

**Hash computation:** `trace_hash = SHA-256(canonical_json(trace_without_trace_hash))`

The `trace_hash` is computed AFTER all other fields are set, then appended. The `prev_trace_hash` is the `trace_hash` of the immediately preceding trace. The first trace in the chain uses `"GENESIS"` as its `prev_trace_hash`.

**Tamper detection:** If any trace is modified, its `trace_hash` changes, which breaks the `prev_trace_hash` link of the next trace. Detection is O(1) per trace.

Aligns with: Observability decision_trace_spec.md DT-04 (Ordering), lock guarantee G-05, PDP Interface 4-layer immutability architecture.

---

## 5. TRACE EMISSION RULES

| Rule | Description |
|---|---|
| **Every verdict produces a trace** | ALLOW and DENY both produce traces. No verdict is untraced. |
| **Trace emission cannot be skipped** | Stage 5 always executes (EVAL-05). Even if earlier stages short-circuit, the trace is emitted. |
| **Traces are append-only** | Once written, a trace is never modified or deleted. |
| **Traces must be written before response delivery** | The decision is not returned to the caller until the trace is persisted. If trace write fails, the verdict is overridden to DENY (OUT-07). |
| **No raw PII in traces** | Agent IDs and resource IDs are logged as-is (they are system identifiers, not personal data). Raw request bodies are NOT logged — only `request_hash`. |

---

## 6. TRACE FILE FORMAT

Traces are emitted to `decision_trace.json` as a JSON array:

```json
[
  { "decision_id": "...", "policy_hash": "...", ... "trace_hash": "..." },
  { "decision_id": "...", "policy_hash": "...", ... "trace_hash": "..." }
]
```

In production, traces are written to the BHIV Bucket (append-only, WORM-protected). For this implementation, the local JSON file serves as the trace store.

---

## 7. RELATIONSHIP TO EXISTING SPECIFICATIONS

| Specification | How This Aligns |
|---|---|
| Day 2 — Response Schema OUT-07 | Audit-coupled: every response has a corresponding trace |
| Day 3 — Evaluation Order EVAL-05 | Stage 5 (audit) never skipped |
| Day 4 — Failure Mode FM-05 | If trace write fails, verdict overridden to DENY |
| Day 7 — Lock G-05 | Mandatory audit guarantee |
| Observability — Decision Trace Spec | DT-01 (Completeness), DT-03 (Immutability), DT-04 (Ordering) |
| Observability — Audit Reconstruction | Hash chain enables forensic reconstruction |
| Task — Non-negotiable rules | "All decisions must be reproducible under replay" |

---

## 8. EXAMPLE TRACE ENTRY

```json
{
  "decision_id": "344ef3ec-ebc0-55d8-b4ac-5ac6293f10a9",
  "policy_hash": "cb6dac30c16456a2898bbcf30533b11170f2f6902449ce7daa9708b4b195ceb1",
  "policy_version": "1.0.0",
  "request_hash": "53d5aa78850826638155c89499b8109a0ce6877ce50d5e4b74f91bcdff031539",
  "verdict": "ALLOW",
  "determining_rules": ["AUTH-001"],
  "truth_classification": "L4",
  "reason": "EXPLICIT_ALLOW",
  "timestamp": "2026-03-07T03:45:13.547208Z",
  "agent_id": "gov-agent-001",
  "resource_id": "policy-reg-001",
  "action": "read",
  "prev_trace_hash": "GENESIS",
  "trace_hash": "a1b2c3d4e5f6..."
}
```

---

**END OF DECISION TRACE SPECIFICATION**
