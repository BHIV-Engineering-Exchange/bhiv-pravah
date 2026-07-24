# tests/performance/test_logging_performance.py
"""
Performance tests for logging components.
"""

import pytest
import time
import statistics
from app.utils.routing_decision_logger import RoutingDecisionLogger


@pytest.fixture
def decision_logger(tmp_path):
    return RoutingDecisionLogger(log_dir=str(tmp_path))


class TestLoggingPerformance:
    """Performance tests for logging"""
    
    def test_logging_latency(self, decision_logger):
        """Test logging latency < 10ms"""
        latencies = []
        
        for i in range(100):
            start = time.perf_counter()
            
            decision_logger.log_decision(
                agent_selected=f"agent-{i}",
                confidence_score=0.85,
                request_id=f"req-{i}",
                context={"test": True},
                response_time_ms=45.0
            )
            
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
        
        p50_latency = statistics.median(latencies)
        assert p50_latency < 10, f"Logging P50 latency {p50_latency}ms exceeds 10ms"
    
    def test_query_performance(self, decision_logger):
        """Test query performance"""
        # Log test data
        for i in range(1000):
            decision_logger.log_decision(
                agent_selected=f"agent-{i % 10}",
                confidence_score=0.80 + (i % 20) / 100,
                request_id=f"req-{i}",
                context={"index": i}
            )
        
        # Test query latency
        start = time.perf_counter()
        decisions = decision_logger.query_decisions(limit=100)
        query_time_ms = (time.perf_counter() - start) * 1000
        
        assert query_time_ms < 50, f"Query time {query_time_ms}ms exceeds 50ms"
        assert len(decisions) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])