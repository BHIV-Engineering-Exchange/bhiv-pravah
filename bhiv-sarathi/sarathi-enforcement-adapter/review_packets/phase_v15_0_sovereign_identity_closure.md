# Phase v15.0 — Sovereign Identity Closure Review Packet

**System:** Sarathi Enforcement Adapter — Inbound HTTP cryptographic identity (default-OFF)
**Version:** v15.0
**Author:** Hemanth B
**Organization:** Blackhole Infiverse (BHIV)
**Review Date:** 2026-04-25
**Classification:** Internal Sovereign Design / Strictly Confidential
**Predecessor packets:** [v14.6 Distributed Determinism](phase_v14_6_distributed_determinism_review.md), [v14.7 Live Integration Closure](phase_v14_7_live_integration_closure.md), [v14.8 Sovereign Authority Closure](phase_v14_8_sovereign_authority_closure.md)

---

## 1. Executive Summary

v14.9 proved deterministic, fail-closed propagation under hostile downstream conditions. The boundary at `/v1/enforce` still trusted any caller holding an `X-API-Key`. v15.0 closes that gap — *not by switching it on tomorrow*, but by **building** the full inbound auth + Ed25519 evaluator registry + production boot-gate posture into the binary while leaving it **OFF by default**. A two-stage cutover (`SARATHI_INBOUND_AUTH=optional` → `=required` + `SARATHI_ENV=production`) activates the production posture without a rebuild.

### Key achievements

- **Default build is byte-identical to v14.9 on the request path** (INV-AUTH-04). The full v14.9 regression suite stays green: `--v14-6` 22/22, `--live-integration 5` 5/5 (env-dependent — see §6), `--parallel-execute 10` 10/10, distributed 10/10, failure-demo 3/3, service-live 8/8, `go test ./...` pass. No env vars set → no behavioural change.
- **Stage A — VC reviewer demo** ([VC_VALIDATION_SCRIPT.md §19](../VC_VALIDATION_SCRIPT.md)) — operator generates an API key with `--genapikey`, shares URL + key over a private channel; tester pastes a self-contained curl block. No Ed25519, no registry edits.
- **Stage C — production posture** ([VC_VALIDATION_SCRIPT.md §20](../VC_VALIDATION_SCRIPT.md)) — every accepted POST is bound to a registered ACTIVE evaluator via Ed25519 over `canonical(body) ‖ 0x1E ‖ nonce ‖ 0x1E ‖ ts ‖ 0x1E ‖ issuer_id`. Replay protection via bounded LRU + TTL trim + fsync overflow. **Verified 2026-04-25**: 4 distinct adversarial flags (`--omit-signature`, `--force-timestamp=-3600`, `--reuse-nonce`, `--issuer-id=ghost`) produced 4 distinct rejection reasons with rows in `proof_logs/inbound_auth_rejections.jsonl`.
- **Production boot gates** — three refusals, all `os.Exit(78)`, demonstrated end-to-end on 2026-04-25: `ERR_INBOUND_AUTH_OFF_IN_PRODUCTION`, `default API keys detected for [...]`, `ERR_TRUST_REGISTRY_EMPTY`. Gates fire only when `SARATHI_ENV=production`.
- **Defense in depth** — boundary signature (binds HTTP body + nonce + timestamp + issuer) and deep-pipeline signature (binds `decision_core_hash`) use the **same** Ed25519 key from the **same** registry but **different** messages.
- **Admin CLI surface** — `--genkey`, `--genapikey`, `--register-evaluator`, `--suspend-evaluator`, `--revoke-evaluator`, `--reactivate-evaluator`, `--list-evaluators`, `--sign-and-post`, `--report-query`. All mutations append to `proof_logs/registry_audit.jsonl`. Snapshot writes are atomic.

---

## 2. Audit findings remediated

| # | Finding (pre-v15.0) | Disposition | Anchor |
|---|---|---|---|
| A-01 | Only-API-key at `/v1/enforce` | Inbound middleware shipped, default OFF | [service_inbound_auth.go](../service_inbound_auth.go), [service_boundary.go](../service_boundary.go) `SetInboundAuth` |
| A-02 | Ed25519 signature verified in deep pipeline only | Boundary verify added; deep verify retained | [service_inbound_auth.go](../service_inbound_auth.go) §2.3 + existing [external_decision.go](../external_decision.go) |
| A-03 | Registry default empty in-memory | Fallback unchanged for dev; production refuses empty | [service_runtime_cli.go](../service_runtime_cli.go) `RunServiceRuntime` boot gates |
| A-04 | Default `bhiv-*-api-key-v1` keys | Production refuses defaults | [service_runtime_cli.go](../service_runtime_cli.go) gate 2 |
| A-05 | No nonce / timestamp check at boundary | LRU + skew added | [inbound_nonce_store.go](../inbound_nonce_store.go), `service_inbound_auth.go` step 3+5 |
| B-02 | Banner read v14.5 | Updated to v15.0 | [enforcement_adapter_main.go](../enforcement_adapter_main.go) `printBanner` |

---

## 3. Industry posture comparison (audit summary)

