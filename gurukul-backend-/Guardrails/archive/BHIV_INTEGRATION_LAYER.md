# BHIV Integration Layer (Corrected)

## SYSTEM CONTEXT & FAILURES ADDRESSED
The ecosystem currently fails determinism and integration audits due to:
1. unstructured ingress (Gurukul Backend)
2. dynamically generated fields (Workflow Service)
3. missing schema wrappers (Review AI)
4. schema drift (missing truth_classification)
5. environment-based routing divergence during replay
6. unversioned/unenforced contracts

This corrected document outlines a purely **Non-Invasive Integration Layer**. It enforces absolutely zero authority, modifies zero payloads, and limits its actions strictly to observation, validation logging, and discrepancy classification.

────────────────────────────────

## SECTION 1 — Authority Behavior Removal

**Zero Enforcement Proxy Model:**
*   Sidecar proxies attached to each node act exclusively as **Passive Validation Observers**.
*   No proxy halts, blocks, or rejects any HTTP/RPC request.
*   If a system submits a malformed, unstructured, or unversioned payload, the proxy allows the traffic to flow through completely unimpeded.
*   The proxy simultaneously emits an out-of-band `SCHEMA_VIOLATION_LOG` to the centralized message bus for PRANA's ingestion.

────────────────────────────────

## SECTION 2 — Payload Modification Removal

**Annotation Wrapper Model:**
*   Original payloads remain 100% untouched. No UUIDs are stripped, no timestamps are overwritten, and no missing fields are injected.
*   The Observer Sidecar wraps the original transmission in a non-destructive annotation envelope for auditing purposes to the message bus:

```json
{
  "original_payload": { ... }, 
  "validation_metadata": {
    "schema_valid": false,
    "registry_reference_present": false,
    "truth_classification_present": false,
    "observed_dynamic_fields": ["route_id", "updated_at"]
  }
}
```

────────────────────────────────

## SECTION 3 — Deterministic Comparison Strategy

**Masked Hash Auditing:**
*   Instead of forging determinism by stripping payloads at the egress proxy, PRANA computes deterministic hashes *after the fact*.
*   When PRANA consumes the `validation_metadata` and the `original_payload`, its internal comparison engine dynamically masks known volatile fields (like live timestamps or UUIDs) in memory.
*   PRANA calculates the hash on the remaining logic block. The original system values remain intact and unmodified on their original routing path.

────────────────────────────────

## SECTION 4 — Contract Discipline (Non-Enforcing)

**Validation Without Friction:**
*   Contracts define the ideal state, but systems remain free-running and loosely typed if they choose.
*   When a node fails to adhere to strict schema boundaries, the Observer Sidecar logs the `contract_version_mismatch` or `schema_violation`.
*   The ecosystem's "health" is measured by the volume of these violations rather than enforcing health by shutting down non-compliant pathways.

────────────────────────────────

## SECTION 5 — Registry Alignment (Passive)

**Passive Registration Checks:**
*   The Observer Sidecars cache the Immutable Canonical Registry.
*   If a payload contains a `registry_reference`, the sidecar flags `registry_match: true` or `false`.
*   If the reference is missing entirely (e.g., from Review AI), the sidecar flags `registry_reference_missing: true`. It does *not* inject a default reference.

────────────────────────────────

## SECTION 6 — Replay Strategy (Non-Invasive)

**Divergence Documentation over Isolation:**
*   Replays are executed dynamically against live environments using the exact recorded historical inputs.
*   No time overrides or `LD_PRELOAD` injections are permitted. No routing mock layers are deployed.
*   Because Gurukul and Workflow rely on active environments, the replay will inherently fracture from historical traces (e.g., routing to different live queues or generating new timestamps).
*   PRANA simply logs this divergence natively: `"historical_hash": "A", "replay_hash": "B", "divergence_reason": "Live routing state mismatch"`. PRANA detects the non-determinism; it does not forcefully prevent it.

────────────────────────────────

## SECTION 7 — Updated Integration Architecture

*   **Observers (Sidecars):** Deployed adjacently to all active nodes (`sys_gurukul_01`, `sys_workflow_01`, etc.). They sniff ingress and egress traffic natively.
*   **Zero Transformation:** They read the packet, validate it against the cached registry, and forward the untouched packet to the application.
*   **Telemetry Bus:** They fire their calculated `validation_metadata` and the raw payload copy asynchronously to the PRANA telemetry bus.
*   **PRANA Vernier:** PRANA consumes the telemetry bus, compares historical runs to replay runs, computes masked hashes internally, and produces integrity audits without ever communicating back to the host systems.

────────────────────────────────

## FINAL QUESTION

"After correction, do BHIV systems interoperate through strict contracts and canonical registry alignment while preserving deterministic replay?"

**Answer: NO**

**Explanation:**
The systems still fail deterministic replay because we adhered strictly to the non-invasive constraints. 

Because we cannot modify internal system logic, block unstructured payloads at the proxy, or hack the environment with time-overrides and mocked routing isolated queues, the systems perfectly retain all their original flaws. Gurukul still computes dynamic metadata, and Workflow still routes based on live load-balancers. 

The integration design is corrected and operates flawlessly as a non-invasive, purely observant telemetry layer. PRANA now accurately observes, validates, maps to the registry, and reports exactly *why* the ecosystem fails. However, you cannot preserve deterministic replay or enforce strict contracts in a loosely-typed, environmentally coupled ecosystem without modifying the systems themselves or actively intercepting and altering the traffic. The integration layer proves the lack of determinism, but logically cannot fix it under these zero-authority constraints.
