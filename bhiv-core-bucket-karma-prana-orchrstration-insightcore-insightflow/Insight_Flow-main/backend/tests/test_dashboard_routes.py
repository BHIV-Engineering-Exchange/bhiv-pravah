# tests/test_dashboard_routes.py
"""
Tests for dashboard API routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user", "email": "test@example.com"}


@pytest.fixture
def mock_dashboard_service():
    """Mock dashboard service"""
    service = Mock()
    service.get_performance_metrics = AsyncMock(return_value={
        "total_decisions": 100,
        "average_confidence": 0.82,
        "min_confidence": 0.65,
        "max_confidence": 0.95,
        "confidence_distribution": {
            "0-0.25": 5,
            "0.25-0.5": 10,
            "0.5-0.75": 35,
            "0.75-1.0": 50
        },
        "avg_response_time_ms": 42.1,
        "top_agents": [
            {"agent_id": "nlp-001", "count": 45},
            {"agent_id": "nlp-002", "count": 30}
        ]
    })
    
    service.get_routing_accuracy = AsyncMock(return_value={
        "total_decisions": 100,
        "high_confidence_decisions": 75,
        "accuracy_percentage": 75.0,
        "time_window_hours": 24
    })
    
    service.get_agent_performance = AsyncMock(return_value=[
        {
            "agent_id": "nlp-001",
            "total_decisions": 45,
            "avg_confidence": 0.85,
            "min_confidence": 0.70,
            "max_confidence": 0.95
        },
        {
            "agent_id": "nlp-002",
            "total_decisions": 30,
            "avg_confidence": 0.78,
            "min_confidence": 0.65,
            "max_confidence": 0.90
        }
    ])
    
    return service


class TestDashboardRoutes:
    """Test dashboard API routes"""
    
    @patch('app.api.routes.dashboard.dashboard_service')
    def test_get_performance_metrics_success(self, mock_service, mock_dashboard_service):
        """Test successful performance metrics retrieval"""
        mock_service.get_performance_metrics = mock_dashboard_service.get_performance_metrics
        
        response = client.get("/dashboard/metrics/performance?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_decisions"] == 100
        assert data["average_confidence"] == 0.82
        
        mock_dashboard_service.get_performance_metrics.assert_called_once_with(hours=24)
    
    @patch('app.api.routes.dashboard.dashboard_service')
    def test_get_performance_metrics_custom_hours(self, mock_service, mock_dashboard_service):
        """Test performance metrics with custom hours parameter"""
        mock_service.get_performance_metrics = mock_dashboard_service.get_performance_metrics
        
        response = client.get("/dashboard/metrics/performance?hours=48")
        
        assert response.status_code == 200
        mock_dashboard_service.get_performance_metrics.assert_called_once_with(hours=48)
    
    @patch('app.api.routes.dashboard.dashboard_service')
    def test_get_routing_accuracy_success(self, mock_service, mock_dashboard_service):
        """Test successful accuracy metrics retrieval"""
        mock_service.get_routing_accuracy = mock_dashboard_service.get_routing_accuracy
        
        response = client.get("/dashboard/metrics/accuracy?hours=12")
        
        assert response.status_code == 200
        data = response.json()
        assert data["accuracy_percentage"] == 75.0
        
        mock_dashboard_service.get_routing_accuracy.assert_called_once_with(hours=12)
    
    @patch('app.api.routes.dashboard.dashboard_service')
    def test_get_agent_performance_success(self, mock_service, mock_dashboard_service):
        """Test successful agent performance retrieval"""
        mock_service.get_agent_performance = mock_dashboard_service.get_agent_performance
        
        response = client.get("/dashboard/metrics/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["agent_id"] == "nlp-001"
        
        mock_dashboard_service.get_agent_performance.assert_called_once_with(hours=24)
    
    def test_invalid_hours_parameter(self):
        """Test invalid hours parameter validation"""
        # Test hours too high
        response = client.get("/dashboard/metrics/performance?hours=1000")
        assert response.status_code == 422
        
        # Test hours too low
        response = client.get("/dashboard/metrics/performance?hours=0")
        assert response.status_code == 422