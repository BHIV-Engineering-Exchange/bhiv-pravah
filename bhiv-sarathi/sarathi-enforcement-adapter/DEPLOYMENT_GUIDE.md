# Sarathi v15.11 — Deployment Guide

**Audience:** Sarathi operator / DevOps / SRE running the production rollout.
**Scope:** Deployment notes, environment setup, runtime configuration, execution instructions, health verification, endpoint map. Everything an operator needs from "binary built" to "live with three peers acknowledging."
**Companions:** `NGROK_VALIDATION_SCRIPT.md` (cross-tunnel runbook), `REVIEW_PACKET.md` (proof packet), `CORE_INTEGRATION.md` / `BUCKET_INTEGRATION.md` / `INSIGHTFLOW_INTEGRATION.md` (per-team specs to share out).

---

## 1. Deployment notes

Sarathi v15.11 ships as a single static Go binary. No runtime dependencies beyond Go stdlib + Cloudflare CIRCL (for the optional hybrid crypto provider). No database. No message broker. State lives on disk under `live/` + `proof_logs/`.

| Property | Value |
|---|---|
| Language / version | Go 1.25+ |
| Binary size | ~16 MB on Windows AMD64 |
| Build cmd | `go build -o sarathi-enforcement-adapter.exe .` |
| External deps | `github.com/cloudflare/circl` (hybrid provider only), `github.com/google/uuid`, `github.com/lib/pq` (PostgreSQL audit sink, optional), `github.com/golang-jwt/jwt/v5` (JWT capability tokens) |
| Default service port | 9002 (configurable) |
| TLS | Optional (`SARATHI_TLS_CERT_PATH` / `SARATHI_TLS_KEY_PATH`); operator-required in production |
| Persistence | File-backed JSONL under `live/` and `proof_logs/` |
| Crypto | Ed25519 (default) or Composite ML-DSA-65 + Ed25519 (opt-in via env var) |

---

## 2. Environment setup

### 2.1 Directory layout (one-time)

```
sarathi/
├── sarathi-enforcement-adapter.exe        # the binary
├── live/
│   ├── .env                                 # operator env file (optional)
│   ├── trust_snapshot.json                  # registry (evaluators, tantra_evaluators, peer_keys)
│   └── keys/
│       ├── sarathi_enforcement/              # Sarathi's own attestation keypair
│       │   ├── issuer-priv.hex             # mode 0600
│       │   └── issuer-pub.hex              # mode 0644
│       └── jwt_authority/                   # Sarathi JWT signing keypair (v15.6)
│           ├── current.key
│           └── current.pub
└── proof_logs/                              # auto-created on first run
    └── ...                                  # see §6 for the list
```

### 2.2 One-time keypair generation

Generate Sarathi's own enforcement keypair (used to sign outbound TANTRA attestation records):

```bash
SARATHI_CRYPTO_PROVIDER=ed25519 ./sarathi-enforcement-adapter.exe --provider-keygen \
    --evaluator-id=bhiv.sarathi.enforcement.prod.v1 \
    --out-dir=./live/keys/sarathi_enforcement \
    --key-id-rotation=2026-05
```

Output: `issuer-priv.hex` (mode 0600 — keep local) + `issuer-pub.hex` (mode 0644 — share with peers). Stdout prints the ready-to-paste command structure.

### 2.3 Register Sovereign Core (after Core sends keys)

After BHIV Core (Raj / Aakanksha) sends out-of-band: their PUBLIC Ed25519 key, key_id, and api_key_fingerprint:

```bash
./sarathi-enforcement-adapter.exe --register-tantra-evaluator \
    --evaluator-id=bhiv.sovereign.decision.prod.v1 \
    --schema-version=tantra.decision.v1 \
    --algorithm=Ed25519 \
    --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
    --public-key=<64-hex-from-Core> \
    --api-key-fingerprint=<64-hex-from-Core> \
    --name="Sovereign BHIV Core" \
    --snapshot=./live/trust_snapshot.json
```

