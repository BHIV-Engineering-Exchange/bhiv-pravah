# Sarathi Enforcement Adapter — Setup Guide

Target: a developer with zero prior context can build, run, and verify Sarathi
in under 30 minutes. This guide is self-contained.

---

## 1. What Sarathi is (one paragraph)

Sarathi is a Policy Enforcement Point (PEP). It receives sealed enforcement
decisions over HTTP, verifies them cryptographically, records an immutable audit
trail, and optionally propagates the result to downstream peers (Bucket,
InsightFlow, Core). It is a single self-contained Go binary with no mandatory
external database.

---

## 2. Prerequisites

| Requirement | Notes |
|---|---|
| Go toolchain | Version per `go.mod`. Verify with `go version`. |
| Git | To clone / pull. |
| OS | Builds and runs on Windows, Linux, macOS. Commands below are PowerShell. |
| Network | Outbound HTTPS only (to reach peers). No inbound ports needed unless running as a service. |

No database is required for the default runtime. (A PostgreSQL integration
exists but is opt-in via `SARATHI_DB_*` and is not needed to run or test.)

---

## 3. Build

From the repository root:

```powershell
go build -o sarathi-enforcement-adapter.exe .
```

A clean build produces `sarathi-enforcement-adapter.exe` (~16 MB) and prints
nothing. Sanity-check the toolchain and static analysis:

```powershell
go vet ./...
```

Both should complete with no output.

---

## 4. Run the service

```powershell
.\sarathi-enforcement-adapter.exe --service
```

On startup the service:
1. Runs pre-flight security gates.
2. Binds its HTTP listener (see §6 for the address).
3. Prints the full list of routes it serves.
4. Logs `[service] ready; pid=...; listening on <addr>`.

Stop it with Ctrl-C (graceful shutdown, default 30 s; tune with
`SARATHI_SERVICE_SHUTDOWN_TIMEOUT_S`).

### HTTP routes served

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/ingest-decision` | Primary ingest — enforces a decision and (if enabled) fires propagation |
| POST | `/v1/enforce` | Enforcement endpoint |
| POST | `/sarathi/enforce` | TANTRA enforcement alias |
| POST | `/sarathi/validate-token` | Inbound token validation |
| POST | `/v1/downstream-ack` | Receives signed receipts from peers |
| GET | `/health`, `/health/deep` | Liveness / readiness |
| GET | `/metrics`, `/metrics/prometheus` | Metrics |
| GET | `/v1/bridge/info` | Bridge identity info |

### Quick smoke test (separate terminal)

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8443/health"
```

Expect a JSON health body. (Adjust host:port to your `SARATHI_SERVICE_ADDR`.)

---

## 5. Environment variables

None are required for a local default run. Group by purpose:

### 5.1 Listener
| Var | Default | Purpose |
|---|---|---|
| `SARATHI_SERVICE_ADDR` | `127.0.0.1:8443` | Listen address. **Set to `0.0.0.0:<port>` for any non-local / cloud host** so the platform can reach it. |
| `SARATHI_SERVICE_SHUTDOWN_TIMEOUT_S` | `30` | Graceful-shutdown deadline. |

### 5.2 Execution handler
| Var | Default | Purpose |
|---|---|---|
| `SARATHI_WEBHOOK_URL` | unset → simulation | When set, permitted decisions are executed via this webhook. Unset = safe simulation mode. |

### 5.3 Enforcement signing
| Var | Default | Purpose |
|---|---|---|
| `SARATHI_ENFORCEMENT_PRIV_PATH` | falls back to `live/keys/sarathi_enforcement/issuer-priv.hex` | Ed25519 key Sarathi signs its custody receipts with. |

### 5.4 Downstream propagation (fan-out) — OFF by default
| Var | Default | Purpose |
|---|---|---|
| `SARATHI_PROPAGATE_ON_INGEST` | `0` (off) | Set `1` to fan out each enforced decision to peers. |
| `SARATHI_BUCKET_ARTIFACT_POST_URL` | — | Bucket `/bucket/artifact` URL. |
| `SARATHI_INSIGHT_TRIGGER_URL` / `_EXECUTE_URL` / `_PROCESS_URL` / `_BUCKET_PERSIST_URL` | — | InsightFlow endpoint URLs. |
| `SARATHI_INSIGHT_API_KEY` | — | `X-API-Key` Sarathi presents to InsightFlow. |
| `SARATHI_CORE_ENFORCE_URL` | — | Core post-execution endpoint. |

