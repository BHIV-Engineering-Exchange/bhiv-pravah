# AI Integration Platform - Testing Documentation

## Overview

This document provides comprehensive testing procedures for the AI Integration Platform. The platform consists of multiple components that require systematic testing to ensure reliability and functionality.

## Project Architecture

### Core Components
- **FastAPI Backend** (Port 8000): RESTful API server
- **Agent Registry**: Dynamic agent discovery and management
- **Basket Manager**: Workflow orchestration engine
- **Logging System**: Centralized logging with multiple outputs
- **Database Layer**: MongoDB for persistence, Redis for caching

### Agent Domains
- **Finance**: cashflow_analyzer, goal_recommender, financial_coordinator
- **Automotive**: auto_diagnostics, vehicle_maintenance, fuel_efficiency
- **Education**: vedic_quiz_agent, sanskrit_parser, gurukul_*
- **Workflow**: workflow_agent

## Testing Environment Setup

### Prerequisites
1. **Python 3.8+** installed
2. **Node.js 16+** installed
3. **MongoDB** running (optional, falls back to file logging)
4. **Redis** running (optional, falls back to in-memory)
5. **Git** for version control

### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/BHAgent23/Agents_integration.git
cd agentBASKETS

# 2. Install Python dependencies
cd AI_integration
pip install -r requirements.txt

# 3. Install Node.js dependencies (for admin panel)
cd admin-panel
npm install
cd ..

# 4. Install root-level Node.js dependencies
cd ..
npm install
```

## Testing Categories

### 1. Unit Tests

#### Redis Service Tests
**File**: `AI_integration/tests/test_redis_service.py`

**Purpose**: Test Redis service functionality including connection, data storage, and retrieval.

**Test Cases**:
- Connection establishment and failure handling
- Execution log storage and retrieval
- Agent state management
- Basket execution tracking
- Data cleanup operations

**Running Tests**:
```bash
cd AI_integration
python -m pytest tests/test_redis_service.py -v
```

**Expected Results**:
- All connection tests pass (with/without Redis running)
- Data storage/retrieval operations work correctly
- Error handling is graceful

#### Basket Manager Tests
**File**: `AI_integration/tests/test_basket_manager.py`

**Purpose**: Test basket execution logic, agent chaining, and error handling.

**Test Cases**:
- Basket initialization with valid/invalid configurations
- Sequential execution of agents
- Input validation and compatibility checking
- Error handling and recovery
- Resource cleanup

**Running Tests**:
```bash
cd AI_integration
python -m pytest tests/test_basket_manager.py -v
```

**Expected Results**:
- Baskets initialize correctly with proper configurations
- Sequential execution completes successfully
- Errors are handled gracefully with proper logging

#### Integration Tests
**File**: `AI_integration/tests/test_integration.py`

**Purpose**: Test end-to-end functionality across components.

**Test Cases**:
- Health endpoint functionality
- Agent and basket listing
- Basket execution via API
- Error scenarios and recovery
- End-to-end basket workflows

**Running Tests**:
```bash
cd AI_integration
python -m pytest tests/test_integration.py -v
```

**Expected Results**:
- All API endpoints respond correctly
- Basket execution completes end-to-end
- Error handling works across components

### 2. System Integration Tests

#### Complete System Test
**File**: `AI_integration/tests/test_complete_system.py`

**Purpose**: Test the complete system with real API calls and external services.

**Test Cases**:
- Direct API calls to law agent endpoints
- LLM service integration
- Basket system integration
- End-to-end workflows

**Running Tests**:
```bash
cd AI_integration
python tests/test_complete_system.py
```

**Expected Results**:
- All external API calls succeed
- System components integrate properly
- End-to-end workflows complete successfully

#### Law Agent Integration Tests
**Files**:
- `AI_integration/tests/test_law_agent_api.py`
- `AI_integration/tests/test_law_agent_integration.py`

**Purpose**: Test law agent specific functionality and integration.

**Running Tests**:
```bash
cd AI_integration
python tests/test_law_agent_api.py
python tests/test_law_agent_integration.py
```

### 3. Configuration Validation Tests

#### Sample Input Validation
**Purpose**: Validate that all sample input files are valid JSON.

**Running Tests**:
```bash
cd AI_integration
python tests/run_tests.py  # Includes sample input validation
```

**Expected Results**:
- All JSON files in `tests/sample_inputs/` are valid
- Files contain proper data structures

#### Basket Configuration Validation
**Purpose**: Validate basket configuration files.

**Running Tests**:
```bash
cd AI_integration
python tests/run_tests.py  # Includes basket config validation
```

**Expected Results**:
- All basket JSON files have required fields
- Execution strategies are valid
- Agent references exist

#### Agent Specification Validation
**Purpose**: Validate agent specification files.

**Running Tests**:
```bash
cd AI_integration
python tests/run_tests.py  # Includes agent spec validation
```

**Expected Results**:
- All agent directories have `agent_spec.json`
- Specifications contain required fields
- Capabilities are properly defined

### 4. Manual Testing Procedures

#### Backend API Testing

**Start the Backend**:
```bash
cd AI_integration
python main.py
```

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "socketio": "disabled",
    "redis": "connected"
  }
}
```

**List Agents**:
```bash
curl http://localhost:8000/agents
```

**List Baskets**:
```bash
curl http://localhost:8000/baskets
```

**Test Basket Execution**:
```bash
curl -X POST http://localhost:8000/run-basket \
  -H "Content-Type: application/json" \
  -d '{
    "basket_name": "finance_daily_check",
    "input_data": {
      "transactions": [
        {"amount": 1000, "category": "income"},
        {"amount": -500, "category": "expenses"}
      ]
    }
  }'
```