Audit row written to `proof_logs/tantra_registry_audit.jsonl`.

### 2.4 Register propagation peers (after each peer team sends their key)

For each of Bucket (Siddhesh), InsightFlow (Vijay), and Core (Raj — `peer='core'` for post-execution receipts), once they send their PUBLIC Ed25519 key:

```bash
./sarathi-enforcement-adapter.exe --register-peer-key \
    --peer=bucket \
    --public-key=<64-hex-from-Siddhesh> \
    --name="Bucket production" \
    --snapshot=./live/trust_snapshot.json

./sarathi-enforcement-adapter.exe --register-peer-key \
    --peer=insightflow \
    --public-key=<64-hex-from-Vijay> \
    --name="InsightFlow production" \
    --snapshot=./live/trust_snapshot.json

./sarathi-enforcement-adapter.exe --register-peer-key \
    --peer=core \
    --public-key=<64-hex-from-Raj> \
    --name="BHIV Core post-exec" \
    --snapshot=./live/trust_snapshot.json
```

Audit rows written to `proof_logs/peer_key_registry_audit.jsonl`.

---

## 3. Runtime configuration

### 3.1 Required env vars (production)

```bash
# Service binding
SARATHI_SERVICE_ADDR=0.0.0.0:9002              # 0.0.0.0 not 127.0.0.1 so ngrok / load balancer can forward
SARATHI_ENV=production                          # enables production boot gates

# Inbound TANTRA auth
SARATHI_INBOUND_AUTH_MODE=required              # require X-API-Key when fingerprint registered
SARATHI_TRACE_ID_REQUIRE_INBOUND=true           # production must never mint trace_id locally
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json

# Sarathi's outbound enforcement signing
SARATHI_ENFORCEMENT_PRIV_PATH=./live/keys/sarathi_enforcement/issuer-priv.hex
SARATHI_ENFORCEMENT_PUB_PATH=./live/keys/sarathi_enforcement/issuer-pub.hex
SARATHI_ENFORCEMENT_KEY_ID=bhiv.sarathi.enforcement.prod.v1#ed25519-2026-05

# Crypto provider (default Ed25519)
SARATHI_CRYPTO_PROVIDER=ed25519                 # OR "hybrid" once peers are hybrid-capable

# Peer-key pinning
SARATHI_PEER_KEY_PINNING=strict                 # production: every peer must be registered

# Production peer fan-out
SARATHI_PROPAGATE_ON_INGEST=1                   # post canonical bytes to peers after /sarathi/enforce success

# Outbound URLs (one per peer endpoint)
SARATHI_BUCKET_ARTIFACT_POST_URL=https://<bucket-host>/bucket/artifact
SARATHI_BUCKET_ARTIFACT_GET_URL=https://<bucket-host>/bucket/artifact
SARATHI_BUCKET_ARTIFACTS_TRACE_URL=https://<bucket-host>/bucket/artifacts
SARATHI_INSIGHT_PROCESS_URL=https://<insightflow-host>/insightflow_process
SARATHI_INSIGHT_TRIGGER_URL=https://<insightflow-host>/sarathi_trigger
SARATHI_INSIGHT_EXECUTE_URL=https://<insightflow-host>/core_execute
SARATHI_INSIGHT_BUCKET_PERSIST_URL=https://<insightflow-host>/bucket_persist
SARATHI_INSIGHT_VERIFY_BUCKET_URL=https://<insightflow-host>/bucket/verify
SARATHI_CORE_ENFORCE_URL=https://<core-host>/v1/enforce
SARATHI_CORE_EXECUTE_URL=https://<core-host>/v1/execute
SARATHI_CORE_HEALTH_URL=https://<core-host>/health
SARATHI_CORE_EXECUTE_TASK_URL=https://<core-host>/execute_task
SARATHI_CORE_HANDLE_TASK_URL=https://<core-host>/handle_task
SARATHI_CORE_SOVEREIGN_DECIDE_URL=https://<core-host>/sovereign/decide
SARATHI_CORE_SOVEREIGN_HEALTH_URL=https://<core-host>/health

# Tuning (defaults shown)
SARATHI_REQUEST_SKEW_S=300                       # inbound HTTP header nonce window
SARATHI_NONCE_WINDOW_S=900                       # inbound HTTP nonce store window
SARATHI_ECOSYSTEM_TIMEOUT_MS=15000              # outbound HTTP timeout
```

