# Assistant Backend Architecture (v3 - Enterprise)

## Overview

This backend implements the AI Assistant as a **single, production-ready system**
with a **locked assistant interface**, merged frontend auth, and BHIV ecosystem integration.

The system exposes **one public assistant API endpoint** for all assistant interactions,
plus ecosystem integration routes, merged auth routes, replay/audit, and monitoring.

### Public API

| Category | Endpoints |
|----------|-----------|
| Core | `GET /`, `GET /health`, `GET /health/system`, `GET /metrics` |
| Auth | `POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout` |
| Assistant | `POST /api/assistant`, `POST /api/mitra/evaluate` |
| Ecosystem | `GET /api/ecosystem/products`, `GET /api/ecosystem/manifests`, `GET /api/ecosystem/health`, `POST /api/ecosystem/query`, `POST /api/ecosystem/execute`, `GET /api/ecosystem/snapshot` |
| Replay | `POST /api/replay/{trace_id}`, `GET /api/replay/{trace_id}/stages`, `POST /api/replay/compare` |
| Metrics | `GET /api/metrics`, `GET /api/metrics/system`, `GET /api/metrics/enforcement` |
| Voice | `POST /api/tts`, `GET /api/tts/status` |
| Webhooks | `POST /webhooks/whatsapp`, `POST /webhooks/telegram`, `POST /webhooks/email`, `POST /webhooks/instagram`, `POST /webhooks/call` |

---

## High-Level Architecture

```
Client (Web / Mobile / Desktop / WhatsApp / Telegram / Email)
|
v
Security Middleware (API Key + JWT + Rate Limit)
|
v
Router Dispatch
|
+--> /api/assistant ---------> Assistant Orchestrator (15+ stages)
|                                |
|                                +--> Language Detection
|                                +--> Intent Classification
|                                +--> Policy Engine
|                                +--> Behavior Validation
|                                +--> Enforcement Engine
|                                +--> LLM Response
|                                +--> Outbound Safety
|                                +--> Execution Service
|
+--> /api/ecosystem/* -------> Adapter Registry
|                                |
|                                +--> UniGuru Adapter
|                                +--> SETU Adapter
|                                +--> Gurukul Adapter
|                                +--> ... (11 total)
|
+--> /api/replay/* ----------> Replay Harness
|                                |
|                                +--> Trace Loading
|                                +--> Replay Execution
|                                +--> Comparison
|
+--> /api/metrics -----------> Metrics Collector
|                                |
|                                +--> Request Counts
|                                +--> Enforcement Stats
|                                +--> System Uptime
|
+--> /metrics ---------------> Prometheus Exporter
```

---

## Architectural Layers

### 1. API Layer
- Exposes endpoints for assistant, auth, ecosystem, replay, metrics
- Handles authentication, validation, and error normalization
- Provides deterministic, frontend-safe contracts

### 2. Security Layer
- API Key validation on all `/api/*` routes
- JWT tokens for user sessions
- Rate limiting per IP
- HMAC-signed gateway tokens for executors

### 3. Orchestration Layer (Assistant)
- Central decision point for all assistant requests
- 15+ stage pipeline: Language -> Intent -> Policy -> Safety -> Enforcement -> LLM -> Execution
- Deterministic trace IDs (SHA-256 based)
- Fail-closed behavior under all failure conditions

### 4. Ecosystem Layer
- Adapter Registry (singleton, lazy instantiation)
- 11 BHIV product adapters following `BaseBHIVAdapter` contract
- Canonical `IntegrationRequest`/`IntegrationResponse` contracts
- Per-adapter health tracking with latency metrics

### 5. Intelligence & Workflow Layer (Internal)
- Intent classification and task analysis
- LLM multi-provider bridge (Groq, OpenAI, Gemini, Mistral)
- Workflow execution when side-effects are required
- **Not accessible directly by clients**

### 6. Infrastructure Layer
- MongoDB persistence (users, tasks, audit_logs)
- Redis caching
- OpenTelemetry tracing + metrics
- Prometheus auto-instrumentation
- Grafana dashboards

