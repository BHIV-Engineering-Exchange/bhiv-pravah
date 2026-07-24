# InsightFlow V3 - Adaptive Decision Intelligence Engine

InsightFlow V3 is a cross-platform, self-learning intelligence layer that routes tasks and responses to the most suitable AI agent, continuously improving through analytics, feedback, and context signals. Now enhanced with **Real-Time Telemetry**, **STP Feedback Integration**, and **Q-Learning Adaptive Routing** for enterprise-grade intelligence and behavioral learning.

## 🎯 **V3 NEW FEATURES - FULLY IMPLEMENTED**

### 📡 **Real-Time Telemetry Bus**
- **WebSocket Streaming**: Live routing decisions streamed to dashboard
- **Bounded Queues**: Backpressure handling with 1000-packet buffer
- **Health Monitoring**: Real-time service health and metrics
- **Performance**: Sustains 200+ messages/second throughput

### 📊 **Live Dashboard**
- **React + TypeScript**: Modern dashboard with Tailwind CSS
- **Real-Time Charts**: Confidence trends, latency, reward distribution
- **Live Stream**: Last 100 routing decisions with search/filter
- **Auto-Reconnect**: Exponential backoff WebSocket reconnection

### 🔗 **STP Feedback Bridge**
- **Behavioral Integration**: Processes feedback from external services
- **Packet Enrichment**: Adds karmic weights and context tags
- **Protocol Support**: STP-1 compliant packet wrapping
- **Safe Processing**: Graceful error handling and fallbacks

### 🧠 **Q-Learning Adaptive Routing**
- **Reward-Based Learning**: Updates agent confidence from feedback
- **Bounded Updates**: Safe Q-value updates with NaN protection
- **Learning Trace**: Complete audit trail of all updates
- **Persistence**: Q-table save/load for durability

## 🚀 Core Features

### 🧠 **Intelligent Routing System**
- **Q-learning Based Routing**: Adaptive routing with multiple strategies
- **Behavioral Scoring**: Karma-weighted decisions based on user behavior patterns
- **Weighted Scoring Engine**: Multi-factor confidence calculation
- **Alternative Agent Suggestions**: Fallback options with confidence scores
- **Context-Aware Decisions**: Priority-based and domain-specific routing

### 📡 **V3 Telemetry & Real-Time Analytics**
- **Live Telemetry Bus**: WebSocket streaming of all routing decisions
- **Real-Time Dashboard**: React dashboard with live charts and metrics
- **Performance Monitoring**: Confidence trends, latency analysis, success rates
- **Bounded Queues**: Backpressure handling with configurable limits
- **Health Endpoints**: Comprehensive service health monitoring

### 🔗 **STP Feedback Integration**
- **STP Bridge**: Lightweight adapter for behavioral service integration
- **Feedback Processing**: Parses karmic weights and reward signals
- **Packet Enrichment**: Adds STP fields to telemetry packets
- **Protocol Compliance**: STP-1 standard packet wrapping
- **Error Resilience**: Graceful degradation on feedback failures

### 🧠 **Q-Learning Adaptive System**
- **Reward-Based Learning**: Updates agent confidence from behavioral feedback
- **Safe Updates**: Bounded Q-values with NaN/infinity protection
- **Learning Trace**: Complete audit trail of confidence changes
- **Persistence**: Q-table save/load for durability across restarts
- **Admin Controls**: Q-learning management endpoints

### 🔐 **Sovereign Core Integration (Phase 2.2)**
- **STP Middleware**: Structured Token Protocol for secure packet transmission
- **Karma Service**: Behavioral scoring from external Karma Tracker
- **Sovereign Auth**: JWT-based authentication with service-to-service support
- **Sovereign Database**: Async PostgreSQL interface with connection pooling
- **Environment Loader**: Standardized configuration with secrets management

