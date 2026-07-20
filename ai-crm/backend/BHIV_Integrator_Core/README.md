# 🎯 BHIV Integrator Core

**Production-Ready Unified Backend Layer**

Consolidates Logistics, CRM, and Task Manager systems into one cohesive, event-driven backend connected through BHIV Core, UniGuru, and Gurukul pipelines.

## 🚀 Quick Start

```bash
# Start the consolidated backend
python start_integrator.py

# Run integration tests
python test_integration.py

# Launch unified dashboard
streamlit run dashboard_integration.py
```

## 📊 Access Points

- **API Gateway**: http://localhost:8005
- **API Documentation**: http://localhost:8005/docs
- **Unified Dashboard**: http://localhost:8501
- **Event Monitoring**: http://localhost:8005/event/events

## 🎯 Core Deliverables Completed

### ✅ Central Integration Layer (BHIV Bridge)
- **Event Broker**: `/event/publish` and `/event/subscribe` for all modules
- **Logistics APIs**: `/logistics/procurement`, `/logistics/delivery`, `/logistics/inventory`
- **CRM APIs**: `/crm/accounts`, `/crm/leads`, `/crm/opportunities`
- **Task APIs**: `/task/review`, `/task/feedback`, `/task/workflow-state`
- **Employee APIs**: `/employee/monitoring`, `/employee/attendance`, `/employee/performance`
- **BHIV Core Integration**: `/bhiv/agent/register`, `/bhiv/agent/decide`

### ✅ Event-Driven Triggers
- **Order → CRM Lead → Opportunity → Task Creation**
- **Delivery delay → Feedback → Task escalation**
- **Account status change → Compliance → Dashboard refresh**
- **Employee monitoring → Performance alerts → Task assignment**

### ✅ Unified Logging & Compliance Flow
- **Structured Logs**: `{system, event_type, reference_id, status, timestamp, DHI_score, compliance_flag}`
- **Sankalp Integration**: Compliance hooks across all modules
- **Audit Trail**: Every transaction carries compliance records
- **Central DB Sync**: Activity logs synced to central database/MongoDB

## Overview

The BHIV Integrator Core serves as the central integration layer that:

- **Consolidates APIs** from Logistics (/procurement, /delivery, /inventory), CRM (/accounts, /leads, /opportunities), and Task Manager (/review, /feedback, /workflow-state)
- **Provides Event Broker** for event-driven communication between systems
- **Implements Unified Logging** with DHI scoring and compliance tracking
- **Integrates Compliance Hooks** across all transactions
- **Connects to BHIV Core** for agentic routing and decision making

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BHIV Integrator Core                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Logistics  │  │     CRM     │  │ Task Mgmt   │         │
│  │    APIs     │  │    APIs     │  │    APIs     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│           │               │               │                 │
│           └───────┬───────┴───────┬───────┘                 │
│                   │               │                         │
│           ┌───────▼───────────────▼───────┐                 │
│           │        Event Broker           │                 │
│           │   (publish/subscribe)         │                 │
│           └───────▲───────────────▲───────┘                 │
│                   │               │                         │
│           ┌───────┴───────────────┴───────┐                 │
│           │    Unified Logging &         │                 │
│           │    Compliance Hooks          │                 │
│           └───────────────────────────────┘                 │
│                   │                                         │
│           ┌───────▼─────────────────────────────────────┐   │
│           │             BHIV Core                        │   │
│           │    (Agent Registry & Decision Engine)       │   │
│           └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 🎯 Event-Driven Architecture
- **Event Broker**: Publish/subscribe system for inter-system communication
- **Event Triggers**: Automatic actions based on system events (Order → CRM Lead → Opportunity → Task)
- **Webhook Integration**: Real-time event notifications between systems

### 📊 Unified Logging & Compliance
- **Structured Logging**: {system, event_type, reference_id, status, timestamp, DHI_score, compliance_flag}
- **DHI Scoring**: Dynamic scoring based on compliance, efficiency, quality, and timeliness
- **Compliance Hooks**: Integrated Sankalp compliance checks for all transactions
- **Audit Trails**: Complete transaction and access logging

### 🔗 System Integration
- **API Consolidation**: Single entry point for all system APIs
- **BHIV Core Connection**: Agent registry and decision routing
- **UniGuru Integration**: Knowledge retrieval and AI assistance
- **Gurukul Pipelines**: Educational content and workflow management

## Event Triggers

