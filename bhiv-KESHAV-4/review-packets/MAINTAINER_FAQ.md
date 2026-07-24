# MAINTAINER FAQ — KESHAV

**For:** Rajaryan Verma (Incoming Steward) and Future Maintainers  
**Last Updated:** 2025-01-XX  
**Status:** Operational Freeze Preparation

---

## General Questions

### Q1: What is KESHAV?
**A:** KESHAV is a **dependency intelligence participation layer** within the TANTRA ecosystem. It analyzes task dependencies, identifies root causes of blockages, and produces structured recommendations for downstream execution layers.

**Key Point:** KESHAV is NOT an execution engine, orchestrator, or decision authority. It is a **signal producer only**.

---

### Q2: What does KESHAV own?
**A:** KESHAV owns **ZERO authority**:
- ❌ No execution authority
- ❌ No decision authority
- ❌ No enforcement authority
- ❌ No truth authority
- ❌ No observability authority

KESHAV only produces **TANTRA output contract** for downstream consumption.

---

### Q3: What is the TANTRA output contract?
**A:** The TANTRA output contract is a structured JSON response:
```json
{
  "trace_id": "<trace_id>",
  "execution_id": "<execution_id>",
  "root_cause": "<task_id>",
  "resolution_signal": "UNBLOCK_DEPENDENCY:<task_id>",
  "impact_score": <int>,
  "severity": "<LOW|MEDIUM|HIGH>",
  "timestamp": "<ISO8601>"
}
```

This contract is consumed by RAJYA (decision layer) without transformation.

---

### Q4: What is the input contract?
**A:** KESHAV requires:
- `trace_id` (string, required)
- `execution_id` (string, required)
- `tasks` (list, required)
- `constraint_results` (list, required)
- `propagation_results` (list, required)

Missing or wrong-type fields → fail closed with `INVALID_INPUT_CONTRACT`.

---

### Q5: What does "fail-closed" mean?
**A:** Fail-closed means:
- Invalid input → immediate rejection
- No downstream execution
- No partial truth persistence
- Visible rejection reasoning (InsightFlow FAILURE event)

**No silent repair, no partial execution.**

---

## Architecture Questions

### Q6: What are the TANTRA layers?
**A:**
```
SETU/Input
  → KESHAV  (analyzer/)         — dependency intelligence
  → RAJYA   (tantra/rajya.py)   — decision layer
  → Sarathi (tantra/sarathi.py) — enforcement layer
  → Core    (tantra/core.py)    — execution layer
  → Bucket  (tantra/bucket.py)  — truth layer

InsightFlow (tantra/insightflow.py) — observability layer
Pipeline    (tantra/pipeline.py)    — orchestration layer
```

---

### Q7: What is RAJYA's role?
**A:** RAJYA is the **execution decision authority**. It consumes KESHAV output and decides whether to proceed with execution.

**Key Point:** RAJYA performs **zero transformation** on KESHAV output. It returns the same object reference.

---

### Q8: What is Sarathi's role?
**A:** Sarathi is the **enforcement authority**. It converts RAJYA's decision into executable actions.

**Example:** `resolution_signal: "UNBLOCK_DEPENDENCY:T1"` → `action: "ENFORCE:UNBLOCK_DEPENDENCY:T1"`

---

### Q9: What is Core's role?
**A:** Core is the **execution authority**. It executes actions approved by Sarathi.

**Key Point:** KESHAV has **no direct interaction** with Core.

---

### Q10: What is Bucket's role?
**A:** Bucket is the **truth authority**. It persists execution state on successful Core execution.

**Key Point:** Bucket writes are **write-on-success only**. Failed runs are NOT stored.

---

### Q11: What is InsightFlow's role?
**A:** InsightFlow is the **observability authority**. It emits structured events for external visibility.

**Key Point:** InsightFlow is **read-only**. It does NOT mutate KESHAV output or trigger execution.

---

## Operational Questions

### Q12: How do I run KESHAV locally?
**A:**
```bash
pip install -e ".[dev]"
python api.py
```

