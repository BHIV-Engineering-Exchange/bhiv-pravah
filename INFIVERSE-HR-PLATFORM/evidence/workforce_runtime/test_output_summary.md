# Test Output Summary

Date: 2026-06-08  
Repository: `INFIVERSE-HR-PLATFORM`  
Gateway: `https://bhiv-hr-gateway-l0xp.onrender.com`  
Status: `live_capture`

## Live Production Capture

- **correlation_id:** 9a83b441-e387-4e26-aeb2-2616e86d2762
- **org_id:** 6a26664c88b72534dc0c06ab
- **trace_id:** f6f72b52-57ed-4ddf-a5c1-43379364c180
- **niyantran signal_id:** sig-f25fd8f6c7bb
- **artha signal_id:** sig-0edf86a54492
- **captured_at:** 2026-06-08T06:50:43.132018+00:00

## Commands

1. Live workforce + SETU sequence against production gateway (Task 20 P1 capture).
2. `python -m compileall backend/services/gateway/app backend/services/gateway/routes/workforce_governance_routes.py`
3. `python -m pytest -q backend/tests/gateway/test_workforce_governance_runtime.py backend/tests/gateway/test_workforce_lifecycle.py`

## Results

- Production gateway health: HTTP 200
- Workforce org → division → department → employee → hierarchy: all HTTP 200
- SETU niyantran + artha signals + trace continuity: all HTTP 200
- Compile step: success for gateway app modules and `workforce_governance_routes.py`.
- Unit tests: **12 passed**.
- Warnings: unknown pytest mark `e2e_unit`; upstream deprecation warning in dependency import path.

## Conclusion

Workforce governance live capture completed against production Render gateway. Evidence files use real IDs and `live_capture` status. Unit baseline remains passing with no failing tests.
