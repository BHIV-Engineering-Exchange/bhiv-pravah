# tests/test_admin_routes.py
"""
Tests for admin API routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user", "email": "test@example.com"}


@pytest.fixture
def mock_routing_logger():
    """Mock routing decision logger"""
    logger = Mock()
    logger.query_decisions.return_value = [
        {
            "timestamp": "2025-01-21T10:00:00Z",
            "request_id": "req-123",
            "agent_selected": "nlp-001",
            "confidence_score": 0.85,
            "score_breakdown": {"rule_based": 0.8, "feedback": 0.9},
            "alternatives": ["nlp-002"],
            "context_summary": "nlp_task, priority=normal",
            "decision_reasoning": "Best match",
            "response_time_ms": 45.2
        }
    ]
    logger.get_statistics.return_value = {
        "total_decisions": 100,
        "avg_confidence": 0.82,
        "min_confidence": 0.65,
        "max_confidence": 0.95,
        "unique_agents": 5,
        "avg_response_time_ms": 42.1
    }
    logger.cleanup_old_logs.return_value = 25
    return logger


class TestAdminRoutes:
    """Test admin API routes"""
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_routing_logs_success(self, mock_get_logger, mock_auth, mock_user, mock_routing_logger):
        """Test successful routing logs retrieval"""
        mock_auth.return_value = mock_user
        mock_get_logger.return_value = mock_routing_logger
        
        response = client.get("/admin/routing-logs?limit=50")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert len(data["decisions"]) == 1
        assert "timestamp" in data
        
        # Verify logger was called with correct parameters
        mock_routing_logger.query_decisions.assert_called_once_with(
            agent_id=None,
            date_from=None,
            date_to=None,
            limit=50
        )
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_routing_logs_with_filters(self, mock_get_logger, mock_auth, mock_user, mock_routing_logger):
        """Test routing logs with filters"""
        mock_auth.return_value = mock_user
        mock_get_logger.return_value = mock_routing_logger
        
        response = client.get(
            "/admin/routing-logs"
            "?agent_id=nlp-001"
            "&date_from=2025-01-21T00:00:00Z"
            "&date_to=2025-01-21T23:59:59Z"
            "&limit=25"
        )
        
        assert response.status_code == 200
        mock_routing_logger.query_decisions.assert_called_once_with(
            agent_id="nlp-001",
            date_from="2025-01-21T00:00:00Z",
            date_to="2025-01-21T23:59:59Z",
            limit=25
        )
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_routing_logs_error(self, mock_get_logger, mock_auth, mock_user):
        """Test routing logs error handling"""
        mock_auth.return_value = mock_user
        mock_get_logger.side_effect = Exception("Logger error")
        
        response = client.get("/admin/routing-logs")
        
        assert response.status_code == 500
        assert "Error retrieving logs" in response.json()["detail"]
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_routing_statistics_success(self, mock_get_logger, mock_auth, mock_user, mock_routing_logger):
        """Test successful statistics retrieval"""
        mock_auth.return_value = mock_user
        mock_get_logger.return_value = mock_routing_logger
        
        response = client.get("/admin/routing-statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "statistics" in data
        assert data["statistics"]["total_decisions"] == 100
        assert data["statistics"]["avg_confidence"] == 0.82
        assert "timestamp" in data
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_routing_statistics_with_agent_filter(self, mock_get_logger, mock_auth, mock_user, mock_routing_logger):
        """Test statistics with agent filter"""
        mock_auth.return_value = mock_user
        mock_get_logger.return_value = mock_routing_logger
        
        response = client.get("/admin/routing-statistics?agent_id=nlp-001")
        
        assert response.status_code == 200
        mock_routing_logger.get_statistics.assert_called_once_with(agent_id="nlp-001")
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_cleanup_logs_success(self, mock_get_logger, mock_auth, mock_user, mock_routing_logger):
        """Test successful log cleanup"""
        mock_auth.return_value = mock_user
        mock_get_logger.return_value = mock_routing_logger
        
        response = client.post("/admin/cleanup-logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_entries"] == 25
        assert "Deleted 25 old log entries" in data["message"]
        assert "timestamp" in data
        
        mock_routing_logger.cleanup_old_logs.assert_called_once()
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_cleanup_logs_error(self, mock_get_logger, mock_auth, mock_user):
        """Test log cleanup error handling"""
        mock_auth.return_value = mock_user
        mock_get_logger.side_effect = Exception("Cleanup error")
        
        response = client.post("/admin/cleanup-logs")
        
        assert response.status_code == 500
        assert "Error cleaning logs" in response.json()["detail"]
    
    @patch('app.api.routes.admin.get_current_user')
    @patch('app.api.routes.admin.get_feedback_service')
    @patch('app.api.routes.admin.get_scoring_engine')
    @patch('app.api.routes.admin.get_routing_logger')
    def test_get_system_health_success(self, mock_get_logger, mock_get_scoring, mock_get_feedback, mock_auth, mock_user):
        """Test successful system health check"""
        mock_auth.return_value = mock_user
        
        # Mock feedback service
        mock_feedback = Mock()
        mock_feedback.health_check.return_value = True
        mock_feedback.get_metrics.return_value = {"cache_hits": 100, "cache_misses": 10}
        mock_get_feedback.return_value = mock_feedback
        
        # Mock scoring engine
        mock_scoring = Mock()
        mock_scoring.weights = {"rule_based": 0.4, "feedback": 0.4, "availability": 0.2}
        mock_get_scoring.return_value = mock_scoring
        
        # Mock routing logger
        mock_logger = Mock()
        mock_logger.get_statistics.return_value = {"total_decisions": 50}
        mock_get_logger.return_value = mock_logger
        
        response = client.get("/admin/system-health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["system_status"] == "healthy"
        assert "services" in data
        assert data["services"]["feedback_service"]["status"] == "healthy"
        assert data["services"]["scoring_engine"]["status"] == "healthy"
        assert data["services"]["routing_logger"]["status"] == "healthy"
    
    def test_unauthorized_access(self):
        """Test unauthorized access to admin endpoints"""
        # Without authentication, should get 401 or 403
        response = client.get("/admin/routing-logs")
        assert response.status_code in [401, 403]
        
        response = client.get("/admin/routing-statistics")
        assert response.status_code in [401, 403]
        
        response = client.post("/admin/cleanup-logs")
        assert response.status_code in [401, 403]
        
        response = client.get("/admin/system-health")
        assert response.status_code in [401, 403]
    
    @patch('app.api.routes.admin.get_current_user')
    def test_invalid_limit_parameter(self, mock_auth, mock_user):
        """Test invalid limit parameter validation"""
        mock_auth.return_value = mock_user
        
        # Test limit too high
        response = client.get("/admin/routing-logs?limit=2000")
        assert response.status_code == 422
        
        # Test limit too low
        response = client.get("/admin/routing-logs?limit=0")
        assert response.status_code == 422