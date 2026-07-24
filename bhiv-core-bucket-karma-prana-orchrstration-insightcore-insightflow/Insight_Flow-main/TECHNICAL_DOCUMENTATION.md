# InsightFlow - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [API Specification](#api-specification)
6. [Q-Learning Algorithm](#q-learning-algorithm)
7. [Authentication & Security](#authentication--security)
8. [Real-time Features](#real-time-features)
9. [Deployment](#deployment)
10. [Performance & Monitoring](#performance--monitoring)
11. [Development Guide](#development-guide)
12. [Testing Strategy](#testing-strategy)

---

## System Overview

### Purpose
InsightFlow is an adaptive decision intelligence engine that routes tasks and responses to the most suitable AI agent using machine learning algorithms, specifically Q-learning for continuous improvement through analytics, feedback, and context signals.

### Core Capabilities
- **Intelligent Agent Routing**: ML-based decision engine with multiple routing strategies
- **Real-time Analytics**: Live performance monitoring and metrics visualization
- **Multi-Agent Support**: NLP, TTS, Computer Vision, and custom agent types
- **Adaptive Learning**: Q-learning algorithm that improves routing decisions over time
- **Performance Tracking**: Comprehensive feedback loop system
- **WebSocket Integration**: Real-time event streaming for instant updates

### Key Metrics
- **Codebase**: 3,165+ lines across 56 files
- **Backend**: ~2,000 lines of Python (FastAPI)
- **Frontend**: ~1,200 lines of TypeScript/React
- **Build Time**: ~5 minutes
- **Deployment**: Single command Docker Compose setup

---

## Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React TS)    │◄──►│   (FastAPI)     │◄──►│   (Supabase)    │
│   Port: 3000    │    │   Port: 8000    │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│     Redis       │◄─────────────┘
                        │   (Cache/WS)    │
                        │   Port: 6379    │
                        └─────────────────┘
```

### Request Flow
```
User Request → Frontend → API Gateway → Authentication → Decision Engine
                                                              │
                                                              ▼
                                                      Q-Learning Router
                                                              │
                                                              ▼
                                                   Agent Selection & Execution
                                                              │
                                                              ▼
                                                     Response & Feedback
                                                              │
                                                              ▼
                                                   Performance Update & Learning
```

### Component Architecture

#### Backend Components
```
app/
├── core/                   # Core system components
│   ├── config.py          # Configuration management
│   ├── database.py        # Supabase client setup
│   └── security.py        # JWT authentication
├── models/                 # Pydantic data models
│   ├── agent.py           # Agent data structures
│   ├── feedback.py        # Feedback models
│   └── routing_log.py     # Routing history models
├── routers/               # API endpoint definitions
│   ├── agents.py          # Agent management endpoints
│   ├── analytics.py       # Analytics endpoints
│   ├── auth.py            # Authentication endpoints
│   ├── routing.py         # Core routing endpoints
│   └── websocket.py       # WebSocket connections
├── schemas/               # Request/Response schemas
│   ├── agent.py           # Agent API schemas
│   ├── feedback.py        # Feedback schemas
│   └── routing.py         # Routing schemas
├── services/              # Business logic layer
│   ├── agent_service.py   # Agent management logic
│   ├── decision_engine.py # Core routing engine
│   ├── event_listener.py  # Event processing
│   └── q_learning.py      # ML algorithm implementation
└── utils/                 # Utility functions
    └── helpers.py         # Common helper functions
```

#### Frontend Components
```
src/
├── components/            # React components
│   ├── Dashboard.tsx      # Main dashboard
│   ├── AgentPerformance.tsx # Agent metrics
│   ├── MetricsOverview.tsx  # System metrics
│   ├── RecentRoutings.tsx   # Routing history
│   └── RoutingAccuracy.tsx  # Accuracy charts
├── services/              # API integration
│   ├── api.ts            # HTTP API client
│   └── websocket.ts      # WebSocket client
├── types/                # TypeScript definitions
│   └── index.ts          # Type definitions
└── utils/                # Utility functions
    └── helpers.ts        # Frontend helpers
```

---

## Technology Stack

### Backend Technologies

#### Core Framework
- **FastAPI 0.115.7**: Modern, fast web framework for building APIs
  - Automatic API documentation (OpenAPI/Swagger)
  - Built-in data validation with Pydantic
  - Async/await support for high performance
  - Type hints for better code quality

#### Database & Storage
- **Supabase 2.9.1**: PostgreSQL-based backend-as-a-service
  - Real-time subscriptions
  - Built-in authentication
  - Row-level security
  - RESTful API generation
- **Redis 7**: In-memory data structure store
  - Session management
  - WebSocket connection tracking
  - Caching layer

#### Data Processing & ML
- **Pydantic 2.10.3**: Data validation and serialization
- **NumPy 2.2.0**: Numerical computing for ML algorithms
- **Pandas 2.2.3**: Data manipulation and analysis

#### Authentication & Security
- **python-jose 3.3.0**: JWT token handling
- **Cryptography**: Secure token encryption
- **CORS middleware**: Cross-origin request handling

#### Communication
- **WebSockets 13.1**: Real-time bidirectional communication
- **HTTPX 0.27.2**: Async HTTP client

### Frontend Technologies

#### Core Framework
- **React 18.3.1**: Component-based UI library
- **TypeScript 5.5.3**: Type-safe JavaScript
- **Vite 5.3.1**: Fast build tool and dev server

#### Styling & UI
- **Tailwind CSS 3.4.4**: Utility-first CSS framework
- **Recharts 2.12.7**: Composable charting library
- **Date-fns 3.6.0**: Date utility library

#### HTTP & Communication
- **Axios 1.7.2**: Promise-based HTTP client
- **WebSocket API**: Native browser WebSocket support

### DevOps & Infrastructure
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Web server and reverse proxy
- **Uvicorn**: ASGI server for FastAPI

---

## Database Design

### Schema Overview
The system uses PostgreSQL through Supabase with four main tables:

#### 1. Agents Table
```sql
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
```

**Purpose**: Stores agent definitions and performance metrics
**Key Fields**:
- `capabilities`: JSON array of agent capabilities
- `performance_score`: Calculated metric (0-1) based on success rate and latency
- `tags`: Array for categorization and filtering

#### 2. Routing Logs Table
```sql
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
```

**Purpose**: Tracks all routing decisions and their outcomes
**Key Fields**:
- `input_data`: Original request data (JSON)
- `confidence_score`: Algorithm confidence in routing decision
- `routing_strategy`: Algorithm used (q_learning, round_robin, etc.)
- `context`: Additional context data for decision making

#### 3. Feedback Events Table
```sql
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
```

**Purpose**: Stores performance feedback for learning
**Key Fields**:
- `success`: Boolean outcome of the routing decision
- `accuracy_score`: Numerical accuracy rating (0-1)
- `user_satisfaction`: User rating (1-5 scale)

#### 4. Q-Learning Table
```sql
CREATE TABLE q_learning_table (
    state TEXT NOT NULL,
    action TEXT NOT NULL,
    q_value FLOAT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (state, action)
);
```

**Purpose**: Stores Q-learning algorithm state-action values
**Key Fields**:
- `state`: Encoded state representation
- `action`: Agent selection action
- `q_value`: Learned value for state-action pair

### Indexes for Performance
```sql
CREATE INDEX idx_routing_logs_created_at ON routing_logs(created_at DESC);
CREATE INDEX idx_routing_logs_agent_id ON routing_logs(selected_agent_id);
CREATE INDEX idx_feedback_agent_id ON feedback_events(agent_id);
CREATE INDEX idx_agents_status ON agents(status);
```

---

## API Specification

### Authentication Endpoints

#### POST /api/v1/auth/login
**Purpose**: Authenticate user and receive JWT token
```json
Request:
{
  "username": "string",
  "password": "string"
}

Response:
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "string",
    "email": "string",
    "role": "admin|user"
  }
}
```

#### POST /api/v1/auth/refresh
**Purpose**: Refresh expired JWT token
```json
Request:
{
  "refresh_token": "string"
}

Response:
{
  "access_token": "new_jwt_token",
  "expires_in": 3600
}
```

### Agent Management Endpoints

#### GET /api/v1/agents
**Purpose**: List all agents with optional filtering
```json
Query Parameters:
- status_filter: "active" | "inactive" | "maintenance"

Response:
[
  {
    "id": "uuid",
    "name": "string",
    "type": "nlp|tts|computer_vision|custom",
    "status": "active|inactive|maintenance",
    "capabilities": [...],
    "performance_score": 0.85,
    "success_rate": 0.92,
    "average_latency": 145.5,
    "total_requests": 1250,
    "successful_requests": 1150,
    "failed_requests": 100,
    "tags": ["text", "classification"],
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/v1/agents/{agent_id}
**Purpose**: Get specific agent details
```json
Response:
{
  "id": "uuid",
  "name": "NLP Processor",
  "type": "nlp",
  "status": "active",
  "capabilities": [
    {
      "name": "text_classification",
      "description": "Classify text content",
      "confidence_threshold": 0.8
    }
  ],
  "performance_metrics": {
    "performance_score": 0.85,
    "success_rate": 0.92,
    "average_latency": 145.5,
    "total_requests": 1250
  }
}
```

#### POST /api/v1/agents
**Purpose**: Create new agent (admin only)
```json
Request:
{
  "name": "string",
  "type": "nlp|tts|computer_vision|custom",
  "capabilities": [
    {
      "name": "string",
      "description": "string",
      "confidence_threshold": 0.8
    }
  ],
  "tags": ["string"],
  "metadata": {}
}

Response: Agent object (same as GET)
```

#### PATCH /api/v1/agents/{agent_id}/status
**Purpose**: Update agent status (admin only)
```json
Request:
{
  "status": "active|inactive|maintenance"
}

Response: Updated agent object
```

### Routing Endpoints

#### POST /api/v1/routing/route
**Purpose**: Route request to optimal agent
```json
Request:
{
  "input_data": {
    "text": "What is the weather today?",
    "additional_context": "user_location: NYC"
  },
  "input_type": "text|image|audio|custom",
  "strategy": "q_learning|round_robin|performance_based|random",
  "context": {
    "user_preferences": {},
    "session_data": {}
  }
}

Response:
{
  "routing_log_id": "uuid",
  "selected_agent": {
    "id": "uuid",
    "name": "NLP Processor",
    "type": "nlp"
  },
  "confidence_score": 0.87,
  "routing_reason": "High performance for text classification tasks",
  "routing_strategy": "q_learning",
  "estimated_latency_ms": 150,
  "execution_time_ms": 142.5
}
```

#### POST /api/v1/routing/feedback
**Purpose**: Submit performance feedback
```json
Request:
{
  "routing_log_id": "uuid",
  "success": true,
  "latency_ms": 142.5,
  "accuracy_score": 0.88,
  "user_satisfaction": 4,
  "error_details": "string (optional)",
  "metadata": {}
}

Response:
{
  "message": "Feedback processed successfully",
  "routing_log_id": "uuid"
}
```

### Analytics Endpoints

#### GET /api/v1/analytics/overview
**Purpose**: Get system performance overview
```json
Query Parameters:
- time_range: "1h|24h|7d|30d"
- agent_type: "nlp|tts|computer_vision" (optional)

Response:
{
  "total_requests": 15420,
  "successful_requests": 14238,
  "failed_requests": 1182,
  "success_rate": 0.923,
  "average_latency_ms": 156.7,
  "active_agents": 12,
  "top_performing_agents": [
    {
      "agent_id": "uuid",
      "name": "NLP Processor",
      "performance_score": 0.95,
      "request_count": 3420
    }
  ],
  "routing_strategy_distribution": {
    "q_learning": 0.65,
    "performance_based": 0.25,
    "round_robin": 0.10
  },
  "time_series_data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "requests": 145,
      "success_rate": 0.92,
      "avg_latency": 150.5
    }
  ]
}
```

#### GET /api/v1/analytics/agents/{agent_id}/performance
**Purpose**: Get detailed agent performance metrics
```json
Query Parameters:
- time_range: "1h|24h|7d|30d"

Response:
{
  "agent_id": "uuid",
  "agent_name": "NLP Processor",
  "performance_metrics": {
    "total_requests": 3420,
    "successful_requests": 3154,
    "failed_requests": 266,
    "success_rate": 0.922,
    "average_latency_ms": 145.2,
    "performance_score": 0.89
  },
  "time_series_performance": [...],
  "error_analysis": {
    "common_errors": [
      {
        "error_type": "timeout",
        "count": 156,
        "percentage": 0.58
      }
    ]
  },
  "usage_patterns": {
    "peak_hours": [9, 10, 14, 15],
    "request_types": {
      "text_classification": 0.65,
      "sentiment_analysis": 0.35
    }
  }
}
```

### WebSocket Endpoints

#### WS /ws/dashboard
**Purpose**: Real-time dashboard updates
```json
Connection: WebSocket
Authentication: JWT token in query parameter

Events Received:
{
  "event_type": "routing_completed|agent_status_changed|performance_update",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    // Event-specific data
  }
}

Events Sent:
{
  "action": "subscribe|unsubscribe",
  "channels": ["routing_events", "agent_status", "performance_metrics"]
}
```

---

## Q-Learning Algorithm

### Overview
The Q-learning implementation is the core intelligence of InsightFlow, enabling adaptive agent selection based on historical performance and context.

### Algorithm Components

#### State Representation
```python
def encode_state(input_type: str, context: Dict, agent_capabilities: List) -> str:
    """
    Encode current request context into a state string
    
    State components:
    - Input type (text, image, audio)
    - Context features (user_type, complexity, domain)
    - Available agent capabilities
    - Time of day, load factors
    """
    features = [
        f"input:{input_type}",
        f"complexity:{context.get('complexity', 'medium')}",
        f"domain:{context.get('domain', 'general')}",
        f"load:{get_current_load_level()}",
        f"time:{get_time_bucket()}"
    ]
    return "|".join(sorted(features))
```

#### Action Space
```python
class QLearningRouter:
    def __init__(self):
        self.learning_rate = 0.1      # α - Learning rate
        self.discount_factor = 0.95   # γ - Future reward discount
        self.epsilon = 0.1            # ε - Exploration rate
        self.epsilon_decay = 0.995    # Epsilon decay rate
        self.min_epsilon = 0.01       # Minimum exploration rate
    
    def get_actions(self, active_agents: List[Agent]) -> List[str]:
        """Return list of available agent IDs as actions"""
        return [agent.id for agent in active_agents if agent.status == 'active']
```

#### Q-Value Update
```python
def update_q_value(self, state: str, action: str, reward: float, next_state: str):
    """
    Update Q-value using Q-learning formula:
    Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
    """
    current_q = self.get_q_value(state, action)
    max_next_q = self.get_max_q_value(next_state)
    
    new_q = current_q + self.learning_rate * (
        reward + self.discount_factor * max_next_q - current_q
    )
    
    self.set_q_value(state, action, new_q)
```

#### Reward Function
```python
def calculate_reward(self, feedback: FeedbackData) -> float:
    """
    Calculate reward based on multiple performance factors
    
    Reward components:
    - Success/failure: +1.0 / -1.0
    - Latency penalty: -0.1 * (latency_ms / 1000)
    - Accuracy bonus: +0.5 * accuracy_score
    - User satisfaction: +0.3 * (user_rating - 3) / 2
    """
    base_reward = 1.0 if feedback.success else -1.0
    
    # Latency penalty (normalized to seconds)
    latency_penalty = -0.1 * (feedback.latency_ms / 1000.0)
    
    # Accuracy bonus
    accuracy_bonus = 0.5 * (feedback.accuracy_score or 0)
    
    # User satisfaction bonus (-0.3 to +0.3)
    satisfaction_bonus = 0.3 * ((feedback.user_satisfaction or 3) - 3) / 2
    
    total_reward = base_reward + latency_penalty + accuracy_bonus + satisfaction_bonus
    
    # Clamp reward to reasonable range
    return max(-2.0, min(2.0, total_reward))
```

#### Exploration vs Exploitation
```python
def select_agent(self, state: str, available_agents: List[str]) -> str:
    """
    Select agent using epsilon-greedy strategy
    """
    if random.random() < self.epsilon:
        # Exploration: random selection
        return random.choice(available_agents)
    else:
        # Exploitation: select best known action
        q_values = {agent: self.get_q_value(state, agent) 
                   for agent in available_agents}
        return max(q_values, key=q_values.get)
```

### Learning Process Flow
```
1. Request arrives → Encode state
2. Get available agents → Define action space  
3. Select agent (ε-greedy) → Execute routing
4. Collect feedback → Calculate reward
5. Update Q-value → Store in database
6. Decay epsilon → Reduce exploration over time
```

### Performance Optimization
- **State Space Reduction**: Use feature hashing for large state spaces
- **Experience Replay**: Store and replay important experiences
- **Batch Updates**: Update Q-values in batches for efficiency
- **Periodic Cleanup**: Remove unused state-action pairs

---

## Authentication & Security

### JWT Implementation

#### Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "role": "admin|user",
    "exp": 1640995200,
    "iat": 1640991600,
    "iss": "InsightFlow"
  },
  "signature": "HMACSHA256(...)"
}
```

#### Security Configuration
```python
# JWT Settings
JWT_SECRET_KEY = "your-secret-key"  # 256-bit secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Security
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_SPECIAL_CHARS = True
BCRYPT_ROUNDS = 12
```

### Role-Based Access Control (RBAC)

#### User Roles
- **Admin**: Full system access, agent management, user management
- **User**: Read access to analytics, routing requests only
- **Service**: API-to-API communication, limited scope

#### Permission Matrix
| Endpoint | Admin | User | Service |
|----------|-------|------|---------|
| GET /agents | ✅ | ✅ | ✅ |
| POST /agents | ✅ | ❌ | ❌ |
| PATCH /agents/{id}/status | ✅ | ❌ | ❌ |
| POST /routing/route | ✅ | ✅ | ✅ |
| POST /routing/feedback | ✅ | ✅ | ✅ |
| GET /analytics/* | ✅ | ✅ | ❌ |

### Security Middleware
```python
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Rate limiting
    if await is_rate_limited(request.client.host):
        raise HTTPException(429, "Rate limit exceeded")
    
    # Request logging
    logger.info(f"{request.method} {request.url} from {request.client.host}")
    
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"]
)
```

---

## Real-time Features

### WebSocket Architecture

#### Connection Management
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
    
    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            del self.user_subscriptions[user_id]
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        for user_id, subscriptions in self.user_subscriptions.items():
            if channel in subscriptions:
                websocket = self.active_connections.get(user_id)
                if websocket:
                    await websocket.send_json(message)
```

#### Event Types
```python
class EventType(str, Enum):
    ROUTING_COMPLETED = "routing_completed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    PERFORMANCE_UPDATE = "performance_update"
    SYSTEM_ALERT = "system_alert"
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
```

#### Real-time Event Processing
```python
async def process_routing_event(routing_log: RoutingLog):
    """Process and broadcast routing completion event"""
    event = {
        "event_type": EventType.ROUTING_COMPLETED,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "routing_log_id": routing_log.id,
            "agent_name": routing_log.agent_name,
            "execution_time_ms": routing_log.execution_time_ms,
            "status": routing_log.status,
            "confidence_score": routing_log.confidence_score
        }
    }
    
    await connection_manager.broadcast_to_channel("routing_events", event)
```

### Frontend WebSocket Integration
```typescript
class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    
    connect(token: string) {
        const wsUrl = `${WS_BASE_URL}/ws/dashboard?token=${token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.subscribe(['routing_events', 'agent_status', 'performance_metrics']);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleEvent(data);
        };
        
        this.ws.onclose = () => {
            this.handleReconnect();
        };
    }
    
    private handleEvent(event: WebSocketEvent) {
        switch (event.event_type) {
            case 'routing_completed':
                this.updateRoutingMetrics(event.data);
                break;
            case 'agent_status_changed':
                this.updateAgentStatus(event.data);
                break;
            case 'performance_update':
                this.updatePerformanceCharts(event.data);
                break;
        }
    }
}
```

---

## Deployment

### Docker Configuration

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose Configuration
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-data:
```

### Environment Configuration

#### Production Environment Variables
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Security
JWT_SECRET_KEY=your-256-bit-secret-key
JWT_ALGORITHM=HS256

# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65
```

### Cloud Deployment Options

#### AWS ECS Deployment
```json
{
  "family": "insightflow-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-ecr-repo/insightflow-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SUPABASE_URL",
          "value": "https://your-project.supabase.co"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insightflow-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: insightflow-backend
  template:
    metadata:
      labels:
        app: insightflow-backend
    spec:
      containers:
      - name: backend
        image: insightflow-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: insightflow-secrets
              key: supabase-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Performance & Monitoring

### Metrics Collection

#### Application Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')

# Business metrics
ROUTING_DECISIONS = Counter('routing_decisions_total', 'Total routing decisions', ['strategy', 'agent_type'])
AGENT_PERFORMANCE = Gauge('agent_performance_score', 'Agent performance score', ['agent_id', 'agent_name'])
Q_LEARNING_UPDATES = Counter('q_learning_updates_total', 'Q-learning table updates')
```

#### Performance Monitoring
```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

### Health Checks

#### Application Health Check
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "checks": {}
    }
    
    # Database connectivity
    try:
        db = get_db()
        result = db.table("agents").select("count").execute()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis connectivity
    try:
        redis_client = get_redis()
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Q-learning model status
    try:
        q_table_size = await get_q_table_size()
        health_status["checks"]["q_learning"] = f"healthy ({q_table_size} entries)"
    except Exception as e:
        health_status["checks"]["q_learning"] = f"unhealthy: {str(e)}"
    
    return health_status
```

### Logging Configuration
```python
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/insightflow.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "DEBUG",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}
```

---

## Development Guide

### Local Development Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with API URLs

# Run development server
npm run dev
```

### Code Style & Standards

#### Python Code Style
```python
# Use type hints
def process_routing_request(
    request: RouteRequest,
    user_context: Dict[str, Any]
) -> RouteResponse:
    """Process routing request with proper typing"""
    pass

# Use Pydantic models for data validation
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AgentType
    capabilities: List[Capability] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Use async/await for I/O operations
async def get_agent_performance(agent_id: str) -> Dict[str, float]:
    """Async database operations"""
    db = get_db()
    result = await db.table("agents").select("*").eq("id", agent_id).execute()
    return result.data[0] if result.data else None
```

#### TypeScript Code Style
```typescript
// Use interfaces for type definitions
interface Agent {
  id: string;
  name: string;
  type: AgentType;
  status: AgentStatus;
  performanceScore: number;
}

// Use proper error handling
const fetchAgents = async (): Promise<Agent[]> => {
  try {
    const response = await api.get<Agent[]>('/agents');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    throw new Error('Unable to load agents');
  }
};

// Use React hooks properly
const useAgentPerformance = (agentId: string) => {
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const data = await api.getAgentPerformance(agentId);
        setPerformance(data);
      } catch (error) {
        console.error('Failed to fetch performance:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPerformance();
  }, [agentId]);
  
  return { performance, loading };
};
```

### Database Migrations

#### Adding New Tables
```sql
-- Migration: 001_add_user_preferences.sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

#### Modifying Existing Tables
```sql
-- Migration: 002_add_agent_metadata.sql
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_health_check TIMESTAMPTZ;

-- Update existing records
UPDATE agents SET metadata = '{}' WHERE metadata IS NULL;
```

---

## Testing Strategy

### Backend Testing

#### Unit Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.q_learning import QLearningRouter

client = TestClient(app)

class TestQLearningRouter:
    def setup_method(self):
        self.router = QLearningRouter()
    
    def test_state_encoding(self):
        """Test state encoding functionality"""
        context = {
            "input_type": "text",
            "complexity": "high",
            "domain": "finance"
        }
        state = self.router.encode_state(context)
        assert "input:text" in state
        assert "complexity:high" in state
        assert "domain:finance" in state
    
    def test_reward_calculation(self):
        """Test reward calculation"""
        feedback = FeedbackData(
            success=True,
            latency_ms=150.0,
            accuracy_score=0.9,
            user_satisfaction=4
        )
        reward = self.router.calculate_reward(feedback)
        assert 0.5 < reward < 2.0  # Should be positive for good performance
    
    @pytest.mark.asyncio
    async def test_agent_selection(self):
        """Test agent selection logic"""
        state = "input:text|complexity:medium"
        agents = ["agent1", "agent2", "agent3"]
        
        # Test exploitation (epsilon = 0)
        self.router.epsilon = 0
        selected = await self.router.select_agent(state, agents)
        assert selected in agents
        
        # Test exploration (epsilon = 1)
        self.router.epsilon = 1
        selected = await self.router.select_agent(state, agents)
        assert selected in agents
```

#### Integration Tests
```python
class TestRoutingAPI:
    def setup_method(self):
        self.client = TestClient(app)
        self.auth_token = self.get_test_token()
    
    def test_route_request_success(self):
        """Test successful routing request"""
        request_data = {
            "input_data": {"text": "Test message"},
            "input_type": "text",
            "strategy": "q_learning"
        }
        
        response = self.client.post(
            "/api/v1/routing/route",
            json=request_data,
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "routing_log_id" in data
        assert "selected_agent" in data
        assert "confidence_score" in data
    
    def test_route_request_unauthorized(self):
        """Test routing request without authentication"""
        request_data = {
            "input_data": {"text": "Test message"},
            "input_type": "text"
        }
        
        response = self.client.post("/api/v1/routing/route", json=request_data)
        assert response.status_code == 401
```

### Frontend Testing

#### Component Tests
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from '../components/Dashboard';
import { WebSocketService } from '../services/websocket';

// Mock WebSocket service
jest.mock('../services/websocket');

describe('Dashboard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard with metrics', async () => {
    const mockMetrics = {
      totalRequests: 1000,
      successRate: 0.95,
      averageLatency: 150
    };

    // Mock API response
    jest.spyOn(api, 'getOverviewMetrics').mockResolvedValue(mockMetrics);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('1000')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('150ms')).toBeInTheDocument();
    });
  });

  test('handles WebSocket connection', () => {
    const mockConnect = jest.fn();
    (WebSocketService as jest.Mock).mockImplementation(() => ({
      connect: mockConnect,
      subscribe: jest.fn()
    }));

    render(<Dashboard />);

    expect(mockConnect).toHaveBeenCalledWith(expect.any(String));
  });
});
```

#### End-to-End Tests
```typescript
import { test, expect } from '@playwright/test';

