# InsightFlow - Adaptive Decision Intelligence Engine

**Version 3.1 (Production Hardened) - Sovereign-Grade Ready** ✅

InsightFlow is a cross-platform, self-learning intelligence layer that routes tasks and responses to the most suitable AI agent, continuously improving through analytics, feedback, and context signals. Now enhanced with **Phase 3.1 Hardening** featuring signed telemetry, karma-weighted Q-learning, and SSPL Phase III compliance.

## 🚀 Core Features

### 🧠 **Intelligent Routing System**
- **Q-learning Based Routing**: Adaptive routing with multiple strategies
- **Karma-Weighted Learning**: Behavioral scoring with reward smoothing (Phase 3.1)
- **Weighted Scoring Engine**: Multi-factor confidence calculation
- **Alternative Agent Suggestions**: Fallback options with confidence scores
- **Context-Aware Decisions**: Priority-based and domain-specific routing
- **Real-Time Policy Updates**: Closed-loop learning with instant adaptation

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

### 📈 **Analytics & Monitoring**
- **Real-time Analytics**: Live performance monitoring and metrics
- **Karma Metrics**: Behavioral scoring analytics and trends
- **STP Metrics**: Packet transmission statistics
- **Telemetry Security**: HMAC-SHA256 packet signing with nonce protection (Phase 3.1)
- **Policy Update Telemetry**: Real-time learning adaptation tracking (Phase 3.1)
- **Admin Dashboard**: Comprehensive control panel
- **Performance Tracking**: Feedback loop and learning system

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
STP_ENABLED=true

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
USE_SOVEREIGN_CORE=true

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
# Telemetry Security Configuration (Phase 3.1)
# =============================================================================

# Enable packet signing
ENABLE_TELEMETRY_SIGNING=true

# Maximum timestamp drift (seconds)
TELEMETRY_MAX_TIMESTAMP_DRIFT=5
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

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
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
pip install asyncpg python-dotenv  # Additional dependencies for Sovereign Core

# Run development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## 📚 API Usage Examples

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

### Route Agent with Karma Scoring

```bash
curl -X POST http://localhost:8000/api/v1/routing/route-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "nlp",
    "context": {
      "priority": "normal",
      "user_id": "user123"
    },
    "confidence_threshold": 0.75
  }'
```

### Batch Processing with STP Wrapping (v2)

```bash
curl -X POST http://localhost:8000/api/v2/routing/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "requests": [
      {"input_data": {"text": "Query 1"}, "input_type": "text"},
      {"input_data": {"text": "Query 2"}, "input_type": "text"}
    ],
    "strategy": "q_learning",
    "enable_stp": true
  }'
```

### Karma Control Endpoints

```bash
# Toggle Karma weighting
curl -X POST "http://localhost:8000/api/karma/toggle" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Get Karma metrics
curl -X GET "http://localhost:8000/api/karma/metrics"

# Get agent Karma score
curl -X GET "http://localhost:8000/api/karma/score/nlp-001"

# Admin Karma controls (requires auth)
curl -X POST "http://localhost:8000/admin/karma/toggle?enabled=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X GET "http://localhost:8000/admin/karma/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X DELETE "http://localhost:8000/admin/karma/cache" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### STP Packet Operations

```bash
# Get STP metrics
curl -X GET "http://localhost:8000/api/stp/metrics"

# Unwrap STP packet (for debugging)
curl -X POST "http://localhost:8000/api/stp/unwrap" \
  -H "Content-Type: application/json" \
  -d '{
    "stp_token": "your_stp_token",
    "payload": {"data": "encrypted_payload"},
    "metadata": {"source": "client"}
  }'
```

### Telemetry Security Operations

```bash
# Get telemetry security status
curl -X GET "http://localhost:8000/api/telemetry/security/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify signed telemetry packet
curl -X POST "http://localhost:8000/api/telemetry/security/verify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "signed_packet": {
      "request_id": "test-123",
      "security": {
        "nonce": "abc123...",
        "timestamp": "2024-01-01T00:00:00Z",
        "packet_signature": "def456..."
      }
    }
  }'

# Get telemetry security metrics
curl -X GET "http://localhost:8000/api/telemetry/security/metrics" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Toggle packet signing (admin only)
curl -X POST "http://localhost:8000/api/telemetry/security/toggle?enabled=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Clear nonce cache (admin only)
curl -X DELETE "http://localhost:8000/api/telemetry/security/nonce-cache" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Submit Feedback with Karma Impact

```bash
curl -X POST http://localhost:8000/api/v2/routing/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "routing_log_id": "log_123",
    "success": true,
    "latency_ms": 145.5,
    "accuracy_score": 0.88,
    "user_satisfaction": 4,
    "karma_impact": true
  }'
```

### Analytics and Monitoring

```bash
# Get comprehensive analytics
curl http://localhost:8000/api/v1/analytics/overview?time_range=24h \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get routing statistics
curl http://localhost:8000/api/routing/statistics

# Get scoring weights
curl http://localhost:8000/api/scoring/weights

# Migration status
curl http://localhost:8000/api/migration/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testing

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

# Run telemetry security tests (Phase 3.1)
pytest tests/test_telemetry_security.py -v
pytest tests/telemetry_security/ -v

# Run telemetry security integration test
python test_telemetry_security_integration.py
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 🚀 Deployment

### Deploy to Cloud Platforms

#### AWS ECS with Sovereign Core

```bash
# Build and push Docker images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker build -t insightflow-backend ./backend
docker tag insightflow-backend:latest YOUR_ECR_URL/insightflow-backend:latest
docker push YOUR_ECR_URL/insightflow-backend:latest

