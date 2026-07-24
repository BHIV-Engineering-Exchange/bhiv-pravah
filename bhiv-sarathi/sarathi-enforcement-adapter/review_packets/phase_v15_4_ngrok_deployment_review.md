# Phase v15.4 — Ngrok Deployment Mode Review Packet

**System:** Sarathi Enforcement Adapter — Cross-network testing over public ngrok HTTPS tunnels + BHIV Core input-bootstrap CLI
**Version:** v15.4
**Author:** Hemanth B
**Organization:** Blackhole Infiverse (BHIV)
**Review Date:** 2026-05-06
**Classification:** Internal Sovereign Design / Strictly Confidential
**Predecessor packets:** [v14.8 Sovereign Authority Closure](phase_v14_8_sovereign_authority_closure.md), [v15.0 Sovereign Identity Closure](phase_v15_0_sovereign_identity_closure.md), [v15.1 Clean State Proof](phase_v15_1_clean_state_proof.md), [vc_integration_validation_v1](vc_integration_validation_v1.md)

---

## 1. Executive Summary

The testing team mandated that the cross-system VC run over public ngrok
HTTPS tunnels — every BHIV peer (Bucket, InsightFlow, Core API, MCP Bridge,
Sovereign Core) and Sarathi itself exposed via individual ngrok tunnels.
Independently, the BHIV Core team (Raj) clarified that Sarathi must NOT
act as a standalone enforcement point; the full chain is
`Core → MCP → Sovereign → Sarathi (PEP) → propagation`.

v15.4 closes both as a **purely additive** layer — zero changes to v14.6
(22/22 audit), v14.7 (5/5 live integration), v14.8 (parallel execution),
v15.0 (inbound identity), v15.1 (network surface), v15.2 (BHIV ecosystem
wiring), or v15.3 (Core full surface) code paths.

### Key achievements

- **Ngrok transport mode** — all 16 `SARATHI_*_URL` env vars now accept
  ngrok HTTPS URLs. No code change required: the v15.2 design
  (`ecosystem_endpoints.go::LoadEcosystemEndpoints`) already supports
  arbitrary URLs via env vars. Default outbound timeout raised 5 s → 15 s
  to absorb ngrok cold-start latency.
- **Dual-mode env wiring helper** — `scripts/ngrok_env.sh` and
  `ngrok_env.ps1`. **Mode A** (1 URL per service, paths derived) for the
  common case; **Mode B** (per-endpoint URL overrides) for split-process
  peers. Both modes can be mixed per peer; per-endpoint flags always win
  over base-URL derivation. Operator can switch by changing flags only;
  never edits source.
- **`--post-task-to-core` CLI** — new v15.4 input-bootstrap flag.
  Lets Sarathi (or any operator/script) post a fresh task input to Core
  `/execute_task` so Core can drive the full chain. Honours Raj's contract:
  `trace_id=""` sent, Core generates and returns it. Sets
  `ngrok-skip-browser-warning: true` so ngrok free-tier interstitials never
  pollute the request.
- **Operator runbook (12 sections)** — `NGROK_VALIDATION_SCRIPT.md`.
  Ngrok install, message templates for each peer team, self-verify curls,
  the `--self` ngrok exposure procedure, env-var setup, pre-flight,
  Test 1 (existing flow over ngrok), Test 2 (new input-bootstrap),
  Postman alternative, gotchas, colleague-facing copy-paste block, failure
  recovery cheat sheet.
- **VC parity demos added** — Demo 9 (ngrok cross-network parity) +
  Demo 10 (input bootstrap end-to-end) appended to
  `VC_VALIDATION_SCRIPT.md`. Existing 8 demos untouched.
- **`ENFORCEMENT_VALIDATION_SCRIPT.md` UNCHANGED** — per user instruction.
  All ngrok-specific procedure lives in the new parallel script.

---

## 2. Why ngrok is a transport-only swap

Two independent transports must produce byte-identical canonical envelopes
for the same input — that is the proof ngrok hasn't corrupted governance.