Then:
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d @sample_input.json
```

---

### Q13: How do I run KESHAV in production?
**A:**
```bash
pip install -e ".[dev]"
make run-prod
# gunicorn "api:app" --workers 4 --bind 0.0.0.0:5000
```

**Do NOT use `python api.py` in production** — Flask dev server is not production-safe.

---

### Q14: How do I run tests?
**A:**
```bash
make test        # run all tests
make coverage    # tests + coverage report (≥90% required)
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make check       # lint + typecheck + coverage
```

---

### Q15: What is the test coverage requirement?
**A:** **≥90% coverage** for `analyzer/` and `tantra/`.

Current coverage: **100%** (123 tests passing).

---

### Q16: How do I validate replay consistency?
**A:** Run:
```bash
pytest tests/test_phase8.py -v
```

This runs 10 identical inputs and asserts byte-for-byte identical outputs (excluding timestamp).

**Expected:** 10/10 identical outputs across 9 scenarios.

---

### Q17: How do I validate corruption resistance?
**A:** Run:
```bash
pytest tests/test_tantra_convergence.py::test_failure_* -v
```

This injects corrupted inputs and asserts fail-closed behavior.

**Expected:** All corruption tests pass with deterministic rejection signatures.

---

## Code Review Questions

### Q18: What changes are allowed?
**A:**
- Bug fixes (no behavioral changes)
- Performance optimizations (determinism preserved)
- Documentation updates
- Test coverage improvements

---

### Q19: What changes are prohibited?
**A:**
- Adaptive behavior (dynamic thresholds, feedback loops)
- Global mutable state
- Orchestration logic bypassing RAJYA
- Execution authority accumulation
- Observability mutation

---

### Q20: How do I review a PR?
**A:** Use this checklist:
- [ ] No adaptive behavior
- [ ] No global mutable state
- [ ] No orchestration logic bypassing RAJYA
- [ ] No execution authority accumulation
- [ ] No observability mutation
- [ ] Replay validation tests pass
- [ ] Corruption injection tests pass
- [ ] Coverage ≥90%

---

### Q21: What if a PR introduces non-determinism?
**A:** **REJECT immediately.**

Non-determinism breaks replay-safety. Run:
```bash
pytest tests/test_phase8.py -v
```

If any test fails → PR is rejected.

---

### Q22: What if a PR bypasses RAJYA?
**A:** **REJECT immediately.**

RAJYA is the execution decision authority. KESHAV must NOT trigger execution directly.

---

### Q23: What if a PR mutates InsightFlow events?
**A:** **REJECT immediately.**

InsightFlow is read-only observability. It must NOT mutate KESHAV output or trigger execution.

---

## Debugging Questions

### Q24: How do I debug a replay inconsistency?
**A:**
1. Retrieve InsightFlow events for incident `trace_id`
2. Replay KESHAV with original input
3. Compare replayed output with original output
4. If mismatch: investigate non-deterministic code (random, time, network, file I/O)

---

### Q25: How do I debug a corruption injection?
**A:**
1. Retrieve InsightFlow FAILURE events
2. Identify rejection signature (`INVALID_INPUT_CONTRACT`, `RAJYA_TRACE_MISMATCH`, etc.)
3. Validate fail-closed behavior (no partial execution)
4. If partial execution: investigate validation bypass

---

### Q26: How do I debug an authority accumulation?
**A:**
1. Review recent PRs for adaptive behavior
2. Validate constitutional boundaries (`review-packets/CONSTITUTIONAL_BOUNDARIES.md`)
3. Run authority isolation tests (`pytest tests/test_tantra_convergence.py -v`)
4. If authority accumulation: revert offending PR

---

### Q27: How do I debug an observability mutation?
**A:**
1. Review InsightFlow event emission code
2. Validate read-only guarantee (`test_insightflow_does_not_mutate_keshav_output`)
3. Run observability integrity tests (`pytest tests/test_tantra_convergence.py -v`)
4. If mutation detected: revert offending PR

---

## Monitoring Questions

### Q28: What should I monitor in production?
**A:**
- **InsightFlow event volume** — monitor for unbounded growth
- **Bucket entry count** — monitor for OOM risk
- **Replay consistency** — validate after incidents
- **Corruption rejection rate** — monitor for attack patterns

---

### Q29: What are the bounded storage limits?
**A:**
- **InsightFlow:** `MAX_EVENTS = 10_000` with oldest-eviction
- **Bucket:** `MAX_ENTRIES = 50_000` with oldest-eviction

---

### Q30: How do I retrieve InsightFlow events?
**A:**
```python
from tantra.insightflow import insightflow

events = insightflow.get_events()
for event in events:
    print(event)
```

---

### Q31: How do I retrieve Bucket truth?
**A:**
```python
from tantra.bucket import bucket

entry = bucket.read("trace-id-001")
if entry:
    print(entry["keshav_output"])
    print(entry["core_output"])