### 📊 **API & Integration**
- **Dual API Versioning**: v1 (legacy) and v2 (enhanced) with migration support
- **Batch Processing**: Process multiple requests simultaneously (v2)
- **WebSocket Integration**: Real-time event streaming for instant updates
- **STP Packet Wrapping**: Secure communication protocol
- **KSML Compatibility**: Structured response formatting

### 🛠️ **Enterprise Features**
- **Multi-Agent Support**: NLP, TTS, Computer Vision, and custom types
- **Migration Tools**: Built-in tracking and conversion utilities
- **Production Ready**: Docker containerization with health checks
- **Backward Compatibility**: Seamless transition from legacy systems
- **Modern Dashboard**: React + TypeScript + Tailwind CSS interface

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Supabase account (for database) OR Sovereign Core Database
- Karma Tracker service (optional, for behavioral scoring)

### 🆕 **V3 Additional Requirements**
- **WebSocket Support**: For real-time telemetry streaming
- **Modern Browser**: Chrome/Firefox/Safari for dashboard
- **Python Packages**: `websockets`, `asyncio` for telemetry
- **Node Packages**: `recharts`, `lucide-react` for dashboard

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/blackholeinfiverse54-creator/Insight_Flow.git
cd Insight_Flow
```

### 2. Configure Environment Variables

Create `.env` file in the backend directory:

```bash
# Supabase Configuration (Legacy Support)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Application Configuration
APP_NAME=InsightFlow
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Q-Learning Hyperparameters
LEARNING_RATE=0.1
DISCOUNT_FACTOR=0.95
EPSILON=0.1
MIN_EPSILON=0.01
EPSILON_DECAY=0.995

# Core Feedback Service
CORE_FEEDBACK_SERVICE_URL=http://core-feedback:8000/api/scores
CORE_FEEDBACK_CACHE_TTL=30
CORE_FEEDBACK_TIMEOUT=5
CORE_FEEDBACK_MAX_RETRIES=3

# Routing Decision Logging
ROUTING_LOG_DIR=logs
ROUTING_LOG_RETENTION_DAYS=30

# =============================================================================
# STP-Layer Configuration (Phase 2.2)
# =============================================================================

# Enable STP wrapping (true/false)
STP_ENABLED=false

# STP destination system
STP_DESTINATION=sovereign_core

# Default priority (normal/high/critical)
STP_DEFAULT_PRIORITY=normal

# Require acknowledgment
STP_REQUIRE_ACK=false

# =============================================================================
# Karma Weighting Configuration (Phase 2.2)
# =============================================================================

# Karma Tracker endpoint URL (Siddhesh's service)
KARMA_ENDPOINT=http://localhost:8002/api/karma

# Enable Karma weighting (true/false)
KARMA_ENABLED=true

# Karma cache TTL (seconds)
KARMA_CACHE_TTL=60

# Karma request timeout (seconds)
KARMA_TIMEOUT=5

# Karma weight in scoring (0-1)
KARMA_WEIGHT=0.15

# =============================================================================
# Sovereign Core Configuration (Phase 2.2)
# =============================================================================

# Enable Sovereign Core (true/false)
USE_SOVEREIGN_CORE=false

# Sovereign Core Auth
SOVEREIGN_AUTH_URL=http://localhost:8003/auth
SOVEREIGN_SERVICE_KEY=your_service_key_here
SOVEREIGN_JWT_SECRET=your_jwt_secret_here
SOVEREIGN_JWT_ALGORITHM=HS256

# Sovereign Core Database
SOVEREIGN_DB_HOST=localhost
SOVEREIGN_DB_PORT=5432
SOVEREIGN_DB_NAME=insightflow_sovereign
SOVEREIGN_DB_USER=insightflow_user
SOVEREIGN_DB_PASSWORD=your_db_password_here

# =============================================================================
# V3 Telemetry Bus Configuration
# =============================================================================

# Enable telemetry streaming
TELEMETRY_ENABLED=true

# Maximum queue size (packets)
TELEMETRY_MAX_QUEUE_SIZE=1000

