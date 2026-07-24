# TECHNICAL REVIEW PACKET — KESHAV

**For:** Engineering Teams & Technical Stakeholders  
**Prepared By:** Pritesh (Architect)  
**Date:** 2025-01-XX  
**Status:** Production Ready

---

## Technical Overview

KESHAV is a **deterministic dependency intelligence layer** that analyzes task dependency graphs, identifies root causes of blockages, and produces structured recommendations for downstream execution layers.

**Core Capabilities:**
- Blocked task detection
- Root cause tracing (BFS traversal)
- Bottleneck identification (max impact score)
- Resolution signal generation
- Severity classification (LOW, MEDIUM, HIGH)

---

## Architecture Deep Dive

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         SETU/Input                          │
│                    (External Data Source)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    KESHAV (analyzer/)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. validate()           → Fail-closed validation     │  │
│  │ 2. detect_blocked_tasks() → Blocked task IDs         │  │
│  │ 3. trace_root_causes()    → Root cause map           │  │
│  │ 4. detect_bottleneck()    → Max impact task          │  │
│  │ 5. generate_actions()     → Resolution signal        │  │
│  │ 6. structure_output()     → TANTRA output contract   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   RAJYA (tantra/rajya.py)                   │
│              Decision Layer — Zero Transformation           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Sarathi (tantra/sarathi.py)                 │
│                    Enforcement Layer                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core (tantra/core.py)                     │
│                     Execution Layer                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Bucket (tantra/bucket.py)                  │
│              Truth Layer — Write-on-Success                 │
└─────────────────────────────────────────────────────────────┘

                    (Observability)
┌─────────────────────────────────────────────────────────────┐
│              InsightFlow (tantra/insightflow.py)            │
│           Read-Only Observability — Structured Events       │
└─────────────────────────────────────────────────────────────┘
```

---

## API Specification

### Endpoint: POST /analyze

**Request:**
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

**Response (200 OK):**
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

**Response (400 FAIL):**
```json
{
  "status": "FAIL",
  "reason": "INVALID_INPUT_CONTRACT",
  "trace_id": ""
}
```

---

### Endpoint: GET /health

**Response (200 OK):**
```json
{
  "status": "OK",
  "service": "KESHAV"
}
```

---

### Endpoint: GET /metrics

**Response (Prometheus format):**
```
# HELP keshav_requests_total Total number of requests
# TYPE keshav_requests_total counter
keshav_requests_total 1234

# HELP keshav_request_errors_total Total number of failed requests
# TYPE keshav_request_errors_total counter
keshav_request_errors_total 5

# HELP keshav_request_success_rate Request success rate
# TYPE keshav_request_success_rate gauge
keshav_request_success_rate 0.9959

# HELP keshav_request_latency_seconds Request latency
# TYPE keshav_request_latency_seconds summary
keshav_request_latency_seconds{quantile="0.5"} 0.0234
keshav_request_latency_seconds{quantile="0.95"} 0.0456
keshav_request_latency_seconds{quantile="0.99"} 0.0789

# HELP keshav_unique_traces_total Unique trace IDs processed
# TYPE keshav_unique_traces_total counter
keshav_unique_traces_total 1234

keshav_severity_total{severity="HIGH"} 123
keshav_severity_total{severity="MEDIUM"} 456
keshav_severity_total{severity="LOW"} 655
```

---

### Endpoint: GET /metrics/json

**Response (JSON format):**
```json
{
  "request_count": 1234,
  "request_errors": 5,
  "request_success_rate": 0.9959,
  "avg_latency_seconds": 0.0234,
  "p95_latency_seconds": 0.0456,
  "p99_latency_seconds": 0.0789,
  "severity_distribution": {
    "HIGH": 123,
    "MEDIUM": 456,
    "LOW": 655
  },
  "unique_traces_processed": 1234
}
```

---

## Algorithm Details

### Phase 1: Blocked Task Detection
```python
def detect_blocked_tasks(constraint_results: list) -> list[str]:
    blocked = [
        cr["task_id"]
        for cr in constraint_results
        if not cr.get("is_valid", True)
    ]
    return sorted(blocked)  # Deterministic ordering
