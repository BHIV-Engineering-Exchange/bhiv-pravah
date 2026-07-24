# Sarathi — Repository Map

Where to find each subsystem. 135 source `.go` files (+ 17 tests) live flat in
the repo root, grouped here by filename prefix and responsibility. To locate a
symbol fast: search the prefix below, then grep within those files.

---

## 1. Entry points

| File(s) | Role |
|---|---|
| `enforcement_adapter_main.go` | `main()` — argument dispatch to every mode (service, CLIs, harnesses). |
| `service_runtime_cli.go` | `--service` runtime: boot gates, listener, graceful shutdown. |
| `service_boundary.go` | HTTP route registration and the request boundary. |
| `cmd_*.go` | One-shot CLIs (see §3). |

---

## 2. Enforcement core (the PEP)

| Prefix / file | Role |
|---|---|
| `enforcement_adapter*.go` | The enforcement pipeline and adapter logic. |
| `service_boundary*.go` | Request boundary, TANTRA handlers, propagation hook. |
| `response_contract.go` | The sealed enforcement response schema. |
| `external_decision.go` | Inbound decision parsing + verification. |
| `pdp_*.go` | Policy decision plumbing. |
| `policy_*.go` | Policy registry. |
| `execution_*.go` | Execution request / trace handling. |

---

## 3. CLI commands (`cmd_*.go`)

| File | Command |
|---|---|
| `cmd_post_task.go` | `--post-task-to-core` — drive a decision through the chain. |
| `cmd_bucket_transmit.go` | `--bucket-transmit` — live Bucket integration proof. |
| `cmd_tantra_register.go` | TANTRA registration. |
| `cmd_tantra_convergence.go` | TANTRA convergence driver. |
| `cmd_provider_keygen.go` | Crypto provider key generation. |
| `cmd_peer_key_register.go` | Register a peer's Ed25519 public key. |
| `cmd_jwt_authority.go` | JWT capability-token authority CLI. |

---

## 4. Cryptography & trust

| Prefix | Role |
|---|---|
| `crypto_*.go` | Crypto-agility provider (Ed25519 default, ML-DSA-65 hybrid toggle). |
| `peer_key_registry.go` | Pinned per-peer Ed25519 public keys; impersonation defence. |
| `tantra_*.go` | TANTRA decision canonicalization, signing, verification, emit. |
| `cet_*.go` | CET (convergence) contract, verifier, service handler, artifact. |
| `jwt_authority_*.go`, `jwt_*.go` | JWT capability-token mint + verify + handlers. |

---

## 5. Peers & propagation

| Prefix / file | Role |
|---|---|
| `peer_common.go` | Shared peer envelope processing + receipt verification. |
| `peer_bucket.go` | Legacy Bucket client. |
| `bucket_bhiv_adapter.go` | Aligned Bucket adapter (envelope, read-back, signed receipt). |
| `bucket_readback_verifier.go` | Bucket read-back verification. |
| `bucket_state_verifier.go` | Bucket chain-state checks. |
| `peer_insightflow.go` | Reference InsightFlow peer simulator (local tests). |
| `translation_insightflow*.go` | InsightFlow Schema A/B/C/D builders + fan-out router. |
| `translation_bucket_artifact.go` | Production BucketArtifact builder (fan-out path). |
| `translation_sovereign_schemas.go` | All peer wire-schema structs. |
| `translation_bhiv_fanout.go` | Consolidated BHIV fan-out. |
| `ecosystem_endpoints.go` | `SARATHI_*_URL` env-var wiring (single source of truth for peer URLs). |
| `ecosystem_clients.go` | Outbound peer HTTP clients (attaches headers + API key). |
| `ecosystem_contracts.go` | Bridge passport / bypass-prevention contracts. |
| `service_boundary_propagation_hook.go` | Fires fan-out after ingest. |
| `downstream_ack_endpoint.go` | Receives signed receipts at `/v1/downstream-ack`. |

---

## 6. Audit & observability

| File | Role |
|---|---|
| `persistent_audit.go` | Persistent audit sink. |
| `jsonl_audit_sink.go` | Append-only JSONL audit writer. |
| `observability_trace.go` | Trace/span observability. |
| `cross_machine_telemetry.go` | Cross-machine telemetry. |

---

## 7. Evaluators, governance, config

| Prefix | Role |
|---|---|
| `evaluator_*.go` | Evaluator registry + admin API/CLI. |
| `governance_*.go` | Production hardening (TLS, DB, metrics, keys). |
| `registry_*.go`, `policy_registry.go` | Registries. |

---

## 8. Test / proof harnesses (not part of the runtime path)

| Prefix / file | Role |
|---|---|
| `adversarial_attack_harness.go` | Adversarial attack suite. |
| `*_simulator.go`, `*_runner.go` | Core/distributed/live integration simulators. |
| `propagation_*.go`, `*_replay*.go` | Propagation + replay determinism. |
| `multi_*.go` | Multi-node determinism. |
| `clock_*.go`, `parallel_*.go`, `transport_*.go` | Specialized stress/determinism harnesses. |
| `*_test.go` | Go unit/integration tests (17 files). |

---

## 9. Config & schema inputs (do NOT delete)

| File | Role |
|---|---|
| `go.mod`, `go.sum` | Module + dependency manifest. |
| `evaluator_registry_config.json` | Evaluator registry config. |
| `registry_config.json` | Registry config. |
| `sovereign-response-schema.json` | Response schema. |
| `execution_trace_schema.json` | Trace schema. |
| `Dockerfile` | Container build. |
| `live/keys/` | Local key material (enforcement + peer keys). |

---

## 10. Runtime output (regenerable)

| Location | Contents |
|---|---|
| `proof_logs/` | Audit trails, propagation log, receipts, Bucket proofs. |
| `live/` | Per-peer event logs + translation artifacts. |

---

## 11. Handover & test docs

| File | Purpose |
|---|---|
| `SETUP_GUIDE.md` | Build, run, deploy, env vars, troubleshooting. |
| `BUILD_STATE.md` | What works / incomplete / tech debt. |
| `SYSTEM_OVERVIEW.md` | Concepts and responsibilities. |
| `ARCHITECTURE_FLOW.md` | End-to-end data flow. |
| `REPO_MAP.md` | This file. |
| `FAQ.md` | Common questions. |
| `PENDING_WORK.md` | Open items + next steps. |
| `BUCKET_TEST_COMMANDS.md` | Step-by-step Bucket integration runbook. |
| `INSIGHTFLOW_INTEGRATION.md` | InsightFlow wire contract. |
| `scripts/test_bucket.ps1`, `scripts/test_insightflow.ps1` | Reusable integration tests. |