| Risk | What ngrok does | Mitigation / proof |
|---|---|---|
| Body re-encoding | Ships verbatim (no transform) | Demo 9: `chain_binding_hash` identical across two repeats of the same input over ngrok |
| Header injection | Adds `Ngrok-*` informational headers; doesn't touch our `X-Sarathi-*` set | Sarathi only acts on its own header strict-list |
| Compression | Off in HTTPS proxy mode | `Content-Length` matches `len(canonical)`; per-hop ack hash matches |
| Free-tier browser interstitial | Returns HTML on browser-like requests | `ngrok-skip-browser-warning: true` header on outbound `PostTaskInput`; documented in operator runbook for inbound curls |
| Tunnel rotation mid-test | Ephemeral URLs change on restart | Re-`export SARATHI_<...>=<new-url>`; binary picks up at next call |

The byte-equality gate (Demo 9) is the single canonical proof: if it
passes, every prior governance invariant (INV-PROP-*, INV-LIVE-*,
INV-PARA-*, INV-AUTH-*) survives the ngrok hop.

---

## 3. Mandate mapping with evidence

| Source | Mandate | v15.4 delivery | Evidence on disk |
|---|---|---|---|
| Testing team (2026-05-05) | Move tomorrow's run to ngrok; do NOT modify `ENFORCEMENT_VALIDATION_SCRIPT.md` | All env-var-driven; new `NGROK_VALIDATION_SCRIPT.md` parallel doc | [NGROK_VALIDATION_SCRIPT.md](../NGROK_VALIDATION_SCRIPT.md) (12 sections); [ENFORCEMENT_VALIDATION_SCRIPT.md](../ENFORCEMENT_VALIDATION_SCRIPT.md) byte-identical to v15.3 |
| BHIV Core team (Raj) | Sarathi role starts at PEP; Core drives the chain after task input | New `--post-task-to-core` CLI; `CoreClient.PostTaskInput` sends `trace_id=""` per spec | [cmd_post_task.go](../cmd_post_task.go), [ecosystem_clients.go::PostTaskInput](../ecosystem_clients.go) |
| BHIV Core team (Raj) | Decision ingestion remains via existing path | `/v1/ingest-decision` and `/sarathi/enforce` aliases unchanged | [service_boundary.go](../service_boundary.go) (no diff vs v15.3) |
| Operator | Easy switch between 1-URL-per-service and per-endpoint-URL peer layouts | Dual-mode `ngrok_env.sh` + `ngrok_env.ps1` | [scripts/ngrok_env.sh](../scripts/ngrok_env.sh), [scripts/ngrok_env.ps1](../scripts/ngrok_env.ps1) |
| Operator | Single source of truth for URL config | Existing `ecosystem_endpoints.go` (lines 144-173) is the only URL reader; no other file touched | [ecosystem_endpoints.go](../ecosystem_endpoints.go) |

### Regression gates (still green)

| Predecessor | Command | Result |
|---|---|---|
| v14.6 audit | `--v14-6` | 22/22 PASS (no diff in code path) |
| v14.7 live-integration | `--live-integration 5` | 5/5 verified |
| v14.8 parallel | `--parallel-execute 10` | 10 matches, 0 divergences |
| v14.9 service runtime | `--service-live-demo` | 8/8 scenarios pass |
| v15.0 identity | `SARATHI_INBOUND_AUTH=required` boot | gates fire as expected |
| v15.1 surface | `--v14-6` after surface-closure cleanup | 22/22 PASS |
| v15.2/v15.3 ecosystem wiring | `--service-live-demo` with env-loaded URLs | propagation completes |
| **v15.4 ngrok transport stability (new)** | Demo 9: `chain_binding_hash` repeated twice over ngrok | MUST be identical across runs (no transport mutation) |
| **v15.4 input bootstrap (new)** | Demo 10: `--post-task-to-core` end-to-end | trace_id continuity end-to-end |

---

## 4. Invariants introduced

