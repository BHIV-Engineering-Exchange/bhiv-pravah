# 🔐 Insight Core Quick Reference

## Start Services (Correct Order)

```bash
# Terminal 1: Karma
cd "karma_chain_v2-main"
python main.py

# Terminal 2: Bucket
cd "BHIV_Central_Depository-main"
python main.py

# Terminal 3: Core
cd "v1-BHIV_CORE-main"
python mcp_bridge.py

# Terminal 4: Workflow
cd "workflow-executor-main"
python main.py

# Terminal 5: UAO
cd "Unified Action Orchestration"
python action_orchestrator.py

# Terminal 6: Insight Core [NEW]
cd "insightcore-bridgev4x-main"
python insight_service.py
```

## Health Checks

```bash
curl http://localhost:8000/health  # Karma
curl http://localhost:8001/health  # Bucket
curl http://localhost:8002/health  # Core
curl http://localhost:8003/healthz # Workflow
curl http://localhost:8004/docs    # UAO
curl http://localhost:8005/health  # Insight Core [NEW]
```

## Test Insight Core

```bash
python test_insight_integration.py
```

Expected: 6/6 tests passing (100%)

## Insight Core Features

- **JWT Validation**: Ensures authenticated requests
- **Replay Protection**: Prevents duplicate requests
- **Fail-Closed**: Rejects invalid requests
- **Telemetry**: Logs all security decisions

## Architecture

```
Core → Insight Core → Bucket
       [JWT Check]
       [Nonce Check]
```

## Ports

- Karma: 8000
- Bucket: 8001
- Core: 8002
- Workflow: 8003
- UAO: 8004
- Insight: 8005 [NEW]

## Status

✅ 7-Pillar Integration Complete
✅ Security Layer Active
✅ All Services Operational