# Maximum WebSocket connections
TELEMETRY_MAX_CONNECTIONS=100

# Rate limit (messages/sec per connection)
TELEMETRY_RATE_LIMIT=200

# Telemetry WebSocket endpoint
TELEMETRY_ENDPOINT=/telemetry/stream

# Telemetry buffer size (number of packets)
TELEMETRY_BUFFER_SIZE=1000

# Telemetry authentication (true/false)
TELEMETRY_AUTH_REQUIRED=false

# =============================================================================
# V3 STP Feedback Configuration
# =============================================================================

# Enable STP feedback enrichment (true/false)
ENABLE_FEEDBACK=true

# STP protocol version
STP_VERSION=stp-1

# Enable Q-learning updates (true/false)
ENABLE_Q_UPDATES=true

# Enable karma weighting in Q-learning (true/false)
ENABLE_KARMA_WEIGHTING=true

# =============================================================================
# V3 Q-Learning Configuration
# =============================================================================

# Q-learning learning rate (0.0-1.0)
Q_LEARNING_RATE=0.1

# Q-learning discount factor (0.0-1.0)
Q_DISCOUNT_FACTOR=0.95
```

### 3. Set Up Database

#### Option A: Supabase (Legacy Support)
Run these SQL commands in your Supabase SQL editor:

```sql
-- Create agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    capabilities JSONB DEFAULT '[]',
    performance_score FLOAT DEFAULT 0.5,
    success_rate FLOAT DEFAULT 0.5,
    average_latency FLOAT DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create routing_logs table
CREATE TABLE routing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL,
    user_id TEXT,
    input_type TEXT NOT NULL,
    input_data JSONB NOT NULL,
    selected_agent_id UUID REFERENCES agents(id),
    agent_name TEXT,
    confidence_score FLOAT,
    routing_reason TEXT,
    routing_strategy TEXT,
    status TEXT DEFAULT 'pending',
    execution_time_ms FLOAT,
    response_data JSONB,
    error_message TEXT,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create feedback_events table
CREATE TABLE feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    routing_log_id UUID REFERENCES routing_logs(id),
    agent_id UUID REFERENCES agents(id),
    feedback_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    latency_ms FLOAT NOT NULL,
    accuracy_score FLOAT,
    user_satisfaction INTEGER CHECK (user_satisfaction BETWEEN 1 AND 5),
    error_details TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Q-learning table
CREATE TABLE q_learning_table (
    state TEXT NOT NULL,
    action TEXT NOT NULL,
    q_value FLOAT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (state, action)
);

-- Create indexes
CREATE INDEX idx_routing_logs_created_at ON routing_logs(created_at DESC);
CREATE INDEX idx_routing_logs_agent_id ON routing_logs(selected_agent_id);
CREATE INDEX idx_feedback_agent_id ON feedback_events(agent_id);
CREATE INDEX idx_agents_status ON agents(status);

-- Insert sample agents
INSERT INTO agents (name, type, status, tags, capabilities) VALUES
('NLP Processor', 'nlp', 'active', ARRAY['text', 'classification'], 
 '[{"name": "text_classification", "description": "Classify text", "confidence_threshold": 0.8}]'::jsonb),
('TTS Generator', 'tts', 'active', ARRAY['audio', 'speech'], 
 '[{"name": "text_to_speech", "description": "Convert text to audio", "confidence_threshold": 0.7}]'::jsonb),
('Vision Analyzer', 'computer_vision', 'active', ARRAY['image', 'detection'], 
 '[{"name": "object_detection", "description": "Detect objects in images", "confidence_threshold": 0.75}]'::jsonb);
```

#### Option B: Sovereign Core Database (Recommended)
Set up PostgreSQL database with the same schema using the Sovereign Core Database interface.

### 4. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Access the Application

- **V3 Dashboard**: http://localhost:3000 (NEW)
- **Backend API**: http://localhost:8000
- **Original Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Panel**: http://localhost:8000/admin/system-health

## 🧪 Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install asyncpg python-dotenv websockets  # V3 dependencies

# Run development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Original)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### 🆕 **V3 Dashboard**

```bash
cd frontend/dashboard