```

---

## Incident Response Questions

### Q32: What if KESHAV produces inconsistent outputs?
**A:**
1. Run replay validation tests (`pytest tests/test_phase8.py -v`)
2. If tests fail: investigate non-deterministic code
3. If tests pass: investigate input mutation or external state

---

### Q33: What if KESHAV fails to reject corrupted input?
**A:**
1. Run corruption injection tests (`pytest tests/test_tantra_convergence.py::test_failure_* -v`)
2. If tests fail: investigate validation bypass
3. If tests pass: investigate input source corruption

---

### Q34: What if KESHAV accumulates authority?
**A:**
1. Review recent PRs for adaptive behavior
2. Run authority isolation tests (`pytest tests/test_tantra_convergence.py -v`)
3. If tests fail: revert offending PR
4. If tests pass: investigate downstream layer changes

---

### Q35: What if InsightFlow mutates KESHAV output?
**A:**
1. Run observability integrity tests (`pytest tests/test_tantra_convergence.py -v`)
2. If tests fail: revert offending PR
3. If tests pass: investigate external mutation

---

## Governance Questions

### Q36: What is "governance drift"?
**A:** Governance drift occurs when a coordination system silently accumulates authority through:
- Adaptive behavior (dynamic thresholds, feedback loops)
- Hidden coordination state (caches, retained semantics)
- Observability mutation (events influencing execution)

**KESHAV must remain governance-neutral.**

---

### Q37: How do I prevent governance drift?
**A:**
- **Reject** adaptive behavior
- **Reject** global mutable state
- **Reject** orchestration logic bypassing RAJYA
- **Enforce** constitutional boundaries
- **Validate** replay consistency

---

### Q38: What is "constitutional convergence"?
**A:** Constitutional convergence means KESHAV operates within explicit boundaries:
- No execution authority
- No decision authority
- No enforcement authority
- No truth authority
- No observability authority

**KESHAV is a signal producer only.**

---

### Q39: What is "replay-safe convergence"?
**A:** Replay-safe convergence means:
- Same input → byte-for-byte identical output (excluding timestamp)
- Deterministic algorithms only
- No hidden state
- No adaptive behavior

**KESHAV guarantees deterministic replay.**

---

### Q40: What is "corruption resistance"?
**A:** Corruption resistance means:
- Invalid input → fail closed
- No silent repair
- No partial execution
- Visible rejection reasoning

**KESHAV rejects all corruption immediately.**

---

## Handover Questions

### Q41: Who was the previous architect?
**A:** Pritesh (KESHAV Architect)

---

### Q42: Who is the incoming steward?
**A:** Rajaryan Verma (Runtime Stewardship Layer)

---

### Q43: Who are the integration partners?
**A:**
- **Kanishk Singh** — Replay Governance + Validation Layer
- **Akanksha Parab** — Sarathi Enforcement Layer
- **RAJYA/Core Team** — Decision + Execution Layer
- **InsightFlow Team** — Observability Layer
- **Bucket Team** — Truth Layer

---

### Q44: Where is the full documentation?
**A:** `review-packets/` directory:
- `REVIEW_PACKET.md` — Full contract specification
- `CONSTITUTIONAL_BOUNDARIES.md` — Authority boundaries
- `DISTRIBUTED_REPLAY_VALIDATION.md` — Replay proof
- `CORRUPTION_INJECTION_PROOF.md` — Corruption resistance
- `OBSERVABILITY_INTEGRITY.md` — InsightFlow validation
- `HIDDEN_STATE_DISCLOSURE.md` — Runtime state classification
- `AUTHORITY_ISOLATION_PROOF.md` — Downstream authority proof
- `OPERATIONAL_HANDOVER.md` — Stewardship guide
- `MAINTAINER_FAQ.md` — This document

---

### Q45: What is the convergence freeze status?
**A:** **KESHAV is constitutionally stable and ready for operational handover.**

No further capability expansion allowed without:
1. Constitutional boundary review
2. Distributed replay validation
3. Authority isolation proof
4. Governance drift assessment

---

## Final Notes

### Q46: What is the most important thing to remember?
**A:** **KESHAV is a signal producer, not an execution authority.**

All downstream layers (RAJYA, Sarathi, Core, Bucket, InsightFlow) retain their authority. KESHAV must NEVER bypass them.

---

### Q47: What should I do if I'm unsure about a change?
**A:**
1. Read `review-packets/CONSTITUTIONAL_BOUNDARIES.md`
2. Run full test suite (`make check`)
3. Validate replay consistency (`pytest tests/test_phase8.py -v`)
4. Consult integration partners (Kanishk, Akanksha, RAJYA/Core Team)

**When in doubt, reject the change.**

---

### Q48: How do I contact the previous architect?
**A:** Pritesh (KESHAV Architect) — handover date: 2025-01-XX

---

### Q49: How do I escalate an issue?
**A:** Contact:
- **Rajaryan Verma** — Runtime Stewardship Layer
- **Kanishk Singh** — Replay Governance + Validation Layer
- **Integration Partners** — RAJYA/Core Team, InsightFlow Team, Bucket Team

---

### Q50: What is the repository access policy?
**A:**
- **Repository:** Private
- **Access:** Restricted to `bh@blackholeinfiverse.com`

---

**Welcome to KESHAV stewardship. Maintain constitutional boundaries, enforce replay-safety, and reject governance drift.**
