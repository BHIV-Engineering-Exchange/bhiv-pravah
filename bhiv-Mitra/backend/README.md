# MITRA Backend

Production backend for the BHIV Ecosystem AI Assistant.

## Overview

FastAPI backend serving as Mitra's core runtime. Processes user messages through a deterministic safety-first pipeline and integrates with all BHIV products through canonical adapters.

## Public API

### Core

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and endpoint listing |
| `/health` | GET | Health check with MongoDB probe |
| `/health/system` | GET | Deep system health |
| `/metrics` | GET | Prometheus metrics |

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/signup` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/auth/me` | GET | Get current user |
| `/api/auth/logout` | POST | User logout |

### Assistant

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/assistant` | POST | Main chat endpoint (V3.0.0) |
| `/api/mitra/evaluate` | POST | Policy evaluation |

### Ecosystem Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ecosystem/products` | GET | List BHIV products |
| `/api/ecosystem/manifests` | GET | Integration manifests |
| `/api/ecosystem/health` | GET | Integration health |
| `/api/ecosystem/query` | POST | Query a BHIV product |
| `/api/ecosystem/execute` | POST | Execute on a BHIV product |
| `/api/ecosystem/snapshot` | GET | Full registry snapshot |

### Replay & Audit

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/replay/{trace_id}` | POST | Replay a trace |
| `/api/replay/{trace_id}/stages` | GET | Get trace stages |
| `/api/replay/compare` | POST | Compare traces |

### Observability

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics` | GET | System metrics |
| `/api/metrics/system` | GET | Detailed metrics |
| `/api/metrics/enforcement` | GET | Enforcement metrics |

### Voice

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tts` | POST | Text-to-speech |
| `/api/tts/status` | GET | TTS engine status |

### Webhooks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/whatsapp` | POST | WhatsApp inbound |
| `/webhooks/telegram` | POST | Telegram inbound |
| `/webhooks/email` | POST | Email inbound |
| `/webhooks/instagram` | POST | Instagram inbound |
| `/webhooks/call` | POST | Telephony inbound |

---

## Authentication

Assistant and ecosystem requests require:

```
X-API-Key: <api-key>
```

Auth routes manage their own bearer-token flow and do not require the assistant API key.

---

## Architecture

The backend uses a single-entry orchestration model with an ecosystem adapter layer.

```
User -> Security Middleware -> Router Dispatch
  -> /api/assistant -> Orchestrator (15+ stages)
  -> /api/ecosystem/* -> Adapter Registry -> BHIV Products
  -> /api/replay/* -> Replay Harness
  -> /api/metrics -> Metrics Collector
```

See: `ARCHITECTURE_OVERVIEW.md`

---

## Ecosystem Integration

11 BHIV products connected through canonical adapters:

| Product | Protocol | Adapter |
|---------|----------|---------|
| UniGuru | REST/Bearer | `uniguru_adapter.py` |
| SETU | REST/API Key | `setu_adapter.py` |
| Gurukul | REST/Bearer | `gurukul_adapter.py` |
| Samruddhi | REST/API Key | `samruddhi_adapter.py` |
| Namami Gange | REST/API Key | `namami_gange_adapter.py` |
| SVACS | REST/API Key | `svacs_adapter.py` |
| UCCIS | REST/Bearer | `uccis_adapter.py` |
| NYAI | REST/Bearer | `nyai_adapter.py` |
| Brahmanda | REST/API Key | `brahmanda_adapter.py` |
| Bucket | Internal | `bucket_adapter.py` |
| TANTRA | REST/API Key | `tantra_adapter.py` |

---

## Monitoring

- **OpenTelemetry**: Traces + metrics via OTLP
- **Prometheus**: Auto-instrumented `/metrics` endpoint
- **Grafana**: Pre-built enterprise dashboard

---

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
cd deploy/kubernetes
kubectl apply -f .
```

### Render

See `render.yaml` for configuration.

---

## Load Testing

```bash
pip install locust
bash deploy/loadtest/run_loadtest.sh 50 10 60
```

---

## Status

Backend integrated with ecosystem adapters, monitoring, and production deployment configs.

## Optional TTS Runtime

The main backend deploy does not require Coqui XTTS.
Optional TTS dependencies are isolated from the base deployment.

To enable the XTTS stack on a dedicated environment:

```bash
pip install -r requirements-tts.txt
```