---

## Request Lifecycle (Assistant)

1. Client sends request to `/api/assistant`
2. Security middleware validates API key + rate limit
3. API layer normalizes request to V3.0.0 schema
4. Orchestrator generates deterministic trace_id
5. Language detection and translation
6. Intent classification
7. Policy engine evaluation
8. Behavior validation
9. Enforcement decision (ALLOW/REWRITE/BLOCK)
10. LLM response generation
11. Outbound safety gate
12. Execution service (if action detected)
13. Response translation back to user language
14. TTS audio generation (if requested)
15. Response returned with trace_id
16. Audit logged to MongoDB bucket

---

## Request Lifecycle (Ecosystem)

1. Client sends request to `/api/ecosystem/query` or `/api/ecosystem/execute`
2. Security middleware validates API key
3. Adapter Registry looks up product adapter
4. `IntegrationRequest` constructed with trace_id
5. Adapter executes query/execute against product API
6. `IntegrationResponse` returned
7. Health metrics updated
8. Audit logged

---

## Graceful Failure & Safety Policy

The backend guarantees frontend-safe behavior under all failure conditions.

### Failure Handling Rules

- **Missing Dependencies**: Dependency skipped, passive response returned
- **Timeouts**: Orchestration timeout enforced, safe fallback returned
- **Partial Workflow Failure**: Failure does not break response schema
- **Unexpected Errors**: Deterministic error envelope returned, no stack traces exposed

### Guarantee

Under no condition does the backend:
- Break the response schema
- Leak internal logic
- Require frontend retries due to instability

---

## Ecosystem Integration

### Adapter Pattern

All BHIV products integrate through canonical adapters:

```
Mitra -> Adapter Registry -> Product Adapter -> Product API
```

### Base Contract

```python
class BaseBHIVAdapter(ABC):
    product_name: str
    manifest: IntegrationManifest
    query(request: IntegrationRequest) -> IntegrationResponse
    execute(request: IntegrationRequest) -> IntegrationResponse
    health_check() -> Dict
```

### Registered Products

| Product | Protocol | Capabilities |
|---------|----------|-------------|
| UniGuru | REST/Bearer | query, execute, notify |
| SETU | REST/API Key | query, execute, stream, sync |
| Gurukul | REST/Bearer | query, execute, notify |
| Samruddhi | REST/API Key | query, execute, notify |
| Namami Gange | REST/API Key | query, execute, stream |
| SVACS | REST/API Key | query, execute, notify |
| UCCIS | REST/Bearer | query, execute, notify, stream |
| NYAI | REST/Bearer | query, execute, stream, notify |
| Brahmanda | REST/API Key | query, execute, stream, sync |
| Bucket | Internal | query, execute, sync |
| TANTRA | REST/API Key | query, execute, stream, sync |

---

## Monitoring & Observability

### OpenTelemetry
- Traces exported via OTLP to collector
- Metrics exported via OTLP to collector
- FastAPI auto-instrumentation

### Prometheus
- `/metrics` endpoint auto-instrumented
- Request rate, latency histograms, error rates
- Enforcement decision counters

### Grafana
- Enterprise dashboard with 6 panels
- Request rate, response time, enforcement, instances, errors, integrations

---

## Deployment

- **Docker Compose**: 7 services (core, worker, MongoDB, Redis, Prometheus, Grafana, OTEL)
- **Kubernetes**: 3-replica deployment with HPA, ingress, network policy
- **Render**: Single-service deployment

---

## Design Principles

- **Single Entry Point** for assistant interactions
- **Encapsulation of internals** from clients
- **Deterministic routing** and trace generation
- **Frontend safety** under all failure conditions
- **Canonical contracts** for ecosystem integration
- **Authority boundaries** enforced by control plane
- **Replay determinism** for audit and governance

---

## Architecture Status

**LOCKED - Enterprise Convergence Complete**

This architecture is production-ready with ecosystem integration, monitoring, and deployment configs.
