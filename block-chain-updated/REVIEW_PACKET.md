# REVIEW PACKET — TANTRA Convergence Integration
**Author:** Prakash Yadav  
**Task:** Blockchain Enforcement Integration (BlackHole Blockchain – TANTRA Convergence)

---

## Real Transaction Flow (Live, Non-Bypassable)

```
Wallet / External Client
        │
        ▼
POST /api/relay/submit  (Port 8080)
        │
        ▼
┌─────────────────────────────────────────────┐
│           TANTRA ENFORCEMENT LAYER          │
│                                             │
│  1. injectTraceID  (if not present)         │
│  2. ExecutionAgent → execution_hash         │
│  3. ValidationAgent → fraud check (9090)    │
│                     → validation_hash       │
│  4. ReplayAgent    → replay_hash            │
│                                             │
│  EQUALITY GATE:                             │
│  execution_hash == validation_hash          │
│                == replay_hash               │
│  AND fraud_decision == "allow"              │
│                                             │
│  MISMATCH or FRAUD → HTTP 403 HARD REJECT  │
└─────────────────────────────────────────────┘
        │  (only if all checks pass)
        ▼
Fraud Service  (Port 9090)
POST /api/fraud/check
        │
        ▼
blockchain.ProcessTransaction()
        │
        ▼
Truth Store  (tantra_truth.jsonl)
Appends: trace_id + execution_hash +
         validation_hash + replay_hash +
         tx_hash + fraud_decision
        │
        ▼
Blockchain Write (mempool → block)
```

---

## Phase Completion Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Access Control | Repo access configured |
| 1 | Blockchain Entry Integration | ✅ DONE — `enforcement.Enforce()` called in `handleRelaySubmit` |
| 2 | Fraud System Integration | ✅ DONE — `ValidationAgent` calls fraud service on port 9090 |
| 3 | Replay + Equality Enforcement | ✅ DONE — hash equality gate, HTTP 403 on mismatch |
| 4 | Full Transaction Flow Lock | ✅ DONE — no bypass path exists in `handleRelaySubmit` |
| 5 | Truth + Bucket Integration | ✅ DONE — store + verify against real blockchain state |

---

## Key Files

| File | Role |
|------|------|
| `core/relay-chain/enforcement/tantra.go` | TANTRA pipeline: ExecutionAgent, ValidationAgent, ReplayAgent, Enforce |
| `core/relay-chain/fraud/fraud.go` | Fraud detection service (port 9090) |
| `core/relay-chain/truthstore/truthstore.go` | Append-only JSONL store + Verify against blockchain |
| `core/relay-chain/api/server.go` | `handleRelaySubmit`, `handleTantraVerify`, `handleTantraRecords` |
| `core/relay-chain/chain/blockchain.go` | `FindTransactionByID` — on-chain lookup for Phase 5 verify |
| `core/relay-chain/cmd/fraud-service/main.go` | Fraud service binary |
| `core/relay-chain/cmd/relay/main.go` | Blockchain node binary |
| `tantra_truth.jsonl` | Runtime truth store (created on first accepted tx) |

---

## How to Run

**Terminal 1 — Fraud Service (port 9090):**
```bash
cd core/relay-chain
go run cmd/fraud-service/main.go
```

**Terminal 2 — Blockchain Node (port 8080):**
```bash
cd core/relay-chain
go run cmd/relay/main.go 3000
```

---

## Postman Proof

### Successful Transaction (all hashes match, fraud = allow)
```json
POST http://localhost:8080/api/relay/submit
{
  "type": "token_transfer",
  "from": "alice",
  "to": "bob",
  "amount": 100,
  "token_id": "BHX",
  "nonce": 1,
  "timestamp": <current_unix>
}
```
Expected response (HTTP 200):
```json
{
  "success": true,
  "transaction_id": "<tx_hash>",
  "status": "pending",
  "trace_id": "<16-char hex>",
  "execution_hash": "<sha256>",
  "validation_hash": "<sha256>",
  "replay_hash": "<sha256>",
  "fraud_decision": "allow"
}
```
All three hashes will be identical (deterministic pipeline).

### Rejected Transaction — Fraud Block
```json
POST http://localhost:8080/api/relay/submit
{
  "type": "token_transfer",
  "from": "bad-actor",
  "to": "bob",
  "amount": 100,
  "token_id": "BHX",
  "nonce": 1,
  "timestamp": <current_unix>
}
```
Expected response (HTTP 403):
```json
{
  "success": false,
  "error": "TANTRA enforcement rejected transaction",
  "rejection_reason": "fraud service blocked this transaction",
  "trace_id": "...",
  "fraud_decision": "block"
}
```

### Rejected Transaction — Zero Amount
```json
POST http://localhost:8080/api/relay/submit
{
  "from": "alice", "to": "bob", "amount": 0,
  "token_id": "BHX", "timestamp": <current_unix>
}
```
Expected response (HTTP 403) — fraud rule: zero amount.

