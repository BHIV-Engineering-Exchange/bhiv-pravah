# ROLE

Date: 2026-06-17  
Status: CANONICAL

---

## What Bucket Is

Bucket is the **BHIV append-only evidence substrate**. It:

- Accepts validated artifact envelopes from approved producers
- Computes server-authoritative SHA256 hashes deterministically
- Stores artifacts immutably in a tamper-evident hash chain
- Preserves `trace_id` and lineage (`parent_hash`) without interpreting payload semantics
- Supports deterministic replay and read-back verification
- Exposes read paths for observability consumers (InsightFlow, Core, operators)

---

## What Bucket Is Not

Bucket is **not**:

| Role | Bucket does NOT |
|------|-----------------|
| Orchestrator | Coordinate workflows, schedule tasks, or manage cross-system control flows |
| Intelligence engine | Interpret payloads, make decisions, or apply business logic |
| Execution authority | Execute, authorize, or trigger actions in other systems |
| Governance authority | Approve namespaces, ratify contracts, or validate producer semantics |
| Transformation layer | Modify, enrich, or normalize producer payloads |

---

## Participation Model

```
SVACS  ──write──► Bucket ◄──write── NICAI
                    ▲
Core   ──write──────┘
                    │
InsightFlow ──read──┘ (observe only)
```

Bucket sits at the center as **memory / truth anchor**. Producers write. Consumers read. Bucket stores.

---

## Guarantees

1. **Immutability** — artifacts are never modified or deleted by normal operations
2. **Deterministic hashing** — canonical JSON serialization yields reproducible SHA256
3. **Lineage integrity** — each artifact links to the current chain head via `parent_hash`
4. **Trace preservation** — `trace_id` stored exactly as provided
5. **Replayability** — append-only log reconstructs full chain state

---

## Non-Goals

- Product-specific payload validation (owned by producers)
- Cross-product orchestration (owned by Core)
- Real-time analytics (owned by InsightFlow)
- Distributed consensus / blockchain behavior

---

## Responsible Parties

| Role | Owner |
|------|-------|
| Contract authority | Raj Prajapati (BHIV Core) |
| Testing & validation | Vinayak Tiwari |
| InsightFlow observability | Nupur (InsightFlow Team) |
| SVACS producer | SVACS Team |
| NICAI producer | NICAI Team |
| Bucket custody | Bucket custodian (operations) |

---

## One-Line Truth

**Bucket is append-only evidence storage with deterministic replay — nothing more.**

*End of ROLE.md*
