# Karma Chain v2 - Comprehensive Analysis

## Executive Summary

**Karma Chain v2** is a sophisticated karma tracking and behavioral analysis system built by Siddhesh and handed over to BHIV on January 5, 2026. It implements Vedic karma principles with modern ML/RL techniques.

---

## System Architecture

### Core Purpose
Karma Chain tracks, evaluates, and predicts user behavior based on Vedic karma principles, providing:
- Behavioral scoring and tracking
- Karmic debt management (Rnanubandhan)
- Atonement recommendations
- Lifecycle simulation (Birth → Life → Death → Rebirth)
- Predictive karma analytics

### Technology Stack
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Port**: 8000 (CONFLICTS with Bucket - needs resolution)
- **ML/RL**: Q-Learning for adaptive predictions
- **Deployment**: Docker + Docker Compose

---

## Key Components

### 1. Karma Engine (`utils/karma_engine.py`)
**Purpose**: Core karma calculation and evaluation

**Key Features**:
- Purushartha-based scoring (Dharma, Artha, Kama, Moksha)
- Token management (DharmaPoints, SevaPoints, PunyaTokens, PaapTokens)
- Karma type classification (Dridha, Adridha, Sanchita, Prarabdha)
- Progressive punishment system
- Decay and expiry mechanisms

**Integration Points**:
- Receives actions from Core/Bucket
- Computes karma scores
- Stores in MongoDB
- Publishes events to Event Bus

### 2. Rnanubandhan Net (`utils/rnanubandhan_net.py`)
**Purpose**: Karmic debt relationship tracking

**Key Features**:
- Tracks karmic bonds between entities
- Manages debt severity (minor, medium, major)
- Calculates debt resolution paths
- Inheritance through rebirth

**Integration Points**:
- Links to user actions
- Affects karma calculations
- Influences atonement requirements

### 3. Agami Predictor (`utils/agami_predictor.py`)
**Purpose**: Future karma prediction using ML

**Key Features**:
- Q-Learning based predictions
- Pattern recognition from historical data
- Atonement recommendation engine
- Adaptive learning from outcomes

**Integration Points**:
- Analyzes historical karma data
- Provides guidance to users
- Feeds into feedback engine

### 4. Karmic Feedback Engine (`utils/karma_feedback_engine.py`)
**Purpose**: Compute net karmic influence and publish telemetry

**Key Features**:
- Real-time karma signal computation
- Batch processing support
- Telemetry publishing
- Health monitoring

**Integration Points**:
- Consumes karma events
- Publishes to STP Bridge
- Feeds InsightFlow dashboards

### 5. Behavioral Normalization (`routes/normalization.py`)
**Purpose**: Standardize multi-module behavioral inputs

**Key Features**:
- Normalizes inputs from Finance, Gurukul, Game, InsightFlow
- Converts to standardized karmic signals
- Batch processing support
- Context-aware weighting

**Integration Points**:
- Receives raw behavioral data
- Outputs normalized karma signals
- Feeds into Karma Engine

### 6. Karmic Analytics (`routes/analytics.py`)
**Purpose**: Analytics and visualization for InsightFlow

**Key Features**:
- Trend analysis
- Chart generation (Dharma/Seva flow, Paap/Punya ratio)
- CSV exports
- Live metrics

**Integration Points**:
- Queries MongoDB for karma data
- Generates visualizations
- Exports for external dashboards

### 7. Event Bus System (`utils/event_bus.py`)
**Purpose**: Real-time event broadcasting

**Key Features**:
- WebSocket-based streaming
- Event history
- Pub/Sub pattern
- Multi-client support

**Integration Points**:
- Broadcasts karma events
- Connects to visualization systems
- Real-time updates

### 8. Lifecycle Engine (`routes/v1/karma/lifecycle.py`)
**Purpose**: Full karmic lifecycle simulation

**Key Features**:
- Birth → Life → Death → Rebirth cycle
- Prarabdha karma tracking
- Death threshold detection
- Loka assignment (Swarga, Mrityuloka, Antarloka, Naraka)
- Karma inheritance

**Integration Points**:
- Tracks user lifecycle
- Manages karma transfer
- Simulates rebirth scenarios

