# BHIV Core ↔ Bucket Integration Implementation

## 🎯 Integration Philosophy

**"Let the brain talk to the diary — but the diary must never control the brain."**

This integration connects BHIV Core (decision engine) to BHIV Bucket (memory store) using **fire-and-forget** communication that preserves Core's independence.

## 🏗️ Architecture Overview

```
BHIV Core (Port 8002)          BHIV Bucket (Port 8000)
┌─────────────────────┐        ┌─────────────────────┐
│  MCP Bridge         │        │  FastAPI Server     │
│  ┌───────────────┐  │        │  ┌───────────────┐  │
│  │ Bucket Client │──┼────────┼──│ Core Handler  │  │
│  └───────────────┘  │        │  └───────────────┘  │
│                     │        │                     │
│  Agent Processing   │        │  Constitutional     │
│  RL Context         │        │  Governance         │
│  Task Execution     │        │  Audit Trail        │
└─────────────────────┘        └─────────────────────┘
```

## 🔄 Data Flow

### Core → Bucket (Fire-and-Forget)
1. **RL Outcomes**: Agent rewards and performance metrics
2. **Agent Results**: Task execution results and metadata  
3. **Error Events**: Failed task information
4. **Context Updates**: Agent state changes

### Bucket → Core (Optional, Timeout-Based)
1. **Agent Context**: Historical performance summaries
2. **Karma Data**: Trust scores and behavioral flags

## 🛡️ Constitutional Safeguards

### Core Protection
- **Non-blocking**: Core continues if Bucket is offline
- **No dependencies**: Core logic unchanged
- **Fire-and-forget**: No waiting for Bucket responses
- **Graceful degradation**: Silent failures don't affect Core

### Bucket Governance  
- **Boundary enforcement**: All Core requests validated
- **API contract validation**: Schema compliance required
- **Audit trail**: Every interaction logged
- **Threat detection**: Malicious requests blocked

## 📁 Implementation Files

### Core Side (v1-BHIV_CORE-main/)
```
integration/
├── bucket_client.py      # Fire-and-forget client to Bucket
├── config.py            # Integration configuration
└── __init__.py

config/
└── settings.py          # Updated with Bucket config

mcp_bridge.py            # Updated with Bucket integration
```

### Bucket Side (BHIV_Central_Depository-main/)
```
integration/
├── core_handler.py      # Handles Core requests with governance
└── __init__.py

main.py                  # Updated with Core endpoints
```

## 🚀 Quick Start

### 1. Start Bucket (Terminal 1)
```bash
cd "BHIV_Central_Depository-main"
python main.py
# Bucket runs on http://localhost:8000
```

### 2. Start Core (Terminal 2)  
```bash
cd "v1-BHIV_CORE-main"
python mcp_bridge.py
# Core runs on http://localhost:8002
```

### 3. Test Integration
```bash
python test_integration.py
```

### 4. Run a Task Through Core
```bash
curl -X POST "http://localhost:8002/handle_task" \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "edumentor_agent",
    "input": "Test integration",
    "input_type": "text"
  }'
```

## 📊 Monitoring Integration

### Check Bucket Health
```bash
curl http://localhost:8000/health
```

### View Core Events in Bucket
```bash
curl http://localhost:8000/core/events
```

### Check Integration Stats
```bash
curl http://localhost:8000/core/stats
```

## 🔧 Configuration

### Environment Variables
```bash
# Core side
BUCKET_URL=http://localhost:8000
BUCKET_TIMEOUT=2.0
ENABLE_BUCKET_WRITES=true
ENABLE_BUCKET_READS=true

# Bucket side  
CORE_INTEGRATION_ENABLED=true
```

## 🎯 What This Achieves

### 1. Persistent Intelligence
- Core decisions are now stored permanently
- Historical context available for future decisions
- Complete audit trail of all AI operations

### 2. Demo-Ready System
- Live agent decisions visible in Bucket
- Historical performance data for presentations
- Real-time monitoring of AI behavior

### 3. Enterprise Compliance
- Full audit trail for regulatory requirements
- Governance enforcement on all operations
- Constitutional boundaries prevent misuse

### 4. Zero Risk Integration
- Core behavior unchanged
- No new dependencies
- Graceful degradation if Bucket fails

## 🔍 Integration Verification

### Core Sends Data to Bucket ✅
- RL outcomes automatically logged
- Agent results stored with metadata
- Error events tracked for debugging

### Bucket Enforces Governance ✅  
- Constitutional boundaries validated
- API contracts enforced
- Threat detection active

### Core Remains Independent ✅
- Continues working if Bucket offline
- No blocking calls to Bucket
- Original endpoints unchanged

### Optional Context Reading ✅
- Core can read historical context
- Timeouts prevent blocking
- Defaults to null if unavailable

## 🚨 Troubleshooting

### Core Can't Connect to Bucket
- Check Bucket is running on port 8000
- Verify BUCKET_URL in Core config
- Core continues normally without Bucket

### Bucket Rejects Core Requests
- Check Core identity in requests
- Verify constitutional boundaries
- Review governance gate logs

### Integration Not Working
- Run `python test_integration.py`
- Check both service health endpoints
- Verify environment variables

## 🎉 Success Criteria

✅ **Core operates independently** - Works with or without Bucket  
✅ **Fire-and-forget communication** - Non-blocking writes to Bucket  
✅ **Constitutional governance** - All boundaries enforced  
✅ **Complete audit trail** - Every Core action logged  
✅ **Zero regression risk** - Original functionality preserved  
✅ **Enterprise ready** - Compliance and monitoring built-in

The integration is now complete and production-ready! 🚀