test.describe('InsightFlow E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.fill('[data-testid="username"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'testpassword');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard');
  });

  test('should display dashboard metrics', async ({ page }) => {
    await expect(page.locator('[data-testid="total-requests"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-rate"]')).toBeVisible();
    await expect(page.locator('[data-testid="average-latency"]')).toBeVisible();
  });

  test('should route a request successfully', async ({ page }) => {
    await page.click('[data-testid="new-request-button"]');
    await page.fill('[data-testid="request-input"]', 'Test routing request');
    await page.selectOption('[data-testid="input-type"]', 'text');
    await page.click('[data-testid="submit-request"]');
    
    await expect(page.locator('[data-testid="routing-result"]')).toBeVisible();
    await expect(page.locator('[data-testid="selected-agent"]')).toContainText('NLP Processor');
  });
});
```

### Performance Testing
```python
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_routing_endpoint():
    """Load test the routing endpoint"""
    url = "http://localhost:8000/api/v1/routing/route"
    headers = {"Authorization": "Bearer test-token"}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        start_time = time.time()
        
        for i in range(1000):  # 1000 concurrent requests
            task = session.post(
                url,
                json={
                    "input_data": {"text": f"Test message {i}"},
                    "input_type": "text",
                    "strategy": "q_learning"
                },
                headers=headers
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
        failed = len(responses) - successful
        duration = end_time - start_time
        
        print(f"Load test results:")
        print(f"Total requests: {len(responses)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Duration: {duration:.2f}s")
        print(f"Requests/second: {len(responses)/duration:.2f}")

if __name__ == "__main__":
    asyncio.run(load_test_routing_endpoint())
```

---

## Conclusion

InsightFlow represents a comprehensive, production-ready AI agent routing system that combines modern web technologies with advanced machine learning algorithms. The system's modular architecture, extensive API coverage, real-time capabilities, and robust testing strategy make it suitable for enterprise deployment.

### Key Technical Achievements
- **Scalable Architecture**: Microservices-based design with Docker containerization
- **Intelligent Routing**: Q-learning algorithm for adaptive agent selection
- **Real-time Operations**: WebSocket integration for live updates
- **Comprehensive API**: RESTful endpoints with OpenAPI documentation
- **Security**: JWT authentication with role-based access control
- **Monitoring**: Health checks, metrics collection, and logging
- **Testing**: Unit, integration, and E2E test coverage

### Future Enhancements
- **Advanced ML**: Deep reinforcement learning algorithms
- **Scalability**: Kubernetes orchestration and auto-scaling
- **Analytics**: Advanced analytics with ML-powered insights
- **Integration**: Plugin system for custom agent types
- **Performance**: Caching strategies and database optimization

This technical documentation serves as a comprehensive guide for developers, system administrators, and stakeholders working with the InsightFlow system.