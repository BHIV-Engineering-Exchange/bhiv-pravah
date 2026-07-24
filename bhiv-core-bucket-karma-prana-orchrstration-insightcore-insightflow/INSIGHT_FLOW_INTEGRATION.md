# 🔄 Insight Flow Integration Complete

## Status: ✅ INTEGRATED (Minimal Bridge Pattern)

**Date**: 2026-01-31  
**Integration Type**: Bridge Service  
**Ports**: 8006 (Bridge), 8007 (Insight Flow Backend)

---

## What is Insight Flow?

**Insight Flow** is an advanced **agent routing and telemetry platform** with:
- Q-learning based intelligent routing
- Karma-weighted behavioral scoring
- Real-time analytics dashboard
- Multi-agent support (NLP, TTS, Vision, etc.)
- Telemetry security with packet signing

---

## Integration Architecture

```
User Request
     ↓
Core (8002) ──optional──> Insight Flow Bridge (8006)
                                    ↓
                          Insight Flow Backend (8007)
                          [Q-Learning Routing]
                          [Karma Weighting]
                          [Analytics]
                                    ↓
                          Route Decision
                                    ↓
                          Back to Core (8002)
                                    ↓
                          Normal Flow → Bucket → Karma
```

---

## Services Overview

### 1. Insight Flow Backend (Port 8007)
- **Purpose**: Full agent routing platform
- **Features**: Q-learning, Karma integration, analytics
- **Database**: Requires PostgreSQL/Supabase
- **Status**: Standalone service

### 2. Insight Flow Bridge (Port 8006)
- **Purpose**: Integration layer with BHIV Core
- **Features**: Routing proxy, analytics aggregation
- **Dependencies**: Insight Flow Backend (8007), Core (8002)
- **Status**: ✅ Created

### 3. Insight Core (Port 8005)
- **Purpose**: JWT security validation
- **Features**: Token validation, replay protection
- **Status**: ✅ Already integrated

---

## Quick Start

### Option 1: Full Integration (Recommended for Advanced Routing)

```bash
# Terminal 1: Start Insight Flow Backend
cd "Insight_Flow-main"
start_insight_flow.bat

# Terminal 2: Start Insight Flow Bridge
cd "Insight_Flow-main"
start_bridge.bat

# Terminal 3: Start Core (will use routing)
cd "v1-BHIV_CORE-main"
python mcp_bridge.py
```

### Option 2: Minimal Integration (Current Setup)

```bash
# Just start the bridge (Insight Flow backend optional)
cd "Insight_Flow-main"
python insight_flow_bridge.py
```

---

## API Endpoints

### Insight Flow Bridge (8006)

#### POST /route
Route request through intelligent routing
```bash
curl -X POST "http://localhost:8006/route" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"text": "What is AI?"},
    "input_type": "text",
    "strategy": "q_learning",
    "context": {"priority": "high"}
  }'
```

#### POST /route-agent
Get best agent for specific type
```bash
curl -X POST "http://localhost:8006/route-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "nlp",
    "context": {"user_id": "user123"},
    "confidence_threshold": 0.75
  }'
```

#### GET /analytics
Get routing analytics
```bash
curl "http://localhost:8006/analytics"
```

#### GET /health
Health check
```bash
curl "http://localhost:8006/health"
```

---

## Integration Benefits

### 1. Intelligent Routing
- Q-learning based agent selection
- Karma-weighted scoring
- Confidence thresholds
- Alternative agent suggestions

### 2. Analytics & Monitoring
- Real-time performance metrics
- Routing decision logs
- Agent success rates
- User behavior analysis

### 3. Non-Invasive
- Optional integration (Core works without it)
- Bridge pattern (no Core modifications)
- Graceful degradation
- Independent scaling

---

## Configuration

### Insight Flow Backend (.env)
```env
# Database (Required for full features)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key

# Or use PostgreSQL
SOVEREIGN_DB_HOST=localhost
SOVEREIGN_DB_PORT=5432
SOVEREIGN_DB_NAME=insightflow

# Karma Integration
KARMA_ENDPOINT=http://localhost:8000/api/karma
KARMA_ENABLED=true

# Q-Learning
LEARNING_RATE=0.1
DISCOUNT_FACTOR=0.95
EPSILON=0.1
```

### Insight Flow Bridge
```python
# insight_flow_bridge.py
INSIGHT_FLOW_URL = "http://localhost:8007"
CORE_URL = "http://localhost:8002"
BUCKET_URL = "http://localhost:8001"
KARMA_URL = "http://localhost:8000"
```

---

## Testing

### Test Bridge Health
```bash
curl http://localhost:8006/health
```

### Test Routing
```bash
curl -X POST "http://localhost:8006/route" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"text": "test"},
    "input_type": "text"
  }'
```

### Test Analytics
```bash
curl http://localhost:8006/analytics
```

---

## System Status

### Current Integration
✅ **Insight Core (8005)**: JWT security - INTEGRATED  
✅ **Insight Flow Bridge (8006)**: Routing proxy - CREATED  
⚠️  **Insight Flow Backend (8007)**: Full platform - OPTIONAL  

### Integration Pattern
- **Minimal**: Bridge only (no database required)
- **Full**: Bridge + Backend (requires PostgreSQL)
- **Recommended**: Start with minimal, upgrade to full as needed

---

## Files Created

1. **`Insight_Flow-main/insight_flow_bridge.py`** - Bridge service
2. **`Insight_Flow-main/start_bridge.bat`** - Bridge startup
3. **`Insight_Flow-main/start_insight_flow.bat`** - Backend startup
4. **`INSIGHT_FLOW_INTEGRATION.md`** - This documentation

---

## Comparison: Insight Core vs Insight Flow

| Feature | Insight Core (8005) | Insight Flow (8006/8007) |
|---------|-------------------|------------------------|
| Purpose | Security validation | Agent routing |
| JWT Validation | ✅ | ❌ |
| Replay Protection | ✅ | ❌ |
| Q-Learning Routing | ❌ | ✅ |
| Karma Integration | ❌ | ✅ |
| Analytics Dashboard | ❌ | ✅ |
| Database Required | ❌ | ✅ (for full features) |
| Integration Status | ✅ Active | ✅ Bridge created |

---

## Next Steps

### Immediate (No Database)
1. Start Insight Flow Bridge: `start_bridge.bat`
2. Test routing: `curl http://localhost:8006/health`
3. Use bridge for intelligent routing (optional)

### Full Setup (With Database)
1. Set up PostgreSQL or Supabase
2. Configure `.env` in `Insight_Flow-main/backend`
3. Start backend: `start_insight_flow.bat`
4. Start bridge: `start_bridge.bat`
5. Access dashboard: `http://localhost:3000`

---

## Maintenance

### Bridge Only (Minimal)
- No database maintenance
- No migrations
- Simple restart if needed

### Full Platform
- Database backups
- Q-table updates
- Analytics retention
- Dashboard updates

---

## Status Summary

✅ **Insight Core**: Fully integrated (security layer)  
✅ **Insight Flow Bridge**: Created and ready  
⚠️  **Insight Flow Backend**: Optional (requires setup)  

**Recommendation**: Use bridge for routing, keep Insight Core for security. Full Insight Flow backend is optional for advanced analytics.

---

**Last Updated**: 2026-01-31  
**Maintained By**: Ashmit Pandey  
**Status**: Bridge Ready, Backend Optional ✅
