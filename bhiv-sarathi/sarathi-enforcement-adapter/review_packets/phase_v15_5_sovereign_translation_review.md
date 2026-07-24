# Phase v15.5 — Sovereign Translational Layer Review Packet

**Date:** 2026-05-07
**Author:** Hemanth B (Sarathi enforcement adapter owner)
**Reviewer scope:** changes since v15.4 (ngrok deployment closure)
**Status:** built clean (`go build`), `go vet ./...` clean, all unit tests pass.

This packet is **additive** to v14.6–v15.4. None of the prior closures are
revisited. The full bundle of new files and modification spots is enumerated
below; reviewers can replay every change directly.

---

## 1. Why this phase exists

The BHIV Core team (Raj) shipped a `/sovereign/decide` response with 6 fields:
`{trace_id, decision, decision_hash, policy_reference, input_hash, timestamp}`.
Sarathi's existing `/v1/ingest-decision` expects a 16-field signed
`ExternalDecision`. Earlier guidance (v15.2 `ENDPOINTS_FOR_BHIV.md` §5) asked
the Sovereign team to either sign an `ExternalDecision` or downgrade to
`/v1/enforce`. Both options put the integration cost on the Sovereign team
and prevented native BHIV-shape ingestion.

v15.5 inverts the contract:

- Sarathi accepts the **9-field SovereignDecideResponse natively** at
  `/sarathi/enforce` (the team's existing 6 fields plus 3 auth fields:
  `api_key`, `ed25519_signature`, `evaluator_id`).
- Sarathi computes the **7 remaining ExternalDecision fields locally** from
  those 9 inputs, deterministically.
- `/v1/ingest-decision` stays live as a **self-test path** so the user can
  inject signed canonical decisions to isolate Sarathi-side bugs.
- `trace_id` becomes the upstream Core API's property — Sarathi no longer
  mints a fallback locally when running in production
  (`SARATHI_TRACE_ID_REQUIRE_INBOUND=true`).
- Bucket and InsightFlow fan-out swap raw canonical bytes for BHIV-shaped
  envelopes (`BucketArtifact` v1.0, four InsightFlow shapes A/B/C/D), with a
  durable `parent_hash` chain per `trace_id`.

---

## 2. New files (10)

| File | Responsibility |
|---|---|
| [translation_sovereign_schemas.go](../translation_sovereign_schemas.go) | Wire structs: `SovereignDecideResponse`, `BucketArtifact`, `InsightFlowSchema A/B/C/D`. Schema-version constants. `BucketArtifactGenesisHash`. |
| [translation_canonical.go](../translation_canonical.go) | Helpers: `CanonicalHashOfStruct`, `ComputePayloadHashHex`, hop counter store, atomic file writer, snapshot api_key fingerprint lookup. |
| [translation_bucket_chain.go](../translation_bucket_chain.go) | `ParentHashStore` — flock-protected per-trace chain at `live/translation/parent_chain/{trace_id}.json`. |
| [translation_sovereign_to_sarathi.go](../translation_sovereign_to_sarathi.go) | `TranslateSovereignToSarathi` — 9 → 16 field map. `VerifySovereignSignature`. Audit row at `proof_logs/translation_map.jsonl`. |
| [translation_bucket_artifact.go](../translation_bucket_artifact.go) | `BuildBucketArtifact` — assembles BHIV BucketArtifact + advances chain atomically. |
| [translation_insightflow.go](../translation_insightflow.go) | Four builders: `BuildSchemaATrigger`, `BuildSchemaBPersist`, `BuildSchemaCExecute`, `BuildSchemaDProcess`. |
| [translation_insightflow_router.go](../translation_insightflow_router.go) | `RouteInsightFlowFanout` — fans out 4 shape-specific bodies to InsightFlow. |
| [translation_bhiv_fanout.go](../translation_bhiv_fanout.go) | `BHIVTranslatedFanOut` — orchestrates Bucket post + InsightFlow fan-out for production callers. |
| [service_boundary_sovereign.go](../service_boundary_sovereign.go) | New HTTP handler `handleSarathiEnforceSovereign`. 5-stage gate: method/CT → API-key → strict parse → trace_id check → fingerprint → signature → translation → re-issue to `handleIngestDecision`. |
| [cmd_sovereign_keygen.go](../cmd_sovereign_keygen.go) | `--bootstrap-sovereign-core` and `--verify-bucket-chain` CLI subcommands. |
| [translation_sovereign_to_sarathi_test.go](../translation_sovereign_to_sarathi_test.go) | Unit tests: happy path, determinism, missing trace_id, wrong evaluator, malformed signature, action mapping, decision_id stability. |
| [translation_bucket_chain_test.go](../translation_bucket_chain_test.go) | Unit tests: genesis on first lookup, append advances chain, atomic LookupAndAppend, current tip, distinct traces independent. |

## 3. Modified files (7)