### 3.2 Optional env vars

```bash
# TLS (operator-required for production deployments)
SARATHI_SERVICE_REQUIRE_TLS=1
SARATHI_TLS_CERT_PATH=./live/tls/cert.pem
SARATHI_TLS_KEY_PATH=./live/tls/key.pem

# Production boot gates
SARATHI_SERVICE_REQUIRE_NONDEFAULT_KEYS=1       # refuse to start with default API keys

# Hybrid crypto (only when SARATHI_CRYPTO_PROVIDER=hybrid)
SARATHI_HYBRID_KEY_ROTATION_TAG=composite-mldsa65-ed25519-2026-05

# Peer-receipt endpoints (must be enabled to receive callbacks)
SARATHI_ENABLE_PEER_RECEIPTS=1                  # mounts /v1/handshake and /v1/downstream-ack

# JWT capability tokens (v15.6 outbound bridge)
SARATHI_JWT_AUTHORITY_PRIV_PATH=./live/keys/jwt_authority/current.key
SARATHI_TOKEN_ISSUER=https://<sarathi-host>/authority
SARATHI_TOKEN_AUDIENCE=bhiv-core-runtime
```

### 3.3 Putting it in `live/.env`

Create `live/.env` once; Sarathi auto-loads it at boot. Example:

```bash
SARATHI_SERVICE_ADDR=0.0.0.0:9002
SARATHI_ENV=production
SARATHI_INBOUND_AUTH_MODE=required
SARATHI_TRACE_ID_REQUIRE_INBOUND=true
SARATHI_TRUST_SNAPSHOT=./live/trust_snapshot.json
SARATHI_ENFORCEMENT_PRIV_PATH=./live/keys/sarathi_enforcement/issuer-priv.hex
SARATHI_ENFORCEMENT_PUB_PATH=./live/keys/sarathi_enforcement/issuer-pub.hex
SARATHI_ENFORCEMENT_KEY_ID=bhiv.sarathi.enforcement.prod.v1#ed25519-2026-05
SARATHI_CRYPTO_PROVIDER=ed25519
SARATHI_PEER_KEY_PINNING=strict
SARATHI_PROPAGATE_ON_INGEST=1
SARATHI_ENABLE_PEER_RECEIPTS=1
SARATHI_BUCKET_ARTIFACT_POST_URL=https://<bucket-host>/bucket/artifact
SARATHI_INSIGHT_PROCESS_URL=https://<insightflow-host>/insightflow_process
SARATHI_CORE_ENFORCE_URL=https://<core-host>/v1/enforce
# ... (the remaining outbound URLs)
```

---

## 4. Execution instructions

### 4.1 Build the binary

```bash
cd /path/to/sarathi-enforcement-adapter
go build -o sarathi-enforcement-adapter.exe .
```

### 4.2 First-time setup (one-time per environment)

