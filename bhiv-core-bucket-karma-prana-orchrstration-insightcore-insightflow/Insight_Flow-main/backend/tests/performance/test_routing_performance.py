# tests/performance/test_routing_performance.py
"""
Performance tests for routing engine.

Verify that routing decisions meet latency SLAs.
"""

import pytest
import time
import statistics
from app.ml.weighted_scoring import WeightedScoringEngine


@pytest.fixture
def scoring_engine(tmp_path):
    config_file = tmp_path / "scoring_config.yaml"
    config_file.write_text("""
scoring_weights:
  rule_based: 0.4
  feedback_based: 0.4
  availability: 0.2
""")
    return WeightedScoringEngine(str(config_file))


class TestRoutingPerformance:
    """Performance tests for routing"""
    
    def test_scoring_latency_p50(self, scoring_engine):
        """Test P50 latency < 30ms"""
        latencies = []
        
        for i in range(100):
            start = time.perf_counter()
            
            scoring_engine.calculate_confidence(
                agent_id=f"agent-{i}",
                rule_based_score=0.80,
                feedback_score=0.85,
                availability_score=0.90
            )
            
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
        
        p50_latency = statistics.median(latencies)
        assert p50_latency < 30, f"P50 latency {p50_latency}ms exceeds 30ms SLA"
    
    def test_scoring_latency_p99(self, scoring_engine):
        """Test P99 latency < 100ms"""
        latencies = []
        
        for i in range(1000):
            start = time.perf_counter()
            
            scoring_engine.calculate_confidence(
                agent_id=f"agent-{i % 10}",
                rule_based_score=0.80 + (i % 20) / 100,
                feedback_score=0.85,
                availability_score=0.90
            )
            
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)
        
        latencies.sort()
        p99_idx = int(len(latencies) * 0.99)
        p99_latency = latencies[p99_idx]
        
        assert p99_latency < 100, f"P99 latency {p99_latency}ms exceeds 100ms SLA"
    
    def test_throughput(self, scoring_engine):
        """Test that we can process > 1000 req/s"""
        start_time = time.perf_counter()
        request_count = 0
        
        while time.perf_counter() - start_time < 1.0:  # 1 second
            scoring_engine.calculate_confidence(
                agent_id=f"agent-{request_count % 10}",
                rule_based_score=0.80,
                feedback_score=0.85,
                availability_score=0.90
            )
            request_count += 1
        
        throughput = request_count
        assert throughput > 1000, f"Throughput {throughput} req/s below 1000 req/s target"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])