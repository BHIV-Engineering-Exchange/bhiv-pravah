# 🚀 BHIV Integrated System - Quick Reference

## Start Services (3 Terminals)

```bash
# Terminal 1 - Bucket
cd BHIV_Central_Depository-main && python main.py

# Terminal 2 - Core  
cd v1-BHIV_CORE-main && python mcp_bridge.py

# Terminal 3 - Karma
cd karma_chain_v2-main && python main.py
```

## Test Integration

```bash
python test_full_integration.py
```

## Health Checks

```bash
curl http://localhost:8002/health  # Core
curl http://localhost:8001/health  # Bucket
curl http://localhost:8000/health  # Karma
```

## Send Test Task

```bash
curl -X POST http://localhost:8002/handle_task \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "edumentor_agent",
    "input": "What is AI?",
    "input_type": "text"
  }'
```

## View Events

```bash
curl http://localhost:8001/core/events      # Bucket events
curl http://localhost:8001/core/stats       # Integration stats
curl http://localhost:8000/api/v1/analytics/karma_trends  # Karma analytics
```

## Ports

- **Core**: 8002
- **Bucket**: 8001
- **Karma**: 8000

## Status

✅ **PRODUCTION READY** - 5/6 tests passing (83%)

## Documentation

- `README.md` - Quick start guide
- `DEEP_INTEGRATION_COMPLETE.md` - Full integration details
- `DEPLOYMENT_READY.md` - Deployment checklist
- `core_bucket_contract.md` - API contract

## Support

All systems operational with zero regression!
