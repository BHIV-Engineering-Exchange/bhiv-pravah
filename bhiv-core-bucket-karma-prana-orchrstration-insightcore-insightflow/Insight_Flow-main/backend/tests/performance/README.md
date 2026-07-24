# Performance Tests

Performance test suite for InsightFlow routing engine components.

## SLA Requirements

### Routing Engine
- **P50 Latency**: < 30ms per routing decision
- **P99 Latency**: < 100ms per routing decision  
- **Throughput**: > 1000 requests/second

### Logging System
- **Log Write Latency**: < 10ms per decision
- **Query Performance**: < 50ms for 100 records

### Dashboard Service
- **Metrics Calculation**: < 100ms for 1000 decisions
- **Agent Performance**: < 50ms for 20 agents

## Test Files

### `test_routing_performance.py`
Core routing engine performance tests:
- Weighted scoring latency (P50/P99)
- Throughput under load
- SLA compliance validation

### `test_logging_performance.py`
Decision logging performance tests:
- Log write latency
- Query performance with large datasets
- Statistics calculation speed

### `test_dashboard_performance.py`
Dashboard service performance tests:
- Metrics aggregation speed
- Agent performance calculation
- Large dataset handling

## Running Tests

### Run All Performance Tests
```bash
cd backend
python tests/performance/run_performance_tests.py
```

### Run Performance Benchmark
```bash
cd backend
python tests/performance/run_performance_tests.py benchmark
```

### Run Specific Test File
```bash
cd backend
pytest tests/performance/test_routing_performance.py -v -s
```

### Run with Detailed Timing
```bash
cd backend
pytest tests/performance/ -v -s --durations=0
```

## Interpreting Results

### Success Criteria
- All assertions pass (latency/throughput SLAs met)
- No performance regressions from baseline
- Consistent performance across test runs

### Failure Investigation
If performance tests fail:

1. **Check System Load**: Ensure test machine isn't under heavy load
2. **Run Multiple Times**: Performance can vary, run 3-5 times
3. **Profile Code**: Use profiling tools to identify bottlenecks
4. **Check Dependencies**: Ensure optimal dependency versions

### Performance Monitoring
- Run performance tests in CI/CD pipeline
- Track performance trends over time
- Set up alerts for SLA violations
- Monitor production metrics vs test results

## Optimization Tips

### Routing Engine
- Cache scoring configurations
- Optimize weight calculations
- Use efficient data structures

### Logging System
- Batch log writes when possible
- Use appropriate file I/O settings
- Implement log rotation

### Dashboard Service
- Cache frequently accessed metrics
- Optimize database queries
- Use efficient aggregation algorithms

## Benchmarking

The benchmark mode provides detailed performance metrics:
- Average latency per operation
- Throughput under sustained load
- Memory usage patterns
- Performance consistency

Use benchmark results to:
- Establish performance baselines
- Compare optimization efforts
- Validate SLA requirements
- Plan capacity requirements