```

**Complexity:** O(n) where n = number of tasks

---

### Phase 2: Root Cause Tracing
```python
def trace_root_causes(blocked_tasks: list, constraint_results: list) -> dict:
    root_causes = {}
    for task_id in blocked_tasks:
        visited = set()
        queue = deque([task_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            unsatisfied = get_unsatisfied_dependencies(current, constraint_results)
            if not unsatisfied:
                root_causes[task_id] = current
                break
            
            queue.extend(unsatisfied)
    
    return root_causes
```

**Complexity:** O(n × m) where n = blocked tasks, m = avg dependency depth

**Cycle Detection:** `visited` set prevents infinite loops

---

### Phase 3: Bottleneck Detection
```python
def detect_bottleneck(blocked_tasks: list, propagation_results: list) -> str:
    max_score = -1
    candidates = []
    
    for task_id in blocked_tasks:
        impact_score = get_impact_score(task_id, propagation_results)
        if impact_score > max_score:
            max_score = impact_score
            candidates = [task_id]
        elif impact_score == max_score:
            candidates.append(task_id)
    
    return min(candidates)  # Lexicographic tie-break (deterministic)
```

**Complexity:** O(n) where n = number of blocked tasks

**Determinism:** Lexicographic tie-break ensures same output for same input

---

### Phase 4: Action Generation
```python
def generate_actions(bottleneck: str, root_causes: dict) -> str:
    bottleneck_root_cause = root_causes.get(bottleneck, bottleneck)
    return f"UNBLOCK_DEPENDENCY:{bottleneck_root_cause}"
```

**Complexity:** O(1)

---

### Phase 5: Output Structuring
```python
def structure_output(
    trace_id: str,
    execution_id: str,
    bottleneck: str,
    resolution_signal: str,
    impact_score: int
) -> dict:
    severity = classify_severity(impact_score)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    return {
        "trace_id": trace_id,
        "execution_id": execution_id,
        "root_cause": bottleneck,
        "resolution_signal": resolution_signal,
        "impact_score": impact_score,
        "severity": severity,
        "timestamp": timestamp
    }
```

**Severity Mapping:**
```python
def classify_severity(impact_score: int) -> str:
    if impact_score < 3:
        return "LOW"
    elif impact_score < 10:
        return "MEDIUM"
    else:
        return "HIGH"
```

**Complexity:** O(1)

---

## Data Structures

### Input Contract
```python
@dataclass
class Task:
    task_id: str
    depends_on: list[str]

@dataclass
class ConstraintResult:
    task_id: str
    is_valid: bool
    unsatisfied_dependencies: list[str]

@dataclass
class PropagationResult:
    task_id: str
    affected_tasks: list[str]
    impact_score: int

@dataclass
class InputContract:
    trace_id: str
    execution_id: str
    tasks: list[Task]
    constraint_results: list[ConstraintResult]
    propagation_results: list[PropagationResult]
```

---

### Output Contract
```python
@dataclass
class OutputContract:
    trace_id: str
    execution_id: str
    root_cause: str | None
    resolution_signal: str | None
    impact_score: int
    severity: str  # "LOW" | "MEDIUM" | "HIGH"
    timestamp: str  # ISO8601
```

---

## Performance Characteristics

### Time Complexity
| Phase | Complexity | Notes |
|-------|------------|-------|
| Validation | O(1) | Constant-time checks |
| Blocked Task Detection | O(n) | Linear scan |
| Root Cause Tracing | O(n × m) | BFS traversal |
| Bottleneck Detection | O(n) | Linear scan |
| Action Generation | O(1) | Constant-time lookup |
| Output Structuring | O(1) | Constant-time assembly |
| **Total** | **O(n × m)** | Dominated by root cause tracing |

**Where:**
- n = number of tasks
- m = average dependency depth

---

### Space Complexity
| Component | Complexity | Notes |
|-----------|------------|-------|
| Input data | O(n) | Task graph |
| Blocked tasks | O(n) | Worst case: all blocked |
| Root causes | O(n) | One per blocked task |
| Visited set | O(n) | BFS cycle detection |
| Queue | O(n) | BFS traversal |
| **Total** | **O(n)** | Linear space |

---

### Benchmarks (Expected)
| Metric | Value | Notes |
|--------|-------|-------|
| Throughput | 100-500 req/s | Per pod (4 workers) |
| Latency (p50) | <50ms | Typical case |
| Latency (p95) | <100ms | Under normal load |
| Latency (p99) | <200ms | Under normal load |
| Memory | 128-256 Mi | Per pod |
| CPU | 100-250m | Per pod |

---

## Determinism Guarantees

### Sources of Determinism
1. **Sorted outputs** — `sorted(blocked_tasks)` ensures consistent ordering
2. **Lexicographic tie-break** — `min(candidates)` for bottleneck selection
3. **BFS traversal** — `visited` set ensures consistent cycle handling
4. **Hardcoded severity** — No adaptive thresholds
5. **Trace ID passthrough** — No generation, no mutation

### No Sources of Non-Determinism
- ❌ No random number generation
- ❌ No system time (except timestamp, excluded from replay comparison)
- ❌ No network calls
- ❌ No file I/O
- ❌ No global mutable state
- ❌ No adaptive behavior

### Validation
**Test:** `test_determinism_*` (9 scenarios × 10 runs = 90 outputs)  
**Result:** 90/90 identical outputs (excluding timestamp)

---

## Failure Modes

### Input Validation Failures
| Failure | Rejection Signature | HTTP Status |
|---------|---------------------|-------------|
| Missing `trace_id` | `INVALID_INPUT_CONTRACT` | 400 |
| Missing `execution_id` | `INVALID_INPUT_CONTRACT` | 400 |
| Wrong type `trace_id` | `INVALID_INPUT_CONTRACT` | 400 |
| Wrong type `execution_id` | `INVALID_INPUT_CONTRACT` | 400 |
| Non-dict input | `INVALID_INPUT_CONTRACT` | 400 |
| Malformed `tasks` | `INVALID_INPUT_CONTRACT` | 400 |
| Malformed `constraint_results` | `INVALID_INPUT_CONTRACT` | 400 |
| Malformed `propagation_results` | `INVALID_INPUT_CONTRACT` | 400 |

---

### Downstream Failures
| Failure | Rejection Signature | HTTP Status |
|---------|---------------------|-------------|
| RAJYA trace mismatch | `RAJYA_TRACE_MISMATCH` | 400 |
| Sarathi exception | `SARATHI_FAILURE` | 400 |
| Core exception | `CORE_FAILURE` | 400 |

---

### Edge Cases
| Case | Behavior |
|------|----------|
| No blocked tasks | `root_cause: null`, `resolution_signal: null`, `severity: LOW` |
| All tasks blocked | Highest impact score wins bottleneck |
| Circular dependency | `visited` set breaks loop, deterministic output |
| Self dependency | `visited` set breaks loop, `root_cause = task_id` |
| Missing dependency | Missing task ID returned as root cause |
| Disconnected components | Bottleneck's root cause wins top-level |

---

## Security Considerations

### Input Validation
- **Fail-closed** — Invalid input → immediate rejection
- **No silent repair** — No auto-correction, no default values
- **Max request size** — 1 MB default (configurable via `MAX_CONTENT_MB`)

### Container Security
- **Non-root user** — UID 1000
- **Read-only filesystem** — No write access
- **No privilege escalation** — `allowPrivilegeEscalation: false`
- **Capabilities dropped** — `drop: [ALL]`

### Network Security
- **Firewall rules** — 5000/tcp only
- **TLS termination** — Via reverse proxy (Nginx, Traefik, Ingress)
- **No outbound calls** — Stateless, no external dependencies

---

## Deployment Architecture

### Docker
```dockerfile
FROM python:3.10-slim
USER keshav
WORKDIR /app
COPY analyzer/ tantra/ api.py ./
CMD ["gunicorn", "api:app", "--workers", "4", "--bind", "0.0.0.0:5000"]
```

---

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keshav-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: keshav
        image: keshav:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

### Horizontal Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: keshav-hpa
spec:
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring & Observability

### Prometheus Metrics
- `keshav_requests_total` — Counter
- `keshav_request_errors_total` — Counter
- `keshav_request_success_rate` — Gauge
- `keshav_request_latency_seconds{quantile}` — Summary
- `keshav_unique_traces_total` — Counter
- `keshav_severity_total{severity}` — Counter

### Grafana Dashboard
- Request rate (time series)
- Error rate (time series)
- Latency (p50, p95, p99)
- Success rate (single stat)
- Severity distribution (pie chart)
- Unique traces processed (single stat)

### Alerting Rules
1. Service down (critical)
2. High error rate >20% (critical)
3. High error rate >5% (warning)
4. High latency >5s (critical)
5. High latency >1s (warning)
6. Pod restarting (warning)
7. High memory usage >85% (warning)
8. High CPU usage >85% (warning)

---

## Testing Strategy

### Unit Tests (123 tests)
- **Phase 1** — Blocked task detection (8 tests)
- **Phase 2** — Root cause tracing (9 tests)
- **Phase 3** — Bottleneck detection (9 tests)
- **Phase 5** — Output structuring (13 tests)
- **Phase 6** — Action generation (11 tests)
- **Phase 7** — Validation (9 tests)
- **Phase 8** — Determinism (10 tests)
- **TANTRA convergence** — (24 tests)
- **Production hardening** — (13 tests)

### Coverage
- **analyzer/**: 100%
- **tantra/**: 100%
- **Total**: 100%

### Determinism Tests
- 9 scenarios × 10 runs = 90 outputs
- All 90 outputs byte-for-byte identical (excluding timestamp)

### Corruption Tests
- 12 attack vectors
- All rejected with deterministic signatures

---

## Integration Points

### Upstream: SETU
**Provides:** Input contract (trace_id, execution_id, tasks, constraint_results, propagation_results)  
**Contract:** Must include valid `trace_id` and `execution_id`

### Downstream: RAJYA
**Consumes:** KESHAV output contract (zero transformation)  
**Contract:** Same object reference returned

### Downstream: Sarathi
**Consumes:** RAJYA output (resolution_signal)  
**Contract:** Converts signal to enforcement action

### Downstream: Core
**Consumes:** Sarathi output (action)  
**Contract:** Executes action

### Downstream: Bucket
**Consumes:** Core output (write-on-success)  
**Contract:** Persists truth only on successful execution

### Lateral: InsightFlow
**Observes:** KESHAV execution (read-only)  
**Contract:** Emits structured events (EXECUTION, FAILURE)

---

## Code Quality

### Linting (Ruff)
```bash
make lint
# ruff check analyzer tantra tests api.py
```

### Formatting (Ruff)
```bash
make format
# ruff format analyzer tantra tests api.py
```

### Type Checking (Mypy)
```bash
make typecheck
# mypy analyzer
```

### Full Check
```bash
make check
# lint + typecheck + coverage
```

---

## Development Workflow

### Local Development
```bash
pip install -e ".[dev]"
python api.py
```

### Run Tests
```bash
make test
```

### Run with Coverage
```bash
make coverage
```

### Production Build
```bash
make docker-build
make docker-run
```

---

## Troubleshooting

### High Latency
**Diagnosis:**
```bash
curl http://localhost:5000/metrics/json | jq '.p95_latency_seconds'
```

**Resolution:**
- Increase workers: `--workers 8`
- Scale horizontally: `kubectl scale deployment keshav-api --replicas=10`

---

### High Error Rate
**Diagnosis:**
```bash
docker logs keshav-api | grep ERROR
```

**Resolution:**
- Check upstream SETU input
- Validate input contract
- Check downstream service health

---

### Memory Leak
**Diagnosis:**
```bash
docker stats keshav-api
```

**Resolution:**
- Enable worker restart: `--max-requests 1000`
- Check Bucket/InsightFlow bounded storage

---

## References

### Documentation
- **REVIEW_PACKET.md** — Full contract specification
- **DEPLOYMENT.md** — Production deployment guide
- **RUNBOOK.md** — Incident response playbook
- **MAINTAINER_FAQ.md** — 50 Q&A

### Code
- **analyzer/** — KESHAV core logic
- **tantra/** — TANTRA ecosystem layers
- **api.py** — Flask API
- **metrics.py** — Prometheus metrics

---

**Prepared for technical review and engineering handover.**