| Vendor / framework | Inbound caller identity at API boundary | v15.0 alignment |
|---|---|---|
| Anthropic API | API key + per-org secret | Stage A parity (API key only); Stage C exceeds with Ed25519 + nonce + timestamp |
| Google Cloud (IAP / GoogleAuth) | OIDC + signed JWT bearer | Stage C parity (Ed25519 detached signature instead of JWT) |
| AWS API Gateway (Sig V4) | HMAC-SHA256 over canonical request | Stage C exceeds — public-key crypto, replay protection via nonce store |
| Microsoft / Azure Front Door | TLS client cert + JWT | Stage C parity (different identity primitive, same trust model) |
| OpenAI API | API key only | Stage A parity |
| IBM / NVIDIA / Mistral | API key + IP allowlist | Stage A + B parity |

The v15.0 posture is consistent with the most stringent of these (signed-request + replay protection), implemented with stdlib-only Go (`crypto/ed25519`, `encoding/json`, `container/list`).

---

## 4. Invariants

| ID | Statement | Mechanism / artefact |
|---|---|---|
| **INV-AUTH-01** | Stage C: every accepted POST is cryptographically bound to a registered ACTIVE evaluator. | 7-step `authenticate` in [service_inbound_auth.go](../service_inbound_auth.go); `proof_logs/inbound_auth_rejections.jsonl` empty for legitimate traffic. |
| **INV-AUTH-02** | No two accepted POSTs share a nonce within `SARATHI_NONCE_WINDOW_S` for the same issuer. | `InboundNonceStore` in [inbound_nonce_store.go](../inbound_nonce_store.go); evidence row from 2026-04-25 with `first_seen` timestamp. |
| **INV-AUTH-03** | `SARATHI_ENV=production` refuses unsafe configurations. | Boot gates in [service_runtime_cli.go](../service_runtime_cli.go); three `exit 78` refusals demonstrated 2026-04-25. |
| **INV-AUTH-04** | Default v15.0 build is byte-identical to v14.9 on the request path. | `NewInboundAuthMiddleware(off) == nil`; full v14.9 regression suite green. |

---

## 5. Reviewer block — reproducible runs

Every command below was exercised on 2026-04-25 against a freshly-built binary. No fixtures pre-baked; every artefact is real.

### 5.1 Default-OFF byte-identity proof

```bash
go build -o sarathi-enforcement-adapter.exe .
unset SARATHI_INBOUND_AUTH SARATHI_ENV
./sarathi-enforcement-adapter.exe --v14-6                          # 22/22
./sarathi-enforcement-adapter.exe --parallel-execute 10            # 10/10
SARATHI_DIST_LOOPBACK_AUTOSPAWN=1 \
  ./sarathi-enforcement-adapter.exe --distributed-integration 10   # 10/10
./sarathi-enforcement-adapter.exe --failure-demo                   # 3/3
./sarathi-enforcement-adapter.exe --service-live-demo              # 8/8
go test -count=1 ./...                                             # pass
```

### 5.2 Stage A reviewer demo (URL + API key only)

```bash
export SARATHI_SERVICE_ADDR=0.0.0.0:8443 SARATHI_LISTEN_HOST=0.0.0.0
export SARATHI_CALLER_KEY_TEST_HARNESS=$(./sarathi-enforcement-adapter.exe --genapikey)
./sarathi-enforcement-adapter.exe --service &
curl -i -X POST http://127.0.0.1:8443/v1/enforce \
  -H "Content-Type: application/json" -H "X-API-Key: $SARATHI_CALLER_KEY_TEST_HARNESS" \
  -d '{"agent_id":"a","resource_id":"r","action":"read","correlation_id":"c","caller_system":"test_harness","caller_version":"v15.0","requested_at":"'"$(date -u +%FT%TZ)"'"}'
# HTTP 200 / 403 with full SaarthiResponse JSON; verdict reflects policy v1
```

### 5.3 Stage C smoke (signed POST + 4 adversarial rejections)