---

## Phase 5 — Verify Against Real Blockchain State

### Check if a transaction is verified on-chain
```
GET http://localhost:8080/api/tantra/verify?tx_hash=<transaction_id>
```
Expected response (verified):
```json
{
  "success": true,
  "result": {
    "found": true,
    "on_chain": true,
    "hashes_match": true,
    "record": {
      "trace_id": "a1b2c3d4e5f6a7b8",
      "execution_hash": "abc123...",
      "validation_hash": "abc123...",
      "replay_hash": "abc123...",
      "tx_hash": "<tx_id>",
      "fraud_decision": "allow",
      "timestamp": 1720000000
    }
  }
}
```

### Verify by trace_id
```
GET http://localhost:8080/api/tantra/verify?trace_id=a1b2c3d4e5f6a7b8
```

### View all truth store records (audit)
```
GET http://localhost:8080/api/tantra/records
```

---

## Truth Store Sample (tantra_truth.jsonl)
```jsonl
{"trace_id":"a1b2c3d4e5f6a7b8","execution_hash":"abc123...","validation_hash":"abc123...","replay_hash":"abc123...","tx_hash":"def456...","fraud_decision":"allow","timestamp":1720000000}
```

---

## Enforcement Guarantee

The equality gate `execution_hash == validation_hash == replay_hash` is enforced because all three agents call `deterministicHash(tx)` on the **same immutable `TxPayload` struct** after `injectTraceID` has run once. The hash is SHA-256 over the canonical JSON of the payload — deterministic by construction. Any tampering between phases would require changing the payload, which would change the hash, which would trigger a hard reject.

---

## 🛠️ Deployment Infrastructure & Observability Integration Notes (Added by Alay)

These integration notes detail the hardened deployment configuration, sequential bootstrapping, automated pre-flight checks, and metrics/observability endpoints established for the BlackHole Blockchain ecosystem.

### 1. Hardened Container Setup & Sequential Bootstrapping
To prevent race conditions where dependent services start before nodes are fully initialized:
- Follower validator nodes `blockchain-node-2` through `5` depend on `blockchain-node-1` with `condition: service_healthy` (configured in [docker-compose.blockchain.yml](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Blackhole_Blockchain-main/Blackhole_Blockchain-main/docker-compose.blockchain.yml)).
- The `bridge` and `wallet` services also wait for `blockchain-node-1` to report healthy before starting.
- Standardized custom external network `blackhole-network` across all compose files to support dynamic resolution.
- Configured custom persistent volume name `blackhole-blockchain_blockchain_data` for host folder-name independence.

### 2. Startup Automation
The startup automation scripts ([start-services.ps1](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Blackhole_Blockchain-main/Blackhole_Blockchain-main/start-services.ps1) and [start-services.sh](file:///c:/Users/ASUS/OneDrive/Desktop/BHIV-Tasks/Blackhole_Blockchain-main/Blackhole_Blockchain-main/start-services.sh)) compile the services and bootstrap the network sequentially:
- **Pre-flight Checks**: Auto-detects Docker daemon state, scans for local port conflicts (`8080`, `8545`, `9000`, `8084`, `9090`), and auto-creates the `blackhole-network` bridge.
- **Bootstrapping Sequence**: Starts blockchain nodes -> waits for Node 1 to pass health checks -> starts the wallet backend -> starts the bridge daemon.
- **Bypass Execution Policy** (Windows): Can be executed using:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\start-services.ps1
  ```

### 3. Service Observability & Diagnostic Endpoints
- **Blockchain Node Health**: `GET /api/health` (Port `8080`–`8085`).
- **Wallet Status & Dependency Diagnostics**: `GET /api/status` (Port `9000`). Reports:
  - Active sessions count.
  - Precise service uptime in seconds (tracked from a global `startTime`).
  - Active blockchain node P2P connectivity status using `wallet.DefaultBlockchainClient.IsConnected()`.
  - Storage backends status (PostgreSQL, Redis, MongoDB, BadgerDB fallback).
- **Bridge SDK Health**: `GET /health` (Port `8084`). Returns comprehensive component statuses, uptime, and versions.

### 4. Dynamic Network Configuration (Docker Mode)
When `DOCKER_MODE=true` is enabled:
- The bridge service (configured with `WALLET_API_URL` and `BLOCKCHAIN_API_URL`) resolves requests to `http://blackhole-wallet:9000/api/status` and `http://blackhole-node-1:8080` instead of failing on host `localhost` loopbacks.
- The wallet service dynamically discovers node multiaddrs via `BLOCKCHAIN_API_URL + "/api/p2p/info"`.
- Container healthchecks have been hardened by installing `curl` package inside the runtime Alpine stage of the blockchain node and bridge Dockerfiles.