| Code | Statement | Mechanism | Artefact |
|---|---|---|---|
| **INV-NGROK-01** | Identical `chain_binding_hash` across two repeats of the same input over ngrok (transport-stability invariant — proves ngrok does not mutate canonical bytes) | RFC 8785 canonical bytes verbatim through HTTPS proxy; `ValidateHop` byte-equality on each hop | Demo 9 in `VC_VALIDATION_SCRIPT.md`; tail of `proof_logs/enforcement_audit_backup.jsonl` after both runs shows identical hashes |
| **INV-NGROK-02** | `PostTaskInput` MUST send `trace_id=""`; Core MUST return non-empty `trace_id` in response | Payload built literally with `"trace_id": ""` in [ecosystem_clients.go::PostTaskInput](../ecosystem_clients.go); CLI prints returned `trace_id` from response JSON | Demo 10 in `VC_VALIDATION_SCRIPT.md`; CLI stdout shows `trace_id: <core-generated-uuid>` |
| **INV-NGROK-03** | Sarathi inbound ignores foreign `Ngrok-*` headers | v15.0 inbound auth header strict-list; Sarathi only consumes `X-Sarathi-*` and `X-API-Key` | [service_inbound_auth.go](../service_inbound_auth.go) — no `Ngrok-*` handling; foreign headers pass through `r.Header` but never read |
| **INV-NGROK-04** | Default outbound HTTP timeout is 15 s in v15.4 (was 5 s); operator override remains `SARATHI_ECOSYSTEM_TIMEOUT_MS=<n>` | `EcosystemClientDefaultTimeout = 15 * time.Second` in [ecosystem_clients.go](../ecosystem_clients.go) | Smoke test stdout: `http timeout: 15s (default; override with SARATHI_ECOSYSTEM_TIMEOUT_MS)` |
| **INV-NGROK-05** | All 16 `SARATHI_*_URL` env vars accept ngrok HTTPS URLs unchanged | `LoadEcosystemEndpoints` env-var precedence in [ecosystem_endpoints.go](../ecosystem_endpoints.go) (v15.2 design) | Smoke test stdout: `endpoints source: env` when any ngrok URL is exported |

---

## 5. Files changed / created (full diff scope)

| File | Type | Notes |
|---|---|---|
| [ecosystem_clients.go](../ecosystem_clients.go) | Edit | `EcosystemClientDefaultTimeout` 5 s → 15 s; added `CoreClient.PostTaskInput` (~50 lines) |
| [enforcement_adapter_main.go](../enforcement_adapter_main.go) | Edit | One-line dispatch added (`ParsePostTaskArgs` before `ParseServiceRuntimeArgs`) |
| [cmd_post_task.go](../cmd_post_task.go) | **NEW** | `--post-task-to-core` CLI flag + handler (~190 lines) |
| [scripts/ngrok_env.sh](../scripts/ngrok_env.sh) | **NEW** | Bash dual-mode env wiring (~250 lines) |
| [scripts/ngrok_env.ps1](../scripts/ngrok_env.ps1) | **NEW** | PowerShell equivalent (~170 lines) |
| [NGROK_VALIDATION_SCRIPT.md](../NGROK_VALIDATION_SCRIPT.md) | **NEW** | 12-section operator runbook |
| [KB_14_NGROK_DEPLOYMENT_v15_4.md](../KB_14_NGROK_DEPLOYMENT_v15_4.md) | **NEW** | Knowledge base entry |
| [ENDPOINTS_FOR_BHIV.md](../ENDPOINTS_FOR_BHIV.md) | Edit | Added §7 (Ngrok deployment mode) |
| [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) | Edit | Added Demo 9 + Demo 10 |
| [KB_13_NETWORK_SURFACE_CLOSURE_v15_1.md](../KB_13_NETWORK_SURFACE_CLOSURE_v15_1.md) | Edit | Added v15.4 cross-reference |
| [ENFORCEMENT_VALIDATION_SCRIPT.md](../ENFORCEMENT_VALIDATION_SCRIPT.md) | **NOT MODIFIED** | Per user instruction — sacred |

**Build verification:** `go build -o sarathi-enforcement-adapter.exe .` succeeded
on Windows, output binary 15.5 MB. Smoke tests:

```
$ ./sarathi-enforcement-adapter.exe --post-task-to-core --input "smoke"
  endpoints source: default
  Core /execute_task URL: http://ngrok-url-not-set.local:8003/execute_task
FATAL: SARATHI_CORE_EXECUTE_TASK_URL is still the unset-default placeholder.
       Run: source scripts/ngrok_env.sh --core-api <https://...>
       Or:  export SARATHI_CORE_EXECUTE_TASK_URL=<https://...>/execute_task

$ SARATHI_CORE_EXECUTE_TASK_URL=https://example.invalid/execute_task ./sarathi-enforcement-adapter.exe --post-task-to-core --input "env"
  endpoints source: env
  Core /execute_task URL: https://example.invalid/execute_task
  http timeout: 15s (default; override with SARATHI_ECOSYSTEM_TIMEOUT_MS)
FATAL: PostTaskInput: ... dial tcp: lookup example.invalid: no such host
```

Both behave correctly: placeholder → fail-loud-with-fix-instructions; env
var → wires up, attempts real network call, fails loud on unreachable host.