```bash
# 1. Generate Sarathi's own keypair
./sarathi-enforcement-adapter.exe --provider-keygen \
    --evaluator-id=bhiv.sarathi.enforcement.prod.v1 \
    --out-dir=./live/keys/sarathi_enforcement \
    --key-id-rotation=2026-05

# 2. Register Sovereign Core (after Core sends keys out-of-band)
./sarathi-enforcement-adapter.exe --register-tantra-evaluator \
    --evaluator-id=bhiv.sovereign.decision.prod.v1 \
    --schema-version=tantra.decision.v1 \
    --algorithm=Ed25519 \
    --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
    --public-key=<hex> --api-key-fingerprint=<hex> \
    --snapshot=./live/trust_snapshot.json

# 3. Register the three peers
./sarathi-enforcement-adapter.exe --register-peer-key --peer=bucket      --public-key=<hex> --snapshot=./live/trust_snapshot.json
./sarathi-enforcement-adapter.exe --register-peer-key --peer=insightflow --public-key=<hex> --snapshot=./live/trust_snapshot.json
./sarathi-enforcement-adapter.exe --register-peer-key --peer=core        --public-key=<hex> --snapshot=./live/trust_snapshot.json
```

### 4.3 Start the service

```bash
./sarathi-enforcement-adapter.exe --service
```

Output prints the boot banner including provider, registry counts, and listening address. Stdout + stderr also tee'd to `sarathi_run_<timestamp>.log` in the repo root.

Expected boot banner:

```
+-------------------------------------------------------+
|  SARATHI ENFORCEMENT ADAPTER v15.7                    |
|  Sovereign Governance Kernel — Production Hardened    |
|  Build: TANTRA Final Contract + Crypto-Agile          |
+-------------------------------------------------------+
[crypto] provider=Ed25519 env=ed25519 key_id_suffix="#ed25519-<rotation>"
[tantra_trust] loaded N/N entries from ./live/trust_snapshot.json (provider=Ed25519)
[peer_key_registry] loaded 3/3 peer key(s) from ./live/trust_snapshot.json (mode=strict)
[Service] listening at 0.0.0.0:9002
  POST /sarathi/enforce
  POST /v1/downstream-ack
  GET  /v1/handshake
  GET  /health
  GET  /metrics
```

### 4.4 Stop / restart

`Ctrl+C` for graceful shutdown. Sarathi closes connections, fsyncs audit logs, exits cleanly with status 0.

---

## 5. Health verification

### 5.1 Liveness

```bash
curl -sS https://<sarathi-host>/health
```

Expected: `200 OK` with JSON `{"status":"healthy","bridge_active":true,"service_status":"ready","service_version":"v15.7","..."}`.

### 5.2 Deep health (includes downstream peer reachability)

```bash
curl -sS https://<sarathi-host>/health/deep
```

Expected: `200 OK` plus per-peer reachability check results.

### 5.3 Schema handshake (peer-facing)

```bash
curl -sS https://<sarathi-host>/v1/handshake
```

Returns the response-fields contract every peer must validate against. Useful for peers to pin Sarathi's contract version.

### 5.4 Metrics

```bash
curl -sS https://<sarathi-host>/metrics
```

JSON metrics covering total requests, error counters, peer ack counts, replay rejections, provider boot rows.

Prometheus-format alias at `/metrics/prometheus`.

### 5.5 Smoke test under each provider

```bash
# Default (Ed25519)
SARATHI_CRYPTO_PROVIDER=ed25519 ./sarathi-enforcement-adapter.exe --list-evaluators
# Expected: [crypto] provider=Ed25519 ...

# Hybrid (Composite ML-DSA-65 + Ed25519)
SARATHI_CRYPTO_PROVIDER=hybrid ./sarathi-enforcement-adapter.exe --list-evaluators
# Expected: [crypto] provider=Composite-MLDSA65-Ed25519 ...

# Invalid value (must panic — proves fail-closed)
SARATHI_CRYPTO_PROVIDER=garbage ./sarathi-enforcement-adapter.exe --list-evaluators
# Expected: panic with explicit refuse-to-boot message; exit non-zero
```

### 5.6 What to watch during one live decision propagation

Open these files (or `tail -f`) BEFORE Core POSTs a decision; everything should appear within ~2 seconds of a successful execution:

| File | What appears |
|---|---|
| `sarathi_run_<ts>.log` | The inbound POST line + handler trace + outbound POST lines |
| `proof_logs/tantra_translation_map.jsonl` | One row: TANTRA → ExternalDecision projection with all hashes |
| `proof_logs/enforcement_audit_backup.jsonl` | One row: enforcement event with verdict and all hashes |
| `proof_logs/sarathi_enforcement_attestations.jsonl` | One row: Sarathi-signed TANTRA attestation |
| `proof_logs/peer_outbound_hashes.jsonl` | One row: per-decision per-peer outbound body hash |
| `proof_logs/peer_propagation_audit.jsonl` | One row: per-peer fan-out outcome (status / hash / error / latency) |
| `proof_logs/downstream_ack_receipts.jsonl` | Three rows (one per peer, async, within 300 s) |
| `proof_logs/tantra_replay.jsonl` | One row: decision_hash + canonical-payload-hash logged for replay rejection |

To watch all in real time:

```bash
tail -f proof_logs/*.jsonl sarathi_run_*.log
```

Pivot on `trace_id` across files to reconstruct the chain. Same `trace_id` should appear in every file.

### 5.7 Rejection paths (intentional failure tests)

To prove fail-closed behavior, run these tests against a live service:

```bash
# Wrong schema_version → 400 ERR_TANTRA_SCHEMA_VERSION_UNKNOWN
curl -X POST https://<sarathi-host>/sarathi/enforce -H "Content-Type: application/json" \
    -d '{"schema_version":"tantra.decision.v999",...}'

# Replay → 409 ERR_TANTRA_REPLAY
curl -X POST <same valid payload twice within 300s>

# Missing X-API-Key when fingerprint registered → 401 ERR_TANTRA_API_KEY_REQUIRED
curl -X POST https://<sarathi-host>/sarathi/enforce -H "Content-Type: application/json" -d '<valid TANTRA payload>'
```

Each rejection produces a `proof_logs/downstream_ack_rejections.jsonl` or `proof_logs/enforcement_audit_backup.jsonl` row with the precise reason.

---

## 6. Endpoint map

### 6.1 Sarathi HTTP surfaces (what Sarathi exposes)

| Method | Path | Purpose |
|---|---|---|
| POST | `/sarathi/enforce` | TANTRA decision intake from Sovereign Core |
| POST | `/v1/ingest-decision` | Canonical 16-field self-test path (operator + harness) |
| POST | `/v1/enforce` | Direct enforcement of a SaarthiRequest (operator path; not used by Core in v15.11) |
| POST | `/v1/downstream-ack` | Peer receipt callback (Bucket / InsightFlow / Core post-exec) |
| GET | `/v1/handshake` | Schema handshake (peers pin against this) |
| GET | `/health` | Liveness |
| GET | `/health/deep` | Deep health including downstream reachability |
| GET | `/metrics` | JSON metrics |
| GET | `/metrics/prometheus` | Prometheus format metrics |
| GET | `/sarathi/.well-known/jwks.json` | Public JWK Set for outbound JWT capability tokens (v15.6) |
| GET | `/sarathi/validate-token` | JWT token validation probe |
| GET | `/v1/bridge/info` | Bridge state introspection |

### 6.2 Sarathi outbound surfaces (what Sarathi calls into BHIV)

| Target | Method | Path | When |
|---|---|---|---|
| Bucket | POST | `/bucket/artifact` | After `/sarathi/enforce` success, async per-decision |
| Bucket | GET | `/bucket/artifact/{decision_id}` | Read-back verification (operator-driven) |
| Bucket | GET | `/bucket/artifacts?trace_id=` | Trace-level enumeration |
| InsightFlow | POST | `/insightflow_process` | After `/sarathi/enforce` success, async per-decision |
| Core | POST | `/v1/enforce` | Post-execution record propagation |
| Core | GET | `/health` | Pre-flight |

### 6.3 Inbound from BHIV (what BHIV calls into Sarathi)