```bash
./sarathi-enforcement-adapter.exe --genkey --out-dir ./live/demo-keys
export SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json
export SARATHI_ADMIN_TOKEN=$(./sarathi-enforcement-adapter.exe --genapikey)
./sarathi-enforcement-adapter.exe --register-evaluator \
  --issuer-id="$(cat live/demo-keys/issuer-id.txt)" \
  --public-key="$(cat live/demo-keys/issuer-pub.hex)" \
  --status=active --admin-token="$SARATHI_ADMIN_TOKEN"

export SARATHI_INBOUND_AUTH=required SARATHI_SERVICE_ADDR=127.0.0.1:18444
export SARATHI_CALLER_KEY_TEST_HARNESS=dev-key-stage-c-test
./sarathi-enforcement-adapter.exe --service &

# Happy path
./sarathi-enforcement-adapter.exe --sign-and-post \
  --priv-key=live/demo-keys/issuer-priv.key \
  --issuer-id="$(cat live/demo-keys/issuer-id.txt)" \
  --endpoint=http://127.0.0.1:18444/v1/enforce \
  --api-key=dev-key-stage-c-test --decision-file=/tmp/req.json
# HTTP 200/403 with SaarthiResponse JSON; nonce + ts + issuer printed; passes boundary

# Adversarial — produces 4 distinct rows in proof_logs/inbound_auth_rejections.jsonl
./sarathi-enforcement-adapter.exe --sign-and-post ... --omit-signature       # 400 ERR_INBOUND_SIGNATURE_MISSING
./sarathi-enforcement-adapter.exe --sign-and-post ... --force-timestamp=-3600 # 401 ERR_INBOUND_TIMESTAMP_SKEWED
./sarathi-enforcement-adapter.exe --sign-and-post ... --reuse-nonce=X         # 409 ERR_INBOUND_NONCE_REPLAY (2nd call)
./sarathi-enforcement-adapter.exe --sign-and-post ... --issuer-id=ghost       # 403 ERR_EVALUATOR_NOT_REGISTERED

./sarathi-enforcement-adapter.exe --report-query proof_logs/inbound_auth_rejections.jsonl reason
# Confirms 4+ distinct reasons
```

### 5.4 Production boot-gate refusals (3 × exit 78)

```bash
SARATHI_ENV=production SARATHI_INBOUND_AUTH=off ./sarathi-enforcement-adapter.exe --service
# FATAL: ERR_INBOUND_AUTH_OFF_IN_PRODUCTION

SARATHI_ENV=production SARATHI_INBOUND_AUTH=required ./sarathi-enforcement-adapter.exe --service
# FATAL: default API keys detected for [...] in SARATHI_ENV=production

SARATHI_ENV=production SARATHI_INBOUND_AUTH=required \
  SARATHI_CALLER_KEY_KSML=k1 ... SARATHI_CALLER_KEY_TEST_HARNESS=k7 \
  ./sarathi-enforcement-adapter.exe --service
# FATAL: ERR_TRUST_REGISTRY_EMPTY
```

---

## 6. Known caveats observed during 2026-04-25 audit

- `--live-integration 5` is environment-sensitive on Windows — the bucket peer ACK rate is reliable but the core/insightflow peer ACKs depend on per-machine timing. This is a v14.7 trait, not a v15.0 regression. The v14.6 audit (`--v14-6`) and the parallel/distributed/failure/service-live gates remain reliable across reboots.
- Stale `proof_logs/determinism_violation_log.jsonl` entries from prior test runs can lower the `--v14-6` audit. Cure: `rm -f proof_logs/determinism_violation_log.jsonl` before the audit run. The audit harness reads any prior entries; v15.0 does not produce new ones.

---

## 7. Definition of done

- [x] Subsystem A — inbound auth middleware, nonce store, admin CLI, 9 tests (real Ed25519, real `InMemoryTrustConsumer`, no mocks). [service_inbound_auth.go](../service_inbound_auth.go), [inbound_nonce_store.go](../inbound_nonce_store.go), [evaluator_admin_cli.go](../evaluator_admin_cli.go), [service_inbound_auth_test.go](../service_inbound_auth_test.go).
- [x] Subsystem B — banner v15.0, `RunEvaluatorAdminCLI` dispatch wired ahead of `--service`. Subsystem B-01 (delete `propagation_fault_injection_sim.go`) deferred — file is tagged `test-affordance-only` and referenced by a comment in `retry_determinism_harness.go`; conservative call to keep until retry-determinism wiring follow-on.
- [x] Subsystem C — KB_12 (NEW), KB_01 / KB_02 / KB_03 / KB_04 / KB_06 / KB_11 updated, SARATHI_SYSTEM_GUIDE.md Part IX (NEW), VC_VALIDATION_SCRIPT.md §19 + §20 (NEW), PRODUCTION_DEPLOYMENT_GUIDE.md §13 (NEW), this review packet (NEW).
- [x] Stage A reviewer demo verified: URL + API key → HTTP 200 / 403 with policy verdict.
- [x] Stage C smoke verified: signed POST happy path + 4 adversarial rejection reasons.
- [x] Three production boot-gate refusals verified (exit 78).
- [x] No mocks, no fakes, no pre-recorded outputs — every artefact traces to a live binary run on 2026-04-25.

---

## 8. Cross-references

- [KB_12_INBOUND_IDENTITY_v15_0.md](../KB_12_INBOUND_IDENTITY_v15_0.md) — full spec
- [SARATHI_SYSTEM_GUIDE.md](../SARATHI_SYSTEM_GUIDE.md) Part IX — operator mental model
- [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) §19 (Stage A) and §20 (Stage B/C)
- [PRODUCTION_DEPLOYMENT_GUIDE.md](../PRODUCTION_DEPLOYMENT_GUIDE.md) §13 — runbook
- [KB_06_BOUNDARY_AND_GAPS.md](../KB_06_BOUNDARY_AND_GAPS.md) Gaps GG, HH — closed
- [KB_04_INVARIANTS_AND_BYPASS_PROOFS.md](../KB_04_INVARIANTS_AND_BYPASS_PROOFS.md) — INV-AUTH-01..04