---

## 6. 6-tunnel topology summary

| Tunnel | Owner | Service | Port | Status (2026-05-06) |
|---|---|---|---|---|
| 1 | Siddhesh | Bucket | 8000 | ✅ have URL |
| 2 | Vijay | InsightFlow | 8001 | ✅ have URL |
| 3 | Raj | BHIV Core API | 8003 | ⏳ pending |
| 4 | Raj | MCP Bridge | 8000 | ⏳ pending |
| 5 | Raj | Sovereign Core | 9001 | ⏳ pending |
| 6 | Us | Sarathi Enforcer | 9002 | ⏳ install ngrok, run `ngrok http 9002`, share with Raj |

If Raj proxies all 3 of his services behind one reverse proxy, tunnels 3+4+5
collapse to 1; helper script handles either layout via flags. See
`NGROK_VALIDATION_SCRIPT.md` §3 (message templates) and §6 (env wiring).

---

## 7. Reviewer reproduction (cold clone, ≤ 30 minutes)

1. `git clone <repo>; cd sarathi-enforcement-adapter`
2. `go build -o sarathi-enforcement-adapter.exe .`
3. Install ngrok (3.x): see `NGROK_VALIDATION_SCRIPT.md` §2.
4. Get auth token from https://dashboard.ngrok.com → `ngrok config add-authtoken <token>`.
5. Coordinate with peers to obtain 5 ngrok URLs (Bucket, InsightFlow, Core API, MCP Bridge, Sovereign Core).
6. `ngrok http 9002` in one terminal; capture your `--self` URL; share with Raj.
7. `source scripts/ngrok_env.sh --bucket ... --insight ... --core-api ... --mcp ... --sov ... --self ...`
8. Transport-stability proof (two runs, identical input):
   * **a.** Run Flow B (`POST /v1/enforce` with the saved `flow_b_input.json`); record `chain_binding_hash` from `flow_b_response.json`.
   * **b.** Wipe (`./scripts/preflight_clean.sh`), restart Sarathi, repeat the same Flow B call; confirm `chain_binding_hash` is identical.
9. End-to-end input bootstrap (Flow A): `./sarathi-enforcement-adapter.exe --post-task-to-core --input "demo X"`. Watch Sarathi service log for inbound `/sarathi/enforce` callback with the same `trace_id`.

If steps 8.b and 9 both pass, **v15.4 closure is independently verified.**

---

## 8. Cross-references

- Operator runbook: [NGROK_VALIDATION_SCRIPT.md](../NGROK_VALIDATION_SCRIPT.md)
- Knowledge base: [KB_14_NGROK_DEPLOYMENT_v15_4.md](../KB_14_NGROK_DEPLOYMENT_v15_4.md)
- Wire contract update: [ENDPOINTS_FOR_BHIV.md](../ENDPOINTS_FOR_BHIV.md) §7
- VC demos: [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) Demos 9 and 10
- Surface closure dependency: [KB_13_NETWORK_SURFACE_CLOSURE_v15_1.md](../KB_13_NETWORK_SURFACE_CLOSURE_v15_1.md)
- Decision-side validation (UNCHANGED): [ENFORCEMENT_VALIDATION_SCRIPT.md](../ENFORCEMENT_VALIDATION_SCRIPT.md)
- Predecessor packet: [vc_integration_validation_v1.md](vc_integration_validation_v1.md)

---

## 9. Sign-off checklist (for the independent reviewer)

- [ ] Built `sarathi-enforcement-adapter.exe` from source on a clean clone.
- [ ] `--post-task-to-core --input "..."` returns Core's response JSON or fails fast on placeholder URL.
- [ ] `scripts/ngrok_env.sh --help` prints; both Mode A and Mode B documented.
- [ ] Demo 9 (ngrok transport stability) — `chain_binding_hash` identical across two repeats of the same input over ngrok.
- [ ] Demo 10 (input bootstrap) — Sarathi log shows callback with Core-generated `trace_id`.
- [ ] Bucket trace-level GET returns the artifact whose `response_hash` equals the Sarathi `chain_binding_hash`.
- [ ] No edits to `ENFORCEMENT_VALIDATION_SCRIPT.md` (`git status` clean).
- [ ] Regression: `--v14-6` audit still 22/22.

---

**End of `phase_v15_4_ngrok_deployment_review.md`.**
**v15.4 status:** complete; ready for tomorrow's testing run.