### 9. STP Bridge (`utils/stp_bridge.py`)
**Purpose**: Secure Telemetry Protocol for external systems

**Key Features**:
- Secure telemetry forwarding
- Integration with Unreal Engine, InsightFlow
- Configurable endpoints
- Status monitoring

**Integration Points**:
- Forwards karma telemetry
- Connects to partner platforms
- Enables cross-system analytics

---

## Data Models

### User Karma Profile
```json
{
  "user_id": "string",
  "tokens": {
    "DharmaPoints": 100,
    "SevaPoints": 50,
    "PunyaTokens": 25,
    "PaapTokens": {
      "minor": 5,
      "medium": 2,
      "maha": 0
    }
  },
  "karma_types": {
    "DridhaKarma": 80,
    "AdridhaKarma": 30,
    "SanchitaKarma": 500,
    "PrarabdhaKarma": 100
  },
  "rnanubandhan": [],
  "lifecycle": {
    "birth_count": 1,
    "current_loka": "Mrityuloka",
    "prarabdha_counter": 100
  }
}
```

### Karma Event
```json
{
  "event_type": "life_event",
  "user_id": "user123",
  "action": "help",
  "description": "Helped colleague",
  "purushartha": {
    "Dharma": 0.9,
    "Artha": 0.5,
    "Kama": 0.3,
    "Moksha": 0.7
  },
  "timestamp": "2026-01-29T10:00:00Z"
}
```

---

## API Endpoints

### Core Karma Operations
- `POST /v1/karma/event` - Log karma event
- `GET /api/v1/karma/{user_id}` - Get karma profile
- `POST /api/v1/log-action/` - Log user action
- `POST /api/v1/submit-atonement/` - Submit atonement

### Lifecycle Management
- `GET /api/v1/karma/lifecycle/prarabdha/{user_id}` - Get Prarabdha
- `POST /api/v1/karma/lifecycle/death/check` - Check death threshold
- `POST /api/v1/karma/lifecycle/rebirth/process` - Process rebirth

### Analytics & Feedback
- `POST /api/v1/feedback_signal` - Compute feedback signal
- `GET /api/v1/analytics/karma_trends` - Get trends
- `GET /api/v1/analytics/charts/dharma_seva_flow` - Generate charts

### Normalization
- `POST /api/v1/normalize_state` - Normalize behavioral state
- `POST /api/v1/normalize_state/batch` - Batch normalize

### Event Bus
- `GET /api/v1/events/subscribe` - Subscribe to events
- `POST /api/v1/events/publish` - Publish events

---

## Integration with BHIV Ecosystem

### Current State
- **Status**: Standalone system, not yet integrated
- **Port Conflict**: Uses 8000 (same as Bucket)
- **Database**: Separate MongoDB instance
- **Authentication**: Core authorization required

### Integration Strategy

#### Phase 1: Port Resolution ✅
- Change Bucket port from 8000 → 8001
- Keep Karma on port 8000
- Update all Bucket references

#### Phase 2: Data Flow Integration
```
Core (8002) → Bucket (8001) → Karma (8000)
     ↓              ↓              ↓
  Agents      Governance      Behavioral
  RL Logic    Audit Trail     Karma Tracking
```

**Flow**:
1. Core processes task → generates events
2. Bucket stores events → validates governance
3. Karma consumes events → computes karma scores
4. Karma publishes feedback → back to Bucket/Core

#### Phase 3: Event Integration
- Bucket publishes Core events to Karma Event Bus
- Karma normalizes behavioral data
- Karma computes karma signals
- Karma stores in MongoDB
- Karma publishes analytics to Bucket

#### Phase 4: Feedback Loop
- Karma provides behavioral insights
- Core uses insights for agent routing
- Bucket uses insights for governance
- InsightFlow uses insights for dashboards

---

## Integration Points with Bucket

### 1. Event Publishing
**Bucket → Karma**
```python
# In Bucket's main.py after storing Core event
async def forward_to_karma(event_data):
    async with aiohttp.ClientSession() as session:
        await session.post(
            "http://localhost:8000/v1/karma/event",
            json={
                "event_type": "life_event",
                "user_id": event_data.get("agent_id"),
                "action": event_data.get("event_type"),
                "description": event_data.get("metadata", {})
            }
        )
```

