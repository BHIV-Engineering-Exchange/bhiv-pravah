# KESHAV

Deterministic dependency intelligence layer — TANTRA contract compliant.

## Quick start

```bash
pip install -e ".[dev]"
python api.py
```

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Run full TANTRA pipeline, returns KESHAV output contract |
| GET | `/health` | Liveness check |

### Input contract

```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "tasks": [
    { "task_id": "T1", "depends_on": [] },
    { "task_id": "T2", "depends_on": ["T1"] }
  ],
  "constraint_results": [
    { "task_id": "T1", "is_valid": false, "unsatisfied_dependencies": [] },
    { "task_id": "T2", "is_valid": false, "unsatisfied_dependencies": ["T1"] }
  ],
  "propagation_results": [
    { "task_id": "T1", "affected_tasks": ["T2"], "impact_score": 10 },
    { "task_id": "T2", "affected_tasks": [],     "impact_score": 4  }
  ]
}
```

### Output contract (200 OK)

```json
{
  "trace_id": "upstream-trace-001",
  "execution_id": "exec-001",
  "root_cause": "T1",
  "resolution_signal": "UNBLOCK_DEPENDENCY:T1",
  "impact_score": 10,
  "severity": "HIGH",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### Failure response (400)

```json
{ "status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": "" }
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5000` | Listening port |
| `DEBUG` | `false` | Flask debug mode |

## Development

```bash
make test        # run all tests
make coverage    # tests + coverage report (≥90% required)
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make check       # lint + typecheck + coverage
```

## Production Deployment

### Docker
```bash
make docker-build      # build container
make docker-run        # run container
make docker-logs       # view logs
```

### Docker Compose
```bash
make docker-compose-up    # start services
make docker-compose-logs  # view logs
make docker-compose-down  # stop services
```

### Kubernetes
```bash
make k8s-deploy    # deploy to cluster
make k8s-status    # check pod status
make k8s-logs      # view logs
make k8s-delete    # remove deployment
```

### Bare Metal
```bash
make run-prod      # gunicorn with 4 workers
```

See `DEPLOYMENT.md` for full production deployment guide.

## Architecture

```
SETU/Input
  → KESHAV  (analyzer/)         — dependency intelligence, TANTRA output contract
  → RAJYA   (tantra/rajya.py)   — decision layer, zero transformation
  → Sarathi (tantra/sarathi.py) — enforcement layer
  → Core    (tantra/core.py)    — execution layer
  → Bucket  (tantra/bucket.py)  — truth layer, write-on-success only

InsightFlow (tantra/insightflow.py) — read-only observability, structured events
```

See `review-packets/REVIEW_PACKET.md` for full contract specification and convergence proof.

## Convergence Documentation

**Constitutional Hardening:**
- `CONSTITUTIONAL_BOUNDARIES.md` — Authority boundaries, orchestration separation, governance drift prevention
- `AUTHORITY_ISOLATION_PROOF.md` — Proof that RAJYA/Sarathi/Core/Bucket/InsightFlow retain authority
- `HIDDEN_STATE_DISCLOSURE.md` — Runtime state classification, zero authority-bearing state

**Replay Validation:**
- `DISTRIBUTED_REPLAY_VALIDATION.md` — 10/10 identical outputs, trace continuity, Bucket truth reconstruction
- `CORRUPTION_INJECTION_PROOF.md` — Fail-closed corruption resistance, deterministic rejection signatures
- `OBSERVABILITY_INTEGRITY.md` — InsightFlow read-only, replay-safe, non-authoritative

**Operational Handover:**
- `OPERATIONAL_HANDOVER.md` — Complete stewardship package for Rajaryan Verma
- `MAINTAINER_FAQ.md` — 50 Q&A for incoming maintainers