| File | Change |
|---|---|
| [service_boundary.go](../service_boundary.go) | Re-mount `/sarathi/enforce` to `handleSarathiEnforceSovereign`. Parse inbound `X-Sarathi-Trace-ID` header on `/v1/ingest-decision`; pass it to `PDPAdapter.Ingest` as the trace context (formerly `nil`). Add `strings` import. |
| [service_inbound_auth.go](../service_inbound_auth.go) | Add `/sarathi/enforce` to `ProtectedPaths` defaults (both `DefaultInboundAuthConfig` and the construction-time fallback). |
| [pdp_adapter.go](../pdp_adapter.go) | Fail-closed when `traceCtx == nil` after `NewTraceContext()` (which now returns `nil` under `SARATHI_TRACE_ID_REQUIRE_INBOUND=true`). |
| [propagation_envelope.go](../propagation_envelope.go) | Same fail-closed pattern in `SealPropagationEnvelope`. |
| [sovereign_governance_v9.go](../sovereign_governance_v9.go) | `NewTraceContext()` returns `nil` when `SARATHI_TRACE_ID_REQUIRE_INBOUND=true`. New `MakeTraceContextFromInbound(traceID)` constructs a context preserving the inbound trace_id verbatim. |
| [external_decision.go](../external_decision.go) | Add `APIKeyFingerprint string` to `EvaluatorTrustSnapshot`. Optional field; legacy snapshots tolerate empty. |
| [evaluator_admin_cli.go](../evaluator_admin_cli.go) | Dispatch `--bootstrap-sovereign-core` and `--verify-bucket-chain`. |

## 4. Verification — built clean

```
$ go build -o sarathi.exe .
$ echo $?
0

$ go vet ./...
$ echo $?
0

$ go test -run "TestTranslateSovereignToSarathi|TestParentHashStore" -count=1 -timeout 60s .
ok      sarathi-enforcement-adapter     2.769s

$ go test -count=1 -timeout 180s .
ok      sarathi-enforcement-adapter     2.912s
```

No prior tests broke; new tests cover the translator's deterministic
behaviour and the parent_hash chain primitives.

## 5. Operator cheat-sheet

```bash
# Bootstrap sovereign BHIV core (forward private key + raw API key to Core team)
./sarathi --bootstrap-sovereign-core \
    --keys-out-dir=./live/keys/sovereign_bhiv_core \
    --evaluator-id=sovereign_bhiv_core \
    --metadata='{"name":"Sovereign BHIV Core","org":"BHIV"}' \
    --snapshot=./live/trust_snapshot.json \
    --print-private-key

# Bootstrap self-test evaluator
./sarathi --bootstrap-sovereign-core \
    --keys-out-dir=./live/keys/self_test \
    --evaluator-id=self_test \
    --metadata='{"name":"Self-Test","purpose":"diagnostic"}' \
    --snapshot=./live/trust_snapshot.json \
    --print-private-key

# Production runtime
SARATHI_INBOUND_AUTH_MODE=required \
SARATHI_TRACE_ID_REQUIRE_INBOUND=true \
SARATHI_INBOUND_ISSUER_PUB_KEY_FILE=./live/keys/sovereign_bhiv_core/issuer-pub.hex \
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json \
  ./sarathi --service --port=9002

# Verify Bucket chain
./sarathi --verify-bucket-chain --trace-id=<traceID>
```

## 6. What did NOT change

- The 5-stage external decision pipeline (registry → signature → integrity →
  expiry → replay) in [external_decision.go](../external_decision.go) is
  untouched.
- `/v1/ingest-decision` continues to accept canonical `ExternalDecision`
  bodies. The user can sign locally and POST to isolate Sarathi-side bugs.
- The legacy `MultiSystemRouter.RoutePropagation()` still runs canonical-byte
  fan-out for in-process simulators and live-integration tests. Production
  callers opt into `BHIVTranslatedFanOut` when pointing at real BHIV peers.
- The Ed25519 keygen, evaluator register/suspend/revoke/rotate primitives
  retain their existing flags. `--bootstrap-sovereign-core` is a composite
  on top of them; nothing is removed.

## 7. Open questions to ask the BHIV teams

**Sovereign Core (Raj):** Confirm Sovereign signs `decision_hash` (NOT
`decision_core_hash`) with Ed25519 over the raw hex string bytes. Sarathi's
verifier in `VerifySovereignSignature` uses
`ed25519.Verify(pub, []byte(decisionHashHex), sigBytes)`.

**Bucket (Siddhesh):** the team supplied two hashes during the v15.4 dry
run — `f54aac4...` and `642a0ce...`. v15.5 treats the first as the
`tip_hash` for an existing trace and ignores the second pending
clarification. Three questions to resolve before next live test:

1. Is the chain seeded with a genesis hash, and if so, what is its sentinel
   string?
2. Is the second hash a chain anchor, a content-hash, or a tenant identifier?
3. What error code do you return when `parent_hash` does not match your
   stored `tip_hash`, and how do I read your current `tip_hash` for a
   `trace_id`?

**InsightFlow (Vijay):** confirm the Schema A/B/C/D mapping in v15.5 §6.4
matches the dashboard expectations. If `bucket_persist` should carry Schema D
instead of B (and `insightflow_process` carry Schema B), the mapping table is
a one-line swap in `RouteInsightFlowFanout`.
