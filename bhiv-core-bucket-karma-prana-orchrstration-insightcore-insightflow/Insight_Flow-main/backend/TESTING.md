# InsightFlow Testing Guide

Complete guide for running tests and verification in InsightFlow.

## Quick Start

### Run Everything
```bash
cd backend
python run_all_verification.py
```

### Run Tests Only
```bash
cd backend
python run_tests.py
```

### Verify Endpoints Only
```bash
cd backend
# Start server first
uvicorn app.main:app --reload &
python verify_endpoints.py
```

## Test Categories

### Phase 1 Tests - Core Components
```bash
pytest tests/adapters/ -v      # KSML adapter tests
pytest tests/validators/ -v    # Packet validator tests
```

### Phase 2 Tests - Services & ML
```bash
pytest tests/services/ -v      # Service layer tests
pytest tests/ml/ -v            # ML/scoring engine tests
```

### Phase 3 Tests - Integration & Performance
```bash
pytest tests/integration/ -v   # End-to-end integration tests
pytest tests/performance/ -v   # Performance/SLA tests
```

## Detailed Test Commands

### Complete Test Suite with Coverage
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Run with Detailed Output
```bash
pytest tests/ -vv -s
```

### Show Slowest Tests
```bash
pytest tests/ -v --durations=10
```

### Run Specific Test File
```bash
pytest tests/integration/test_routing_integration.py -v
```

## Endpoint Verification

### Manual Testing

#### Route Agent Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/routing/route-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "nlp",
    "context": {"text": "test"},
    "confidence_threshold": 0.5
  }'
```

#### Dashboard Endpoints
```bash
curl http://localhost:8000/dashboard/metrics/performance?hours=24
curl http://localhost:8000/dashboard/metrics/accuracy
curl http://localhost:8000/dashboard/metrics/agents
```

#### Admin Endpoints (require auth)
```bash
curl "http://localhost:8000/admin/routing-logs?limit=5"
curl http://localhost:8000/admin/routing-statistics
curl -X POST http://localhost:8000/admin/cleanup-logs
```

## Code Quality Checks

### Run Quality Checks
```bash
python check_code_quality.py
```

### Manual Quality Commands
```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/ --max-line-length=100

# Check test coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## Windows Users

Use the provided batch files:

```cmd
# Run all tests
test_commands.bat

# Test endpoints
endpoint_tests.bat
```

## Test Results

### Success Criteria
- All unit tests pass
- Integration tests pass
- Performance tests meet SLAs
- Code coverage > 70%
- All endpoints respond correctly

### Performance SLAs
- Routing P50 latency < 30ms
- Routing P99 latency < 100ms
- Throughput > 1000 req/s
- Logging latency < 10ms
- Dashboard metrics < 100ms

## Troubleshooting

### Common Issues

#### Server Not Running
```bash
# Start server
uvicorn app.main:app --reload
```

#### Missing Dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

#### Permission Issues
```bash
# On Windows, run as administrator
# On Unix, check file permissions
chmod +x *.py
```

#### Port Already in Use
```bash
# Kill existing process
# Windows: taskkill /f /im python.exe
# Unix: pkill -f uvicorn
```

### Test Failures

#### Integration Test Failures
- Check if all services are running
- Verify database connections
- Check log files for errors

#### Performance Test Failures
- Ensure system is not under load
- Run tests multiple times
- Check for resource constraints

#### Endpoint Test Failures
- Verify server is running on correct port
- Check authentication if required
- Validate request/response formats

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_all_verification.py
```

## Coverage Reports

After running tests with coverage:
- HTML report: `htmlcov/index.html`
- Terminal report: Shows missing lines
- Target: > 70% coverage

## Performance Monitoring

Track performance trends:
- Run performance tests regularly
- Monitor SLA compliance
- Set up alerts for regressions
- Compare with production metrics