With the flag off, Sarathi still enforces every request — it just does not call peers.

### 5.5 Production hardening (only when `SARATHI_ENV=production`)
| Var | Purpose |
|---|---|
| `SARATHI_ENV=production` | Activates strict boot gates below. Leave unset for development/smoke-tests. |
| `SARATHI_INBOUND_AUTH=required` | Mandatory in production; rejects unauthenticated callers. |
| `SARATHI_CALLER_KEY_<SYSTEM>` | Per-caller API keys; production refuses to start on default keys. |
| `SARATHI_TRUST_SNAPSHOT` or `SARATHI_TRUST_REMOTE_URL` | Trust registry (evaluator/peer public keys). Required in production required-mode. |
| `SARATHI_SERVICE_REQUIRE_TLS=1` + `SARATHI_TLS_CERT_PATH` + `SARATHI_TLS_KEY_PATH` | Enforce TLS at the listener. |

---

## 6. Running on a cloud host

A cloud platform typically injects a port via an env var and requires the
process to bind `0.0.0.0`. Two settings make Sarathi reachable and useful there:

1. **Bind correctly (mandatory):**
   ```
   SARATHI_SERVICE_ADDR = 0.0.0.0:<platform-port>
   ```
   Without this, the default `127.0.0.1:8443` is unreachable and the platform's
   health check fails.

2. **Enable propagation (optional):** set `SARATHI_PROPAGATE_ON_INGEST=1` plus
   the peer URLs and `SARATHI_INSIGHT_API_KEY` from §5.4.

Start command on the host: `./sarathi-enforcement-adapter --service`

Health check path for the platform: `GET /health`.

**Behaviour on ingest:** enforcement runs automatically on every
`POST /v1/ingest-decision`. Propagation to peers fires only if §5.4 is
configured. Nothing else is required for the enforcement path to work.

---

## 7. Where things are written at runtime

| Location | Contents |
|---|---|
| `proof_logs/peer_propagation_audit.jsonl` | One row per fan-out: per-peer URL, HTTP status, ack hash, error, latency. |
| `proof_logs/peer_outbound_hashes.jsonl` | Per-peer outbound body hashes (dual-hash gate). |
| `proof_logs/downstream_ack_receipts.jsonl` / `..._rejections.jsonl` | Signed receipts received back from peers (accepted / rejected). |
| `proof_logs/bucket/` | Bucket transmission records + signed custody receipts. |
| `live/` | Per-peer append-only event logs and translation artifacts. |

Tail the master transmission log live:
```powershell
Get-Content proof_logs\peer_propagation_audit.jsonl -Wait -Tail 5
```

---

## 8. Verifying integrations (optional)

Self-contained integration test runbooks are included:

- **Bucket:** see `BUCKET_TEST_COMMANDS.md` (step-by-step), or run
  `.\scripts\test_bucket.ps1`.
- **InsightFlow:** run `.\scripts\test_insightflow.ps1` (use `-Step health`
  first to confirm reachability).

These exercise the live peers end-to-end and print pass/fail per endpoint.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Platform health check fails | Listener bound to `127.0.0.1` | Set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>`. |
| Enforced but peers never called | Propagation disabled | Set `SARATHI_PROPAGATE_ON_INGEST=1` + peer URLs. |
| `FATAL ... SARATHI_INBOUND_AUTH` | `SARATHI_ENV=production` without inbound auth | Set `SARATHI_INBOUND_AUTH=required` (+ caller keys, trust snapshot) or unset `SARATHI_ENV`. |
| Custody receipt unsigned | Enforcement key not found | Set `SARATHI_ENFORCEMENT_PRIV_PATH` or ensure `live/keys/sarathi_enforcement/issuer-priv.hex` exists. |
| Peer returns 4xx/5xx | Peer-side issue | Check `proof_logs/peer_propagation_audit.jsonl` for the status + error string. |

---

## 10. Next steps for a new owner

1. Build (§3) and run the service (§4); confirm `/health` responds.
2. Read `BUILD_STATE.md` for what works / what's pending.
3. Read `SYSTEM_OVERVIEW.md` and `ARCHITECTURE_FLOW.md` for the model.
4. Use `REPO_MAP.md` to locate any subsystem.
5. Run the integration runbooks in §8 to see live propagation.
