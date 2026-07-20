# Node Interruption Results

**Status:** partial — rate-limit failure observed, not full SIGKILL test  
**Generated:** 2026-07-07

## Observed behavior (live)

During comprehensive burst testing, BHIV Core returned **429 Too Many Requests** mid-pipeline:

```
429 Client Error: Too Many Requests for url: http://127.0.0.1:8001/core
```

Affected traces: `comp_ttg_bca6477faa`, `comp_gurukul_8934d450a8`

Integration Bridge surfaced this as HTTP 500 to the caller. No partial artifacts were corrupted; pipeline aborted before A3 execution.

## Full SIGKILL interruption

Not demonstrated in this session (requires controlled process kill mid-request).

## Pass/fail

- **PASS:** Pipeline fails safely on BHIV unavailability (no silent success)
- **NOT RUN:** Full node kill + recovery scenario
