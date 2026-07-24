# KESHAV Review Packet

**Owner:** Rajaryan Verma
**Date:** 2026-06-24
**Sprint:** KESHAV Convergence Sprint (Phases 1-6)
**State:** FULLY CERTIFIED — Sovereign Capability Published

---

## 1. Entry Point

**File:** `analyzer/analyze_blockage.py` → `analyze_and_recommend(input_data: dict) -> dict`

This is the single entry point for all KESHAV computation. It accepts a structured input contract and returns a TANTRA-compliant output contract. There is no other execution path.

**API Entry Point:** `api.py` → `POST /analyze`

The Flask server at `api.py` receives HTTP requests, extracts JSON, calls `tantra.pipeline.run_tantra_pipeline()`, which calls `analyze_and_recommend()`, then returns the result.

---

## 2. Core Execution Flow

```
analyze_and_recommend(input_data)
  │
  ├─ _validate(input_data)
  │   └─ Fail-closed: returns {"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT"}
  │
  ├─ Phase 1: detect_blocked_tasks(constraint_results)
  │   └─ Returns list of task_ids where is_valid=False
  │
  ├─ Phase 2: trace_root_causes(blocked_ids, tasks, constraints)
  │   └─ BFS traversal anchored to unsatisfied_dependencies
  │
  ├─ Phase 3: detect_bottleneck(blocked_ids, propagation_results)
  │   └─ Finds highest-impact task (sorted for determinism)
  │
  ├─ Phase 4: generate_actions(root_causes, bottleneck, ...)
  │   └─ Emits UNBLOCK_DEPENDENCY resolution signals
  │
  └─ Phase 5: structure_output(trace_id, execution_id, ...)
      └─ Assembles TANTRA-compliant output dict with timestamp
```

**Key files:**

| File | Phase | Purpose |
|------|-------|---------|
| `analyzer/analyze_blockage.py` | Entry | Orchestrates all 5 phases |
| `analyzer/blocked_task_detector.py` | 1 | Detect blocked tasks |
| `analyzer/root_cause_tracer.py` | 2 | BFS root cause tracing |
| `analyzer/bottleneck_detector.py` | 3 | Bottleneck detection |
| `analyzer/action_generator.py` | 4 | Resolution signal generation |
| `analyzer/output_structurer.py` | 5 | Output assembly |

---

## 3. Live Runtime Flow

```
Client → HTTP POST /analyze → api.py
  → tantra.pipeline.run_tantra_pipeline(input_data)
    → KESHAV:      analyzer.analyze_and_recommend(input_data)
    → InsightFlow:  tantra.insightflow.emit(keshav_output)       [read-only]
    → RAJYA:        tantra.rajya.consume(keshav_output, trace_id) [zero-transform]
    → Sarathi:      tantra.sarathi.enforce(rajya_output)
    → Core:         tantra.core.execute(sarathi_output)
    → Bucket:       tantra.bucket.write(core_output, keshav_output)
  → return keshav_output as JSON (HTTP 200)
```

On any failure, the chain halts. No downstream layers are invoked. No Bucket write occurs. HTTP 400 is returned.

---

## 4. Integration Flow

```
SETU/Input ──→ KESHAV ──→ RAJYA ──→ Sarathi ──→ Core ──→ Bucket
                  │
                  └──→ InsightFlow (side-channel, read-only)
```

**Integration Rules:**
- `trace_id` is byte-identical across all layers (verified by 54 assertions)
- RAJYA performs zero-transformation (same Python object reference)
- Sarathi reads `resolution_signal` and emits `ENFORCE:<signal>` actions
- Core executes the action and marks `executed=True`
- Bucket persists `{trace_id, keshav_output, core_output}` — write-only on success
- InsightFlow emits structured events — never mutates the payload

**KESHAV does NOT own:**
- Decision authority (RAJYA)
- Enforcement authority (Sarathi)
- Execution authority (Core)
- Persistence authority (Bucket)
- Observability logic (InsightFlow)

---

## 5. Replay Flow

KESHAV is 100% deterministically replayable:
- Same input → same output (excluding passive `timestamp` field)
- Verified: 10 runs × 3 input classes → all SHA-256 hashes identical
- Enforced structurally: `sorted()`, lexicographical tie-breakers, function-scoped stateless, zero global state, zero randomness

**Proof:** `replay_determinism_proof.py` → 34/34 assertions passed.

---

## 6. Failure Modes

| Mode | Trigger | HTTP | Response |
|------|---------|------|----------|
| Missing `trace_id` | Input contract violation | 400 | `{"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": ""}` |
| Missing `execution_id` | Input contract violation | 400 | Same as above |
| Non-dict input | Type violation | 400 | Same as above |
| `tasks` not a list | Type violation | 400 | Same as above |
| `trace_id` not a string | Type violation | 400 | Same as above |
| Invalid JSON | Parse failure | 400 | `{"status": "FAIL", "reason": "INVALID_JSON", "trace_id": ""}` |
| Wrong Content-Type | Media type mismatch | 415 | `{"status": "FAIL", "reason": "UNSUPPORTED_MEDIA_TYPE", "trace_id": ""}` |
| Wrong HTTP method | Method mismatch | 405 | `{"status": "FAIL", "reason": "METHOD_NOT_ALLOWED", "trace_id": ""}` |
| Unknown endpoint | Route mismatch | 404 | `{"status": "FAIL", "reason": "NOT_FOUND", "trace_id": ""}` |
| Request too large | Body > MAX_CONTENT_MB | 413 | `{"status": "FAIL", "reason": "REQUEST_TOO_LARGE", "trace_id": ""}` |

