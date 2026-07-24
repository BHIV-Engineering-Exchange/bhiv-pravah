# tests/test_dashboard_service.py
"""
Tests for dashboard service.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.dashboard_service import DashboardService, get_dashboard_service


@pytest.fixture
def mock_routing_logger():
    """Mock routing decision logger"""
    logger = Mock()
    logger.query_decisions.return_value = [
        {
            "timestamp": "2025-01-21T10:00:00Z",
            "agent_selected": "nlp-001",
            "confidence_score": 0.85,
            "response_time_ms": 45.2
        },
        {
            "timestamp": "2025-01-21T10:01:00Z",
            "agent_selected": "nlp-002",
            "confidence_score": 0.72,
            "response_time_ms": 38.1
        },
        {
            "timestamp": "2025-01-21T10:02:00Z",
            "agent_selected": "nlp-001",
            "confidence_score": 0.91,
            "response_time_ms": 52.3
        }
    ]
    return logger


class TestDashboardService:
    """Test dashboard service functionality"""
    
    @patch('app.services.dashboard_service.get_routing_logger')
    def test_get_performance_metrics_success(self, mock_get_logger, mock_routing_logger):
        """Test successful performance metrics retrieval"""
        mock_get_logger.return_value = mock_routing_logger
        
        service = DashboardService()
        metrics = await service.get_performance_metrics(hours=24)
        
        assert metrics["total_decisions"] == 3
        assert metrics["average_confidence"] == pytest.approx(0.827, rel=1e-2)
        assert metrics["min_confidence"] == 0.72
        assert metrics["max_confidence"] == 0.91
        assert metrics["avg_response_time_ms"] == pytest.approx(45.2, rel=1e-1)
        assert len(metrics["top_agents"]) == 2
        assert metrics["top_agents"][0]["agent_id"] == "nlp-001"
        assert metrics["top_agents"][0]["count"] == 2
    
    @patch('app.services.dashboard_service.get_routing_logger')
    def test_get_performance_metrics_empty(self, mock_get_logger):
        """Test performance metrics with no data"""
        mock_logger = Mock()
        mock_logger.query_decisions.return_value = []
        mock_get_logger.return_value = mock_logger
        
        service = DashboardService()
        metrics = await service.get_performance_metrics(hours=24)
        
        assert metrics["total_decisions"] == 0
        assert metrics["average_confidence"] == 0
        assert metrics["top_agents"] == []
    
    @patch('app.services.dashboard_service.get_routing_logger')
    def test_get_routing_accuracy_success(self, mock_get_logger, mock_routing_logger):
        """Test successful accuracy metrics retrieval"""
        mock_get_logger.return_value = mock_routing_logger
        
        service = DashboardService()
        accuracy = await service.get_routing_accuracy(hours=24)
        
        assert accuracy["total_decisions"] == 3
        assert accuracy["high_confidence_decisions"] == 2  # 0.85 and 0.91 >= 0.75
        assert accuracy["accuracy_percentage"] == pytest.approx(66.67, rel=1e-1)
        assert accuracy["time_window_hours"] == 24
    
    @patch('app.services.dashboard_service.get_routing_logger')
    def test_get_agent_performance_success(self, mock_get_logger, mock_routing_logger):
        """Test successful agent performance retrieval"""
        mock_get_logger.return_value = mock_routing_logger
        
        service = DashboardService()
        agents = await service.get_agent_performance(hours=24)
        
        assert len(agents) == 2
        
        # Find nlp-001 stats
        nlp_001 = next(a for a in agents if a["agent_id"] == "nlp-001")
        assert nlp_001["total_decisions"] == 2
        assert nlp_001["avg_confidence"] == pytest.approx(0.88, rel=1e-2)
        assert nlp_001["min_confidence"] == 0.85
        assert nlp_001["max_confidence"] == 0.91
        
        # Find nlp-002 stats
        nlp_002 = next(a for a in agents if a["agent_id"] == "nlp-002")
        assert nlp_002["total_decisions"] == 1
        assert nlp_002["avg_confidence"] == 0.72
    
    def test_confidence_distribution(self):
        """Test confidence distribution calculation"""
        values = [0.1, 0.3, 0.6, 0.8, 0.9]
        distribution = DashboardService._get_distribution(values)
        
        assert distribution["0-0.25"] == 1
        assert distribution["0.25-0.5"] == 1
        assert distribution["0.5-0.75"] == 1
        assert distribution["0.75-1.0"] == 2
    
    def test_get_top_agents(self):
        """Test top agents calculation"""
        decisions = [
            {"agent_selected": "agent-1"},
            {"agent_selected": "agent-2"},
            {"agent_selected": "agent-1"},
            {"agent_selected": "agent-3"},
            {"agent_selected": "agent-1"}
        ]
        
        top_agents = DashboardService._get_top_agents(decisions, limit=2)
        
        assert len(top_agents) == 2
        assert top_agents[0]["agent_id"] == "agent-1"
        assert top_agents[0]["count"] == 3
        assert top_agents[1]["agent_id"] == "agent-2"
        assert top_agents[1]["count"] == 1
    
    def test_get_dashboard_service_singleton(self):
        """Test dashboard service singleton pattern"""
        service1 = get_dashboard_service()
        service2 = get_dashboard_service()
        
        assert service1 is service2