| Source | Method | Path | Purpose |
|---|---|---|---|
| Sovereign Core | POST | `/sarathi/enforce` | TANTRA decision |
| Bucket | POST | `/v1/downstream-ack` | Receipt after storing /bucket/artifact body |
| InsightFlow | POST | `/v1/downstream-ack` | Receipt after processing /insightflow_process body |
| Core | POST | `/v1/downstream-ack` | Receipt after post-execution /v1/enforce body |
| Any peer | GET | `/v1/handshake` | Schema agreement |

---

## 7. Observing a single live decision (DevOps walk-through)

This is the procedure to validate that one end-to-end decision is propagating correctly. Run it as the FIRST production smoke test after deployment.

1. Confirm boot: `curl https://<sarathi-host>/health` returns 200.
2. Confirm registry: `./sarathi-enforcement-adapter.exe --list-evaluators` shows the registered Sovereign + all three peer keys.
3. Open `tail -f proof_logs/*.jsonl sarathi_run_*.log` in one terminal.
4. Ask Core team to POST one decision.
5. In the live log within ~2 s, observe:
   - `sarathi_run_*.log`: inbound POST line for `/sarathi/enforce`, then the 12-step verifier audit, then three outbound POST lines (one per peer).
   - `proof_logs/tantra_translation_map.jsonl`: one new row with the decision's `trace_id`.
   - `proof_logs/enforcement_audit_backup.jsonl`: one new row with the verdict.
   - `proof_logs/peer_propagation_audit.jsonl`: one row covering all three peer hops with HTTP statuses.
6. Within ~5 s (depends on peer ack speed), observe three new rows in `proof_logs/downstream_ack_receipts.jsonl` — one per peer.
7. Re-POST the same decision: should return 409 `ERR_TANTRA_REPLAY` and produce one row in `proof_logs/downstream_ack_rejections.jsonl`.

If any of those steps fails, grep the audit logs for the `trace_id` and walk the reasons.

---

## 8. DevOps / Infra responsibilities (the "if applicable" section in task.md)

When the deployment moves off the developer machine onto real infrastructure, the additional items below need owners. None of these are Sarathi-internal — they are standard production-deployment concerns.

| Item | What it means | Where to do it |
|---|---|---|
| **TLS termination** | Sarathi listens on HTTP; production needs HTTPS. Either operator-supplied cert via `SARATHI_TLS_CERT_PATH`/`SARATHI_TLS_KEY_PATH`, or terminate TLS at an upstream proxy (nginx / Cloudflare / ALB) and forward to Sarathi. | Reverse proxy or `--service` env vars. |
| **Reverse proxy / load balancer** | Sarathi is single-binary, single-process. For HA, run multiple replicas behind a load balancer; trust snapshot + proof_logs MUST be on shared persistent storage so all replicas see the same registry and emit to the same audit log. | nginx, HAProxy, AWS ALB, Cloudflare. |
| **DNS / public hostname** | Peers post to `https://<sarathi-host>/...`. The hostname must be DNS-resolvable from Bucket / InsightFlow / Core networks. For dev/ngrok, the URL is the ngrok tunnel; for prod, a CNAME to the load balancer. | DNS provider. |
| **Firewall / WAF** | Only `/sarathi/enforce`, `/v1/downstream-ack`, `/v1/handshake`, `/health` need to be public-facing. `/v1/ingest-decision` (self-test), `/metrics`, `/v1/bridge/info` should be restricted to internal IPs. | WAF rule set / proxy ACL. |
| **Service supervisor** | Sarathi is `--service` long-lived. Wrap in systemd (Linux), Windows Service, or container orchestrator (Kubernetes) for restart on crash, log rotation, resource limits. | systemd unit / Dockerfile + k8s manifest. |
| **Persistent storage for `live/` + `proof_logs/`** | These directories grow over time. Plan for ≥10 GB. JSONL is append-only; rotate via `logrotate` or equivalent at the OS layer. Trust snapshot is ~1 KB; backed up nightly is sufficient. | EBS volume / persistent claim / mounted disk. |
| **Backup of `trust_snapshot.json`** | Single source of truth for evaluator + peer keys. Lost = re-register every peer. Back up nightly + before every `--register-*` change. | rsync to S3 / restic / equivalent. |
| **Secret management for `issuer-priv.hex`** | Sarathi's own enforcement private key. Lost = re-keygen + re-issue public key to peers. Compromised = same. Store in HashiCorp Vault / AWS Secrets Manager / equivalent for prod; the on-disk file is fine for dev. | Vault / Secrets Manager. |
| **Time sync (NTP)** | Sarathi's verifier checks ±300 s timestamp skew. Hosts with drift > 300 s reject decisions as `ERR_TANTRA_TIMESTAMP_SKEWED`. NTP on every host. | systemd-timesyncd / chronyd / w32time. |
| **Log shipping** | `proof_logs/*.jsonl` are the audit anchor. Ship to centralised logging (ELK / Splunk / Datadog) for queryability + retention beyond the local disk window. | Filebeat / Vector / fluent-bit. |
| **Monitoring & alerting** | Hook `/metrics` into Prometheus + Grafana. Alert on: `total_http_errors` rate spike, `propagation_total` lag, `downstream_ack_rejections` rate, replay-store size > 50k. | Prometheus + Alertmanager. |
| **CI / CD** | `go build` + `go test` + `go vet` gate every merge. Don't deploy a binary without those three green. Tag releases with `v15.x.y`. | GitHub Actions / GitLab CI. |
| **Rollback plan** | Keep N-1 binary on the host. Boot banner prints the active version. Rollback = swap binary + restart. Snapshot file is forward-compatible (additive fields). | Symlink + systemd reload. |
| **Operator runbook** | Document: how to register a new peer, how to rotate Sarathi's keypair, how to flip crypto provider, how to investigate a rejected receipt. Most of this is in `NGROK_VALIDATION_SCRIPT.md` + this guide. | Internal wiki. |