# Deploy with environment variables for Sovereign Core
aws ecs update-service --cluster your-cluster --service insightflow-service --force-new-deployment
```

#### Kubernetes with ConfigMaps

```bash
# Create ConfigMap for Sovereign Core configuration
kubectl create configmap insightflow-config \
  --from-env-file=backend/.env

# Apply Kubernetes configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

#### Render/Railway

1. Connect your GitHub repository
2. Set environment variables (including Sovereign Core config)
3. Deploy with automatic builds

## 📊 Enhanced System Architecture

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

### Sovereign Core Integration Flow

```
Client Request → STP Wrapping → Karma Score Retrieval → Weighted Scoring
                      ↓                    ↓                    ↓
              Token Generation    Behavioral Analysis    Multi-factor Confidence
                      ↓                    ↓                    ↓
              Secure Transmission → Agent Selection → STP Response Wrapping
```

## 🔄 API Migration & Compatibility

InsightFlow supports multiple integration patterns:

### **Current Support:**
- **v1 API**: Legacy format with backward compatibility
- **v2 API**: Enhanced with Karma, STP, and advanced features
- **Supabase**: Legacy database support
- **Sovereign Core**: Modern enterprise integration

### **Migration Timeline:**
- **Phase 1**: Dual API support (Current)
- **Phase 2**: Sovereign Core integration (Current)
- **Phase 3**: v1 deprecation warnings (30 days)
- **Phase 4**: v1 removal (60 days)

### Migration Resources
- **Migration Guide**: [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)
- **API Versioning**: [docs/API_VERSIONING.md](docs/API_VERSIONING.md)
- **STP Implementation**: [docs/STP_IMPLEMENTATION.md](docs/STP_IMPLEMENTATION.md)
- **Migration Status**: `GET /api/migration/status`
- **Conversion Tools**: `POST /api/migration/convert/request`

## 🔧 Configuration Management

### Environment-Based Configuration

```bash
# Development
ENVIRONMENT=development
USE_SOVEREIGN_CORE=false
KARMA_ENABLED=true
STP_ENABLED=false

# Staging
ENVIRONMENT=staging
USE_SOVEREIGN_CORE=true
KARMA_ENABLED=true
STP_ENABLED=true

# Production
ENVIRONMENT=production
USE_SOVEREIGN_CORE=true
KARMA_ENABLED=true
STP_ENABLED=true
```

### Feature Toggles

- **Karma Weighting**: Runtime toggle via API or environment
- **STP Middleware**: Enable/disable secure packet transmission
- **Sovereign Core**: Switch between Supabase and Sovereign Core
- **API Versioning**: Control v1/v2 availability

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Guidelines

- Follow existing code patterns
- Add tests for new features
- Update documentation
- Maintain backward compatibility
- Use type hints and docstrings

## 📝 License

MIT License - see LICENSE file for details

## 👥 Team

- **Lead Developer**: Ashmit Pandey
- **Analytics Core**: Nisarg
- **Infrastructure**: Bucket Team
- **Karma Integration**: Siddhesh (Karma Tracker Service)

## 📧 Support

For support, email support@insightflow.ai or open an issue on GitHub.

## 🏆 Acknowledgments

- **Sovereign Core Team**: For enterprise integration framework
- **Karma Tracker Team**: For behavioral scoring service
- **Community Contributors**: For feedback and improvements

---

**Built with ❤️ using FastAPI, React, Supabase, Q-Learning, and Sovereign Core**

## 🎯 Quick Start Commands Summary

```bash
# Complete setup in 4 commands
git clone https://github.com/blackholeinfiverse54-creator/Insight_Flow.git
cd Insight_Flow/backend
cp .env.example .env  # Edit with your configuration
docker-compose up --build

# Access at http://localhost:3000 (Frontend) and http://localhost:8000 (API)
```

## 📦 Project Statistics

- **Backend**: ~45 files, ~8,500 lines of Python
- **Frontend**: ~15 files, ~1,500 lines of TypeScript/React
- **Tests**: ~25 test files with comprehensive coverage
- **Documentation**: Complete API guides and migration docs
- **Total**: Production-ready full-stack application with enterprise features
- **Build Time**: ~7 minutes
- **Deployment Time**: ~12 minutes
- **Migration**: Automated tracking and conversion tools

## 🌟 Latest Updates (Phase 3.1 - Production Hardened)

### ✨ **New in v3.1 (Phase 3.1 Hardening):**
- **Signed Telemetry**: HMAC-SHA256 packet signing with nonce-based replay protection
- **Karma-Weighted Q-Learning**: Adaptive reward smoothing (75% reward + 25% karma)
- **Real-Time Policy Updates**: Closed-loop learning with instant adaptation telemetry
- **SSPL Phase III Compliance**: Complete security test coverage and validation
- **Timestamp Drift Protection**: 5-second tolerance with cryptographic verification
- **Agent Fingerprinting**: Per-agent security tracking and validation

### ✨ **Previous Updates (Phase 2.2):**
- **Sovereign Core Integration**: Enterprise-grade security and database
- **Karma Behavioral Scoring**: AI-driven user behavior analysis
- **STP Middleware**: Secure token protocol for packet transmission
- **Enhanced Admin Controls**: Real-time system management
- **Comprehensive Testing**: Full endpoint and integration test coverage
- **Migration Support**: Seamless transition tools and guides

### 🔮 **Coming Soon (Phase 4.0):**
- **Advanced Analytics Dashboard**: Real-time behavioral insights with ML optimization
- **Multi-tenant Support**: Organization-level isolation and resource management
- **Enhanced Security**: OAuth2, RBAC, and comprehensive audit logging
- **Performance Optimization**: Redis caching, CDN integration, and load balancing
- **Mobile SDK**: Native mobile app integration with offline support
- **Distributed Tracing**: OpenTelemetry integration for microservices monitoring

---

**Ready to deploy! 🚀**