### Order → CRM → Task Flow
1. **Order Created** (Logistics) → Creates CRM Lead
2. **Lead Qualified** (CRM) → Creates Opportunity
3. **Opportunity Won** (CRM) → Creates Fulfillment Task
4. **Task Completed** (Task) → Updates CRM Opportunity

### Issue Escalation Flow
1. **Delivery Delayed** (Logistics) → Escalates Task
2. **Task Escalated** (Task) → Notifies CRM Account Manager
3. **Complaint Received** (Task) → Triggers Compliance Review

## Quick Start

### Prerequisites
- Python 3.11+
- Running Logistics, CRM, and Task Management systems
- BHIV Core system (optional for full functionality)

### Installation
```bash
cd BHIV_Integrator_Core
pip install -r requirements.txt
```

### Configuration
Edit `config/settings.py` with your system URLs and API keys.

### Run
```bash
python app.py
```

The integrator will be available at `http://localhost:8005`

## API Endpoints

### Logistics Integration
- `GET/POST /logistics/procurement` - Procurement orders
- `GET/POST /logistics/delivery` - Delivery management
- `GET/PUT /logistics/inventory` - Inventory tracking

### CRM Integration
- `GET/POST /crm/accounts` - Account management
- `GET/POST /crm/leads` - Lead management
- `GET/POST /crm/opportunities` - Opportunity management

### Task Management Integration
- `GET/POST /task/review` - Task reviews
- `GET/POST /task/feedback` - Task feedback
- `GET/POST /task/workflow-state` - Workflow management
- `GET/POST /task/tasks` - Task CRUD operations

### Event Broker
- `POST /event/publish` - Publish events
- `POST /event/subscribe` - Subscribe to events
- `GET /event/events` - Get event history

## Configuration

### Environment Variables
```env
# System URLs
LOGISTICS_BASE_URL=http://localhost:8000
CRM_BASE_URL=http://localhost:8502
TASK_BASE_URL=http://localhost:8000

# BHIV Core
BHIV_CORE_URL=http://localhost:8002
BHIV_CORE_API_KEY=your-api-key

# Compliance
COMPLIANCE_ENABLED=true
SANKALP_COMPLIANCE_URL=http://localhost:8007

# Event Broker
EVENT_BROKER_PORT=8006
```

## Compliance & Security

### DHI Score Calculation
- **Compliance (40%)**: Transaction compliance status
- **Efficiency (30%)**: Processing speed and resource usage
- **Quality (20%)**: Error rates and success metrics
- **Timeliness (10%)**: Response times and SLA adherence

### Compliance Hooks
- **Transaction Validation**: All financial transactions checked
- **Data Privacy**: PII data encryption and access control
- **Audit Trails**: Complete logging of all system actions
- **Access Control**: Role-based permissions for all operations

## Monitoring & Health Checks

- **Health Endpoint**: `GET /health` - System health status
- **Status Endpoint**: `GET /status` - Detailed system status
- **Metrics Endpoint**: `GET /event/health` - Event broker status

## Development

### Project Structure
```
BHIV_Integrator_Core/
├── app.py                 # Main FastAPI application
├── config/
│   └── settings.py        # Configuration settings
├── apis/
│   ├── logistics_api.py   # Logistics API router
│   ├── crm_api.py         # CRM API router
│   └── task_api.py        # Task API router
├── event_broker/
│   └── event_broker.py    # Event broker implementation
├── unified_logging/
│   └── logger.py          # Unified logging system
├── compliance/
│   └── compliance_hooks.py # Compliance integration
├── modules/               # Future module implementations
├── tests/                 # Test suites
└── docs/                  # Documentation
```

### Adding New Event Triggers
1. Define trigger in `config/settings.py` EVENT_TRIGGERS
2. Implement trigger logic in `event_broker/event_broker.py`
3. Add event handling in appropriate API router

### Extending Compliance Checks
1. Add new compliance rules in `compliance/compliance_hooks.py`
2. Update DHI score calculations in logger
3. Configure compliance flags in settings

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8005
CMD ["python", "app.py"]
```

### Environment Setup
- Set production URLs in environment variables
- Configure proper API keys and secrets
- Enable compliance and logging features
- Set up monitoring and alerting

## Contributing

1. Follow the existing code structure
2. Add comprehensive logging for all operations
3. Include compliance checks for sensitive operations
4. Update documentation for new features
5. Add tests for new functionality

## License

Proprietary - BHIV Core Integration Layer