#### Frontend Testing

**Start Admin Panel**:
```bash
cd AI_integration/admin-panel
npm run dev
```

**Access URLs**:
- Admin Panel: http://localhost:5173
- Backend API: http://localhost:8000

**Manual Test Steps**:
1. Open admin panel in browser
2. Verify agents are listed
3. Verify baskets are displayed
4. Test basket execution with sample data
5. Check health status indicators

#### Logging System Testing

**Check Log Files**:
```bash
# Application logs
tail -f AI_integration/logs/application.log

# Execution logs
tail -f AI_integration/logs/executions.log

# Error logs
tail -f AI_integration/logs/errors.log

# Basket-specific logs
ls AI_integration/logs/basket_runs/
tail -f AI_integration/logs/basket_runs/finance_daily_check_*.log
```

**MongoDB Log Verification**:
```bash
# Connect to MongoDB and check logs collection
mongosh
use ai_integration
db.logs.find().limit(5)
```

**Redis Data Verification**:
```bash
# Connect to Redis and check stored data
redis-cli
KEYS *
HGETALL "execution:<execution_id>:logs"
```

### 5. Performance Testing

#### Basket Execution Performance
**Test Method**: Run multiple basket executions and measure timing.

```bash
# Run performance test
cd AI_integration
python -c "
import asyncio
import time
from baskets.basket_manager import AgentBasket
from agents.agent_registry import AgentRegistry

async def performance_test():
    registry = AgentRegistry('agents')
    basket_spec = {
        'basket_name': 'performance_test',
        'agents': ['cashflow_analyzer', 'goal_recommender'],
        'execution_strategy': 'sequential'
    }

    start_time = time.time()
    basket = AgentBasket(basket_spec, registry)
    result = await basket.execute({'input': 'test'})
    end_time = time.time()

    print(f'Execution time: {end_time - start_time:.2f}s')
    return result

asyncio.run(performance_test())
"
```

**Expected Performance**:
- Single agent: < 5 seconds
- 2-agent basket: < 10 seconds
- Memory usage: < 500MB

### 6. Error Scenario Testing

#### Database Connection Failure
**Test Method**: Stop MongoDB/Redis and verify graceful fallback.

```bash
# Stop services
sudo systemctl stop mongod
sudo systemctl stop redis

# Run tests
cd AI_integration
python main.py

# Check health endpoint - should show degraded status
curl http://localhost:8000/health
```

**Expected Behavior**:
- System continues to function with file-based logging
- Health endpoint shows "degraded" status
- No crashes or unhandled exceptions

#### Invalid Input Testing
**Test Method**: Send malformed requests to API endpoints.

```bash
# Invalid basket execution
curl -X POST http://localhost:8000/run-basket \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Invalid agent execution
curl -X POST http://localhost:8000/run-agent \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "nonexistent_agent"}'
```

**Expected Behavior**:
- Proper HTTP error codes (400, 404, 500)
- Descriptive error messages
- Logging of error details

### 7. Automated Test Suite

#### Running All Tests
```bash
cd AI_integration
python tests/run_tests.py
```

**Test Output**:
- Comprehensive test results in `tests/test_results.json`
- Detailed logging in `test_results.log`
- Success/failure summary

#### Continuous Integration
**GitHub Actions**: `.github/workflows/supabase-deploy.yml`

**Trigger**: Push to main branch

**Tests Run**:
- Unit tests for all components
- Integration tests
- Configuration validation
- Performance benchmarks

### 8. Troubleshooting Test Failures

#### Common Issues and Solutions

**Redis Connection Failed**:
```
Error: Redis connection failed
Solution: Install/start Redis or ensure fallback mechanisms work
```

**MongoDB Connection Failed**:
```
Error: MongoDB connection failed
Solution: Install/start MongoDB or verify file logging fallback
```

**Agent Import Failed**:
```
Error: ModuleNotFoundError
Solution: Check agent directory structure and Python path
```

**Basket Execution Timeout**:
```
Error: Execution timeout
Solution: Check agent implementations and network connectivity
```

**Configuration Validation Failed**:
```
Error: Invalid JSON in configuration files
Solution: Validate JSON syntax and required fields
```

### 9. Test Data Management

#### Sample Input Files
**Location**: `AI_integration/tests/sample_inputs/`

**Files**:
- `cashflow_analyzer_input.json`
- `financial_coordinator_input.json`
- `goal_recommender_input.json`
- `sanskrit_parser_input.json`
- `vedic_quiz_agent_input.json`

#### Test Basket Configurations
**Location**: `AI_integration/baskets/`

**Available Baskets**:
- `finance_daily_check.json`
- `auto_complete_checkup.json`
- `gurukul_practice.json`

### 10. Monitoring and Reporting

#### Test Results Dashboard
```bash
# View latest test results
cat AI_integration/tests/test_results.json | jq '.summary'
```

#### Log Analysis
```bash
# Search for errors in logs
grep "ERROR" AI_integration/logs/*.log

# Check basket execution logs
find AI_integration/logs/basket_runs/ -name "*.log" -exec tail -20 {} \;
```

#### Performance Monitoring
```bash
# Monitor system resources during testing
top -p $(pgrep -f "python main.py")

# Check Redis memory usage
redis-cli info memory
```

## Conclusion

This testing documentation provides comprehensive procedures for validating all aspects of the AI Integration Platform. Regular execution of these tests ensures system reliability and catches issues early in development.

For additional support or questions about testing procedures, refer to the main README.md or contact the development team.