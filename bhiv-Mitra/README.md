# MITRA - BHIV Ecosystem AI Assistant

Mitra is a production-grade AI assistant platform that serves as BHIV's reusable interaction, orchestration, and execution capability across the entire ecosystem.

## What Mitra Does

Mitra processes user messages through a deterministic safety-first pipeline and can communicate with all BHIV products through canonical adapters.

**Channels**: Web, WhatsApp, Telegram, Email, Instagram, Voice, Calendar, Device
**Products**: UniGuru, SETU, Gurukul, Samruddhi, Namami Gange, SVACS, UCCIS, NYAI, Brahmanda, Bucket, TANTRA

## Architecture

```
User -> React Frontend -> FastAPI Backend
  -> Security (API Key + JWT)
  -> Orchestrator (15+ stage pipeline)
    -> Language Detection -> Intent -> Policy -> Safety -> Enforcement
    -> LLM (Groq/OpenAI/Gemini/Mistral) -> Outbound Safety
    -> Execution -> Platform Executor
  -> Response

Ecosystem:
  Mitra <-> Adapter Registry -> BHIV Products
```

## Quick Start

```bash
# Docker (recommended)
cd backend
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

See [STARTUP_GUIDE.md](STARTUP_GUIDE.md) for full setup instructions.

## Deployment Options

| Method | Config | Status |
|--------|--------|--------|
| Docker Compose | `backend/docker-compose.yml` | 7 services |
| Kubernetes | `backend/deploy/kubernetes/` | 7 manifests + HPA |
| Render | `backend/render.yaml` | Production |
| Vercel | `frontend/frontend/vercel.json` | Production |

## Monitoring

- **Prometheus**: `http://localhost:9090` (metrics scrape)
- **Grafana**: `http://localhost:3001` (dashboards)
- **OpenTelemetry**: OTLP traces + metrics via collector

## BHIV Ecosystem Integration

11 products connected through canonical adapter pattern:

```bash
# List products
curl -H "X-API-Key: your_key" http://localhost:8000/api/ecosystem/products

# Check health
curl -H "X-API-Key: your_key" http://localhost:8000/api/ecosystem/health

# Query a product
curl -X POST -H "X-API-Key: your_key" -H "Content-Type: application/json" \
  http://localhost:8000/api/ecosystem/query \
  -d '{"product": "UniGuru", "action": "courses", "payload": {}}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/assistant` | POST | Main chat (V3.0.0) |
| `/api/auth/*` | POST/GET | Authentication |
| `/api/ecosystem/*` | GET/POST | BHIV product integration |
| `/api/replay/*` | GET/POST | Trace replay |
| `/api/metrics` | GET | System metrics |
| `/api/tts` | POST | Text-to-speech |
| `/webhooks/*` | POST | Channel webhooks |
| `/metrics` | GET | Prometheus metrics |

## Project Structure

```
MITRA-main/
├── backend/
│   ├── app/
│   │   ├── api/           # API routers (assistant, auth, ecosystem, etc.)
│   │   ├── core/          # Orchestrator, security, database, monitoring
│   │   ├── ecosystem/     # BHIV adapter framework
│   │   │   ├── adapters/  # 11 product adapters
│   │   │   ├── base_adapter.py
│   │   │   └── adapter_registry.py
│   │   ├── executors/     # Platform executors
│   │   ├── inbound/       # Inbound channel handlers
│   │   ├── services/      # Business logic services
│   │   └── external/      # External system integrations
│   ├── deploy/
│   │   ├── kubernetes/    # K8s manifests
│   │   ├── prometheus/    # Prometheus config
│   │   ├── grafana/       # Grafana dashboards
│   │   ├── otel-collector/ # OTEL config
│   │   └── loadtest/      # Load testing
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   └── frontend/
│       └── src/
│           ├── components/
│           │   ├── dashboard/  # BHIV Dashboard, Replay, Health
│           │   ├── auth/       # Login, Signup
│           │   └── ...         # Chat components
│           ├── services/       # API layer
│           └── contexts/       # Auth, Language
├── review_packets/             # Enterprise review documentation
└── DEPLOYMENT_GUIDE.md
```

## Documentation

- [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Setup and running
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [review_packets/](review_packets/) - Enterprise review documentation
- `backend/ARCHITECTURE_OVERVIEW.md` - System architecture

## License

Part of the BHIV Ecosystem.