### 2. Behavioral Normalization
**Bucket → Karma Normalization**
```python
# Normalize agent behavior before storing
normalized = await karma_client.normalize_state({
    "module": "core",
    "user_id": agent_id,
    "action": action_type,
    "context": metadata
})
```

### 3. Analytics Integration
**Karma → Bucket Dashboard**
```python
# Fetch karma analytics for Bucket dashboard
karma_trends = await karma_client.get_analytics(
    user_id=agent_id,
    timeframe="7d"
)
```

### 4. Feedback Signals
**Karma → Core (via Bucket)**
```python
# Get karma feedback for agent routing
karma_signal = await karma_client.get_feedback_signal(
    user_id=agent_id
)
# Use signal to influence Core's RL decisions
```

---

## Port Conflict Resolution

### Problem
- **Karma Chain**: Port 8000
- **Bucket**: Port 8000
- **Conflict**: Cannot run both simultaneously

### Solution
**Change Bucket to Port 8001**

**Files to Update**:
1. `BHIV_Central_Depository-main/main.py` - Change uvicorn port
2. `v1-BHIV_CORE-main/integration/bucket_client.py` - Update URL
3. `test_simple.py` - Update test URLs
4. `start_system.py` - Update port checks
5. `README.md` - Update documentation
6. All curl examples and documentation

**New Port Allocation**:
- **Core**: 8002 (unchanged)
- **Bucket**: 8001 (changed from 8000)
- **Karma**: 8000 (unchanged)

---

## Integration Checklist

### Prerequisites
- [ ] Change Bucket port to 8001
- [ ] Verify Bucket starts on 8001
- [ ] Verify Karma starts on 8000
- [ ] Update all documentation

### Phase 1: Basic Integration
- [ ] Create Karma client in Bucket
- [ ] Forward Core events to Karma
- [ ] Test event flow: Core → Bucket → Karma
- [ ] Verify Karma stores events

### Phase 2: Behavioral Normalization
- [ ] Integrate normalization endpoint
- [ ] Normalize agent behaviors
- [ ] Store normalized signals in Bucket
- [ ] Test normalization flow

### Phase 3: Analytics Integration
- [ ] Fetch karma analytics
- [ ] Display in Bucket dashboard
- [ ] Export karma data
- [ ] Test analytics endpoints

### Phase 4: Feedback Loop
- [ ] Get karma feedback signals
- [ ] Pass to Core for RL decisions
- [ ] Monitor feedback effectiveness
- [ ] Tune feedback weights

---

## Security Considerations

### Authentication
- Karma requires Core authorization
- Bucket must authenticate with Core
- Karma validates requester identity

### Data Privacy
- Karma stores behavioral data
- Must comply with GDPR
- Implement data retention policies
- Support right-to-be-forgotten

### Governance
- Karma operates in "constraint_only" mode
- Does not influence UX directly
- Passive observation only (PRANA boundary)
- No direct user feedback loops

---

## Next Steps

### Immediate (Today)
1. ✅ Analyze Karma Chain architecture
2. ⏳ Change Bucket port to 8001
3. ⏳ Verify both systems start
4. ⏳ Update all documentation

### Short-term (This Week)
1. Create Karma client in Bucket
2. Implement event forwarding
3. Test basic integration
4. Document integration patterns

### Medium-term (Next Week)
1. Integrate behavioral normalization
2. Add analytics endpoints
3. Implement feedback loop
4. Performance testing

### Long-term (Phase 2)
1. Full lifecycle integration
2. Rnanubandhan tracking
3. Agami predictions
4. InsightFlow dashboards

---

## Conclusion

Karma Chain v2 is a sophisticated behavioral tracking system that complements the Core-Bucket integration. By changing Bucket's port to 8001, we can run all three systems simultaneously and create a comprehensive behavioral intelligence platform.

**System Ports**:
- Core: 8002 (Brain - Decision Making)
- Bucket: 8001 (Memory - Event Storage)
- Karma: 8000 (Conscience - Behavioral Tracking)

**Integration Pattern**: Core → Bucket → Karma → Analytics → Feedback

**Status**: Ready for port change and integration