**All failures fail closed.** No partial execution. No Bucket writes. No downstream propagation.

---

## 7. Proof Artifacts

| Artifact | Assertions | Script |
|----------|-----------|--------|
| Unit tests | 123 passed, 100% coverage | `python -m pytest tests/` |
| TANTRA wiring | 54/54 | `python tantra_wiring_proof.py` |
| Replay determinism | 34/34 | `python replay_determinism_proof.py` |
| Production hardening | 94/94 | `python production_hardening_proof.py` |
| End-to-end proofs | N/A | `python run_proofs.py` |
| Production validation | 6 checks | `python validate_production.py` |
| Lint | 0 violations | `python -m ruff check analyzer tantra tests api.py metrics.py` |
| Type check | 0 issues | `python -m mypy analyzer` |

**Total automated assertions: 305 — all passing.**

**Proof documents:**
- `END_TO_END_PROOF.md`
- `TANTRA_WIRING_PROOF.md`
- `REPLAY_DETERMINISM_PROOF.md`
- `PRODUCTION_HARDENING_PROOF.md`

**Ecosystem Convergence Certification Deliverables (Phases 1-6):**
- `ECOSYSTEM_PARTICIPANT_REGISTRY.md`
- `RUNTIME_ATTACHMENT_AUDIT.md`
- `LIVE_ECOSYSTEM_EXECUTION_PROOF.md`
- `AUTHORITY_BOUNDARY_CERTIFICATION.md`
- `TRUTH_LAYER_MATURITY_REPORT.md`
- `KESHAV_ECOSYSTEM_CONVERGENCE_PACKET.md`
- `ECOSYSTEM_CERTIFICATION_EVIDENCE.txt` (Testing Output)
- `ecosystem_certification_test.py` (Testing Package for Testing Department)

**Capability Publication Deliverables:**
- `capability/KESHAV_CAPABILITY.md`
- `capability/SERVICE_CONTRACT.md`
- `capability/CAPABILITY_REGISTRY.md`
- `capability/SEMANTIC_REGISTRY.md`
- `capability/SCHEMA_REGISTRY.md`
- `capability/CAPABILITY_CERTIFICATION_PACKET.md`
- `capability/MULTI_CONSUMER_INTEGRATION_EVIDENCE.txt` (Integration Proof Output)
- `capability/VINAYAK_TESTING_PACKAGE.md` (Testing Package for Vinayak)

---

## 8. Deployment Instructions

**Quick start:**
```bash
pip install -e ".[dev]"
python api.py
# → http://127.0.0.1:5000
```

**Production:**
```bash
gunicorn "api:app" --workers 4 --bind 0.0.0.0:5000 --timeout 30
```

**Docker:**
```bash
docker build -t keshav:latest .
docker run -d --name keshav-api -p 5000:5000 keshav:latest
```

**Kubernetes:**
```bash
kubectl apply -f k8s-deployment.yaml
```

Full details: `KESHAV_DEPLOYMENT_GUIDE.md`

---

## 9. Environment Setup

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5000` | Listening port |
| `DEBUG` | `false` | Flask debug mode |
| `MAX_CONTENT_MB` | `1` | Max request body size |
| `WORKERS` | `4` | Gunicorn workers |

Template: `.env.example`

---

## 10. Rollback Procedure

**Kubernetes:**
```bash
kubectl rollout undo deployment/keshav-api -n keshav
```

**Docker:**
```bash
docker stop keshav-api && docker rm keshav-api
docker run -d --name keshav-api -p 5000:5000 keshav:previous
```

**Git:**
```bash
git revert <commit-hash>
pip install -e .
```

Full details: `KESHAV_DEPLOYMENT_GUIDE.md` → Rollback Procedure section.

---

## 11. Known Limitations

1. **In-memory Bucket/InsightFlow.** State lost on restart. Recovery by replay.
2. **Single-process Bucket.** Each Gunicorn worker/container has its own instance.
3. **No authentication.** Secure via network-level controls.
4. **No rate limiting.** Use reverse proxy.
5. **PATH dependency.** `ruff`/`mypy` may need `python -m` prefix.

---

## 12. Future Work

1. **Persistent Bucket** — Redis or PostgreSQL for cross-process persistence.
2. **Authentication** — API key or JWT.
3. **Rate limiting** — Flask-Limiter or API gateway.
4. **Distributed tracing** — OpenTelemetry integration.
5. **CI/CD pipeline** — Automated test + lint + deploy.
6. **Shared Bucket** — Cross-replica state via Redis.
