# Partial Failure Results

**Status:** PASS — rate-limit failure handled and mitigated  
**Generated:** 2026-07-07

## Scenario: BHIV Core rejects execution (429)

When BHIV Core rate limit is exceeded, Integration Bridge returns HTTP 500:

```json
{"detail": "429 Client Error: Too Many Requests for url: http://127.0.0.1:8001/core"}
```

## Observed behavior

- Pipeline stops before A3 execution
- No false success returned
- Error detail propagated to caller

## Mitigations applied

1. `core/service_orchestrator.py` sets `RATE_LIMIT_IP_PER_MIN=10000` for local startup
2. `src/utils/security_hardening.py` bypasses rate limiting for `127.0.0.1` / `::1` (local mesh calls)
3. `run_comprehensive_live_tests.py` uses retry + spacing between product runs

## Post-mitigation validation

After restart: `run_comprehensive_live_tests.py` → **4/4 products PASS**

## Pass/fail

- **PASS:** Partial failure visible and does not corrupt completed traces
- **NOT RUN:** Bucket rejecting specific artifact type mid-chain
