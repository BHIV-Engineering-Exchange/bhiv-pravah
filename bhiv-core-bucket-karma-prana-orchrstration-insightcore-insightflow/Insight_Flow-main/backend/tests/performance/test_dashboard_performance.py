# tests/performance/test_dashboard_performance.py
"""
Performance tests for dashboard service.
"""

import pytest
import time
import asyncio
from app.services.dashboard_service import DashboardService
from app.utils.routing_decision_logger import RoutingDecisionLogger


@pytest.fixture
def dashboard_service(tmp_path):
    logger = RoutingDecisionLogger(log_dir=str(tmp_path))
    service = DashboardService()
    service.decision_logger = logger
    return service, logger


class TestDashboardPerformance:
    """Performance tests for dashboard"""
    
    @pytest.mark.asyncio
    async def test_metrics_calculation_performance(self, dashboard_service):
        """Test dashboard metrics calculation performance"""
        service, logger = dashboard_service
        
        # Generate test data
        for i in range(1000):
            logger.log_decision(
                agent_selected=f"agent-{i % 10}",
                confidence_score=0.70 + (i % 30) / 100,
                request_id=f"req-{i}",
                context={"index": i},
                response_time_ms=30 + (i % 50)
            )
        
        # Test performance metrics calculation
        start = time.perf_counter()
        metrics = await service.get_performance_metrics(hours=24)
        calc_time_ms = (time.perf_counter() - start) * 1000
        
        assert calc_time_ms < 100, f"Metrics calculation {calc_time_ms}ms exceeds 100ms"
        assert metrics["total_decisions"] == 1000
    
    @pytest.mark.asyncio
    async def test_agent_performance_calculation(self, dashboard_service):
        """Test agent performance calculation speed"""
        service, logger = dashboard_service
        
        # Generate test data for multiple agents
        for i in range(500):
            logger.log_decision(
                agent_selected=f"agent-{i % 20}",
                confidence_score=0.75 + (i % 25) / 100,
                request_id=f"req-{i}",
                context={"agent_type": "nlp"}
            )
        
        # Test agent performance calculation
        start = time.perf_counter()
        agents = await service.get_agent_performance(hours=24)
        calc_time_ms = (time.perf_counter() - start) * 1000
        
        assert calc_time_ms < 50, f"Agent performance calculation {calc_time_ms}ms exceeds 50ms"
        assert len(agents) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])