None of these are part of the Sarathi binary's responsibility — they're the environment Sarathi runs in. Allocate ownership to your DevOps / SRE function before going live.

---

## 9. Production readiness checklist

Before flipping the public DNS to Sarathi:

- [ ] `go build` exits 0. `go test ./... -count=1` all green. `go vet ./...` clean.
- [ ] `live/trust_snapshot.json` contains: 1 row in `tantra_evaluators` (Sovereign Core), 3 rows in `peer_keys` (bucket / insightflow / core), Sarathi's own `bhiv.sarathi.enforcement.prod.v1` registered.
- [ ] All 16+ `SARATHI_*_URL` outbound env vars point at REAL peer URLs (no `ngrok-url-not-set.local` placeholders).
- [ ] `SARATHI_PEER_KEY_PINNING=strict` set.
- [ ] `SARATHI_PROPAGATE_ON_INGEST=1` set.
- [ ] `SARATHI_TRACE_ID_REQUIRE_INBOUND=true` set.
- [ ] `SARATHI_INBOUND_AUTH_MODE=required` set.
- [ ] `SARATHI_ENV=production` set.
- [ ] TLS configured at proxy OR via Sarathi env vars.
- [ ] NTP running on the host.
- [ ] `proof_logs/` on persistent storage with rotation configured.
- [ ] `trust_snapshot.json` backed up; backup procedure tested.
- [ ] `issuer-priv.hex` mode 0600; backup in secret manager.
- [ ] Per-team specs sent to Core / Bucket / InsightFlow (see `CORE_INTEGRATION.md`, `BUCKET_INTEGRATION.md`, `INSIGHTFLOW_INTEGRATION.md`).
- [ ] Public keys received from each team and registered via `--register-*` CLIs.
- [ ] Smoke test §5.6 completed against the live deployment.
- [ ] Rejection test §5.7 confirmed (fail-closed behavior verified).
- [ ] First end-to-end decision propagation observed per §7 with all three receipts arriving within 300 s.

When all boxes are checked, Sarathi is production-ready for the live TANTRA chain.
