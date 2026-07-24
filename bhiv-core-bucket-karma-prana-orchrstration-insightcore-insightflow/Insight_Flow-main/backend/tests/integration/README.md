# Integration Tests

This directory contains end-to-end integration tests for the InsightFlow system.

## Test Files

### `test_core_integration_e2e.py`
Complete end-to-end tests covering:
- KSML adapter wrapping/unwrapping
- Interface conversion between v1/v2 formats
- Packet validation
- Weighted scoring calculations
- Decision logging and retrieval
- Error handling scenarios

### `test_routing_integration.py`
Focused integration tests for routing system:
- Dashboard service integration
- Routing decision logger
- Weighted scoring engine
- Feedback service integration
- Performance metrics aggregation

## Running Tests

### Run All Integration Tests
```bash
cd backend
python tests/integration/run_integration_tests.py
```

### Run Specific Test File
```bash
cd backend
python tests/integration/run_integration_tests.py test_routing_integration
```

### Run with pytest directly
```bash
cd backend
pytest tests/integration/ -v
```

## Test Coverage

The integration tests cover:

1. **Component Integration**
   - Service-to-service communication
   - Data flow between components
   - Configuration loading and usage

2. **End-to-End Workflows**
   - Complete routing decision flow
   - Logging to dashboard metrics pipeline
   - Error propagation and handling

3. **Data Consistency**
   - Logging accuracy
   - Metrics calculation correctness
   - Score aggregation validation

4. **Error Scenarios**
   - Invalid input handling
   - Service failure recovery
   - Data corruption resilience

## Dependencies

Integration tests require:
- pytest
- pytest-asyncio
- All InsightFlow application dependencies

## Configuration

Tests use temporary directories and mock configurations to avoid affecting production data.

Test fixtures provide:
- Temporary logging directories
- Mock scoring configurations
- Sample test data

## Troubleshooting

If tests fail:

1. **Check Dependencies**: Ensure all required packages are installed
2. **Verify Paths**: Make sure you're running from the backend directory
3. **Check Logs**: Review test output for specific error messages
4. **Temporary Files**: Tests clean up automatically, but check temp directories if needed

## Adding New Tests

When adding new integration tests:

1. Follow the existing naming convention
2. Use appropriate fixtures for setup/teardown
3. Test both success and failure scenarios
4. Include docstrings explaining what's being tested
5. Clean up any resources created during tests