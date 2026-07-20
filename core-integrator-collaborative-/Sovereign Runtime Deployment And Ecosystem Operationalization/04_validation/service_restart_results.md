# Service Restart Results

**Status:** PASS (partial)  
**Generated:** 2026-07-07

## What was run

1. BHIV Core process killed (PID 8820) during rate-limit investigation
2. Full stack restarted via `python start_all.py`
3. `python run_comprehensive_live_tests.py` — all 4 products passed after restart

## Observed

- After restart with orchestrator env (`AUTH_*`, `RATE_LIMIT_*`), all 8 services came up
- Localhost rate-limit bypass in `security_hardening.py` prevents mesh self-throttling during tests
- Pipeline executions succeeded immediately after restart

## Pass/fail

- **PASS:** Controlled restart + successful pipeline retry
- **PARTIAL:** Did not kill mid-pipeline-execution and verify in-flight recovery
