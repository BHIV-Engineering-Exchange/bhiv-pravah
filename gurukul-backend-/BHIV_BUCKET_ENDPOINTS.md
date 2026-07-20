# BHIV Bucket API Reference

## 1. BHIV Central Depository (External Server)
The standalone storage and governance layer for TANTRA.

- **REST Base URL**: `http://localhost:8000`
- **Socket.IO Base URL**: `http://localhost:5000`

### Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/bucket/artifact/write` | Store a new immutable artifact |
| `GET`  | `/bucket/artifact/read` | Retrieve artifact by ID & product |
| `POST` | `/bucket/artifact/query` | Search artifacts via metadata |
| `POST` | `/bucket/audit/append` | Append entry to immutable audit trail |
| `GET`  | `/bucket/latest-hash` | Get chain head for cryptographic continuity |
| `GET`  | `/health` | System health & service status |

### Real-time Events (Socket.IO)
- `agent-recommendation`: Emitted on adaptive decisions
- `escalation`: Emitted on governance violations
- `dependency-update`: Emitted on artifact linking

---

## 2. Gurukul Internal Bucket Router (Integration Layer)
The gateway within Gurukul for educational telemetry.

- **Local Base URL**: `http://localhost:3000/api/v1`
- **Production Base URL**: `https://gurukul-up9j.onrender.com/api/v1`

### Ingestion & Contracts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/bucket/prana/ingest` | Primary PRANA packet ingestion |
| `POST` | `/bucket/artifact/write` | BHIV Contract-compliant write alias |
| `GET`  | `/bucket/latest-hash` | Get local head hash (packet/review/task) |
| `GET`  | `/audit/artifact/{id}` | Inspect packet for verification |

### Queue & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/bucket/prana/packets/pending` | Get packets for Karma Tracker |
| `POST` | `/bucket/prana/packets/mark-processed` | Confirm processing completion |
| `GET`  | `/bucket/prana/status` | Queue size & storage statistics |

---

## 3. Configuration Variables
- `BUCKET_URL`: Usually `http://localhost:8000/bucket/artifact/write`
- `TANTRA_API_KEY`: Required for authenticated writes