# Install dependencies
npm install

# Run V3 dashboard
npm start

# Access dashboard
# http://localhost:3000
```

## 📚 API Usage Examples

### 🆕 **V3 Telemetry & Real-Time Features**

#### WebSocket Telemetry Stream
```bash
# Connect to live telemetry stream
wscat -c ws://localhost:8000/telemetry/decisions

# Health check
curl http://localhost:8000/telemetry/health
```

#### STP Feedback Processing
```bash
# Send behavioral feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "karmic_weight": 0.34,
    "reward_value": 0.8,
    "context_tags": ["success", "fast"],
    "state": "nlp_task",
    "action": "nlp-001",
    "request_id": "req-123",
    "stp_version": "stp-1"
  }'
```

#### Q-Learning Management
```bash
# Get learning trace
curl http://localhost:8000/admin/q-learning/trace?limit=50

# Save Q-table
curl -X POST http://localhost:8000/admin/q-learning/save

# Load Q-table
curl -X POST http://localhost:8000/admin/q-learning/load
```

### 📊 **Original API Examples**

### Enhanced Routing with Karma Weighting (v2)

```bash
curl -X POST http://localhost:8000/api/v2/routing/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "input_data": {"text": "What is the weather today?"},
    "input_type": "text",
    "strategy": "q_learning",
    "context": {
      "priority": "high",
      "domain": "weather",
      "user_id": "user123"
    },
    "preferences": {
      "max_latency_ms": 500,
      "min_confidence": 0.8,
      "enable_karma": true
    }
  }'
```

## 🧪 Testing

### 🆕 **V3 Integration Testing**

```bash
cd backend

# Run V3 integration tests
pytest tests/test_v3_integration.py -v

# Run complete V3 test suite
python test_v3_complete.py

# Run telemetry tests
pytest tests/telemetry_bus/ -v
```

### Comprehensive Endpoint Testing

```bash
cd backend

# Run comprehensive endpoint tests
python test_all_endpoints.py

# Run specific test suites
pytest tests/ -v
pytest tests/services/ -v
pytest tests/middleware/ -v

# Run Karma service tests
pytest tests/services/test_karma_service.py -v

# Run STP middleware tests
pytest tests/middleware/test_stp_middleware.py -v
```

### Frontend Tests

```bash
cd frontend
npm run test

# V3 Dashboard tests
cd frontend/dashboard
npm test
```

## 📊 Enhanced System Architecture

### 🆕 **V3 Real-Time Intelligence Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     InsightFlow V3                           │
│                Real-Time Intelligence                        │
└─────────────────────────────────────────────────────────────┘

User Request → API Router → Decision Engine → Agent Selection
                    ↓              ↓               ↓
              Telemetry Bus → WebSocket Stream → Live Dashboard
                    ↓              ↓               ↓
              STP Bridge ← Behavioral Service → Q-Learning
                    ↓              ↓               ↓
              Packet Enrichment → Reward Signal → Confidence Update
                                     ↓
                              Real-Time Learning
```

### **Legacy Architecture (Still Supported)**

```
User Request → API Version Detection → STP Middleware → Enhanced Decision Engine
                        ↓                      ↓                    ↓
                Migration Tracking      Packet Wrapping      Karma Weighting
                        ↓                      ↓                    ↓
                Analytics Dashboard    Secure Transmission   Behavioral Scoring
                                                    ↓
                                            Agent Selection + Alternatives
                                                    ↓
                                            Feedback Collection
                                                    ↓
                                      Performance + Karma Metrics Update
                                                    ↓
                                          Q-Table + Karma Update (Learning)
```

## 🎯 Quick Start Commands Summary

### 🚀 **V3 Complete Setup**

```bash
# Complete V3 setup in 6 commands
git clone https://github.com/blackholeinfiverse54-creator/Insight_Flow.git
cd Insight_Flow/backend
cp .env.example .env  # Edit with V3 configuration
docker-compose up --build

# Start V3 Dashboard (separate terminal)
cd ../frontend/dashboard
npm install && npm start

# Access Points:
# - Backend API: http://localhost:8000
# - V3 Dashboard: http://localhost:3000
# - Original Frontend: http://localhost:5173
# - API Docs: http://localhost:8000/docs
```

### 📡 **V3 Feature Testing**

```bash
# Test telemetry stream
wscat -c ws://localhost:8000/telemetry/decisions

# Send test feedback
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{"reward_value": 0.8, "state": "test", "action": "agent1"}'

# Check Q-learning trace
curl http://localhost:8000/admin/q-learning/trace
```

## 📦 Project Statistics

### 🆕 **V3 Enhanced Statistics**
- **Backend**: ~65 files, ~12,000 lines of Python (V3 additions)
- **Frontend**: ~30 files, ~3,000 lines of TypeScript/React (V3 dashboard)
- **Tests**: ~35 test files with V3 integration coverage
- **Documentation**: Complete V3 guides and implementation docs
- **V3 Features**: Real-time telemetry, STP bridge, Q-learning
- **Performance**: 200+ msg/sec WebSocket throughput
- **Build Time**: ~9 minutes (with V3 components)
- **Deployment Time**: ~15 minutes (with dashboard)

### **Legacy Statistics (Still Supported)**
- **Original Backend**: ~45 files, ~8,500 lines of Python
- **Original Frontend**: ~15 files, ~1,500 lines of TypeScript/React
- **Migration Tools**: Automated tracking and conversion tools
- **Total**: Production-ready full-stack application with enterprise features

## 🌟 Latest Updates (V3 - FULLY IMPLEMENTED)

### ✨ **New in V3:**
- **Real-Time Telemetry Bus**: WebSocket streaming of all routing decisions
- **Live Dashboard**: React dashboard with real-time charts and metrics
- **STP Feedback Integration**: Behavioral service integration with reward processing
- **Q-Learning Adaptive Routing**: Confidence updates based on behavioral feedback
- **Admin Q-Learning Controls**: Learning trace, Q-table persistence
- **Comprehensive V3 Testing**: Full integration test suite

### ✅ **V3 Implementation Status:**
- **Phase A - Telemetry Bus**: ✅ COMPLETE
- **Phase B - Dashboard**: ✅ COMPLETE
- **Phase C - STP Bridge**: ✅ COMPLETE
- **Phase D - Q-Learning**: ✅ COMPLETE
- **Integration Testing**: ✅ COMPLETE
- **Documentation**: ✅ COMPLETE

### 🔮 **Future Enhancements:**
- **Advanced ML Models**: Deep learning integration
- **Multi-tenant Dashboard**: Organization-level dashboards
- **Mobile Dashboard**: Native mobile app
- **Advanced Analytics**: Predictive routing analytics
- **Edge Deployment**: Distributed telemetry processing

## 🎉 **V3 IMPLEMENTATION COMPLETE!**

### ✅ **All V3 Features Implemented & Tested:**
- **Real-Time Telemetry**: WebSocket streaming ✅
- **Live Dashboard**: React + charts ✅
- **STP Feedback**: Behavioral integration ✅
- **Q-Learning**: Adaptive routing ✅
- **Admin Controls**: Q-learning management ✅
- **Integration Tests**: Complete test suite ✅

### 🚀 **Ready for Production Deployment!**

**V3 brings InsightFlow to the next level with real-time intelligence, behavioral learning, and live monitoring capabilities while maintaining full backward compatibility with all existing features.**

---

**Built with ❤️ using FastAPI, React, WebSockets, Q-Learning, and Real-Time Intelligence**