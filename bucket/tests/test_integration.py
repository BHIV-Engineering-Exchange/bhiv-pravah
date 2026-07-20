import pytest
import json
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from baskets.basket_manager import AgentBasket
from agents.agent_registry import AgentRegistry
from communication.event_bus import EventBus
from utils.redis_service import RedisService

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_basket_config(self):
        """Sample basket configuration for testing"""
        return {
            "basket_name": "test_integration_basket",
            "agents": ["financial_coordinator"],
            "execution_strategy": "sequential",
            "description": "Integration test basket"
        }
    
    @pytest.fixture
    def sample_input_data(self):
        """Sample input data for testing"""
        return {
            "user_id": "test_user_123",
            "financial_data": {
                "income": 50000,
                "expenses": {"housing": 1500, "food": 500},
                "assets": {"savings": 10000},
                "debts": {"credit_card": 2000}
            },
            "goals": [{"type": "emergency_fund", "target_amount": 15000}]
        }
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "mongodb" in data["services"]
        assert "redis" in data["services"]
    
    def test_agents_endpoint(self, client):
        """Test the agents listing endpoint"""
        response = client.get("/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_baskets_endpoint(self, client):
        """Test the baskets listing endpoint"""
        response = client.get("/baskets")
        assert response.status_code == 200
        
        data = response.json()
        assert "baskets" in data
        assert "count" in data
        assert isinstance(data["baskets"], list)
    
    def test_redis_status_endpoint(self, client):
        """Test Redis status endpoint"""
        response = client.get("/redis/status")
        # Should return either 200 (connected) or 503 (not connected)
        assert response.status_code in [200, 503]
    
    @patch('main.AgentBasket')
    def test_run_basket_endpoint_success(self, mock_basket_class, client, sample_basket_config):
        """Test successful basket execution via API"""
        # Mock the basket execution
        mock_basket = Mock()
        mock_basket.execution_id = "test_exec_123"
        mock_basket.execute = AsyncMock(return_value={"result": "success", "data": "test_output"})
        mock_basket_class.return_value = mock_basket
        
        # Create a temporary basket file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_basket_config, f)
            basket_file = Path(f.name)
        
        try:
            # Copy to baskets directory
            baskets_dir = Path("baskets")
            baskets_dir.mkdir(exist_ok=True)
            basket_path = baskets_dir / "test_integration_basket.json"
            basket_path.write_text(json.dumps(sample_basket_config))
            
            response = client.post("/run-basket", json={"basket_name": "test_integration_basket"})
            assert response.status_code == 200
            
            data = response.json()
            assert "result" in data
            assert "execution_metadata" in data
            
        finally:
            # Cleanup
            if basket_path.exists():
                basket_path.unlink()
            basket_file.unlink()
    
    def test_run_basket_endpoint_not_found(self, client):
        """Test basket execution with non-existent basket"""
        response = client.post("/run-basket", json={"basket_name": "non_existent_basket"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_run_basket_endpoint_no_input(self, client):
        """Test basket execution with no input"""
        response = client.post("/run-basket", json={})
        assert response.status_code == 400
        assert "must provide" in response.json()["detail"].lower()
    
    @patch('main.AgentBasket')
    def test_run_basket_endpoint_execution_error(self, mock_basket_class, client, sample_basket_config):
        """Test basket execution with error"""
        # Mock the basket execution to raise an error
        mock_basket = Mock()
        mock_basket.execute = AsyncMock(side_effect=Exception("Execution failed"))
        mock_basket_class.return_value = mock_basket
        
        response = client.post("/run-basket", json={"config": sample_basket_config})
        assert response.status_code == 500
        assert "execution failed" in response.json()["detail"].lower()
    
    def test_create_basket_endpoint(self, client):
        """Test basket creation endpoint"""
        basket_data = {
            "name": "test_created_basket",
            "agents": ["financial_coordinator"],
            "execution_strategy": "sequential",
            "description": "Test created basket"
        }
        
        response = client.post("/create-basket", json=basket_data)
        
        # Clean up created file
        basket_path = Path("baskets") / "test_created_basket.json"
        if basket_path.exists():
            basket_path.unlink()
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_created_basket" in data["message"]
    
    def test_create_basket_endpoint_no_name(self, client):
        """Test basket creation without name"""
        basket_data = {
            "agents": ["financial_coordinator"],
            "execution_strategy": "sequential"
        }

        response = client.post("/create-basket", json=basket_data)
        assert response.status_code == 400
        assert "name is required" in response.json()["detail"].lower()

    def test_delete_basket_endpoint_success(self, client):
        """Test successful basket deletion"""
        # First create a test basket
        basket_data = {
            "name": "test_delete_basket",
            "agents": ["financial_coordinator"],
            "execution_strategy": "sequential",
            "description": "Test basket for deletion"
        }

        create_response = client.post("/create-basket", json=basket_data)
        assert create_response.status_code == 200

        # Now delete it
        delete_response = client.delete("/baskets/test_delete_basket")
        assert delete_response.status_code == 200

        data = delete_response.json()
        assert data["success"] is True
        assert "test_delete_basket" in data["message"]
        assert "cleanup_summary" in data

    def test_delete_basket_endpoint_not_found(self, client):
        """Test deletion of non-existent basket"""
        response = client.delete("/baskets/non_existent_basket")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_logs_endpoint(self, client):
        """Test logs retrieval endpoint"""
        response = client.get("/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
    
    def test_logs_endpoint_with_agent_filter(self, client):
        """Test logs retrieval with agent filter"""
        response = client.get("/logs?agent=financial_coordinator")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data

class TestEndToEndBasketExecution:
    """End-to-end tests for basket execution"""
    
    @pytest.fixture
    def mock_redis_service(self):
        """Mock Redis service for testing"""
        redis_service = Mock(spec=RedisService)
        redis_service.generate_execution_id.return_value = "e2e_test_123"
        redis_service.store_execution_log = Mock()
        redis_service.store_basket_execution = Mock()
        redis_service.update_basket_status = Mock()
        redis_service.store_agent_state = Mock()
        redis_service.store_agent_output = Mock()
        redis_service.is_connected.return_value = True
        return redis_service
    
    @pytest.fixture
    def mock_registry(self):
        """Mock registry with test agents"""
        registry = Mock(spec=AgentRegistry)
        registry.get_agent.return_value = {
            "name": "test_agent",
            "module_path": "tests.mock_agent",
            "capabilities": {"memory_access": False}
        }
        registry.validate_compatibility.return_value = True
        return registry
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        event_bus = Mock(spec=EventBus)
        event_bus.publish = AsyncMock()
        return event_bus
    
    @pytest.mark.asyncio
    async def test_complete_basket_execution_flow(self, mock_registry, mock_event_bus, mock_redis_service):
        """Test complete basket execution from start to finish"""
        basket_spec = {
            "basket_name": "e2e_test_basket",
            "agents": ["test_agent1", "test_agent2"],
            "execution_strategy": "sequential",
            "description": "End-to-end test basket"
        }
        
        # Mock successful agent execution
        mock_agent_module = Mock()
        mock_runner = Mock()
        mock_runner.run = AsyncMock(side_effect=[
            {"result": "agent1_output", "step": 1},
            {"result": "agent2_output", "step": 2, "final": True}
        ])
        mock_runner.close = Mock()
        
        with patch('baskets.basket_manager.MongoDBClient') as mock_mongo, \
             patch('baskets.basket_manager.importlib.import_module', return_value=mock_agent_module), \
             patch('baskets.basket_manager.AgentRunner', return_value=mock_runner), \
             patch('baskets.basket_manager.Path.mkdir'), \
             patch('baskets.basket_manager.Path.open', create=True) as mock_open:
            
            # Setup MongoDB mock
            mock_mongo_client = Mock()
            mock_mongo_client.db = Mock()
            mock_mongo_client.store_log = Mock()
            mock_mongo.return_value = mock_mongo_client
            
            # Setup file mock
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Create and execute basket
            basket = AgentBasket(basket_spec, mock_registry, mock_event_bus, mock_redis_service)
            
            input_data = {"user_id": "test_user", "data": "test_input"}
            result = await basket.execute(input_data)
            
            # Verify successful execution
            assert "error" not in result
            assert result["result"] == "agent2_output"
            assert result["final"] is True
            
            # Verify Redis logging calls
            assert mock_redis_service.store_execution_log.call_count >= 4  # Start, agent1, agent2, completion
            mock_redis_service.store_basket_execution.assert_called_once()
            mock_redis_service.update_basket_status.assert_called_with(
                "e2e_test_basket", "e2e_test_123", "completed", result
            )
            
            # Verify agent execution
            assert mock_runner.run.call_count == 2
            mock_event_bus.publish.assert_called()

class TestAgentSpecific:
    """Tests for specific agents with sample inputs"""

    def load_sample_input(self, agent_name):
        """Load sample input for an agent"""
        input_file = Path(__file__).parent / "sample_inputs" / f"{agent_name}_input.json"
        if input_file.exists():
            with input_file.open() as f:
                return json.load(f)
        return {"input": "default_test_input"}

    @pytest.mark.asyncio
    async def test_financial_coordinator_with_sample_input(self):
        """Test financial coordinator with realistic input"""
        sample_input = self.load_sample_input("financial_coordinator")

        # Mock the agent execution
        with patch('agents.agent_runner.AgentRunner') as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run = AsyncMock(return_value={
                "recommendations": [
                    {"type": "budget_optimization", "priority": "high"},
                    {"type": "emergency_fund", "priority": "medium"}
                ],
                "analysis": {
                    "debt_to_income_ratio": 0.26,
                    "savings_rate": 0.16,
                    "financial_health_score": 75
                }
            })
            mock_runner.close = Mock()
            mock_runner_class.return_value = mock_runner

            # Test would run the agent here
            # This is a placeholder for actual agent testing
            assert sample_input["user_id"] == "user_123"
            assert "financial_data" in sample_input
            assert "goals" in sample_input

    @pytest.mark.asyncio
    async def test_cashflow_analyzer_with_sample_input(self):
        """Test cashflow analyzer with realistic input"""
        sample_input = self.load_sample_input("cashflow_analyzer")

        # Verify sample input structure
        assert "transactions" in sample_input
        assert "analysis_type" in sample_input
        assert len(sample_input["transactions"]) > 0

        # Mock expected output
        expected_output = {
            "cash_flow_summary": {
                "total_income": 6000,
                "total_expenses": 2600,
                "net_cash_flow": 3400
            },
            "category_analysis": {
                "housing": {"amount": 1500, "percentage": 57.7},
                "food": {"amount": 300, "percentage": 11.5}
            },
            "trends": {
                "monthly_trend": "positive",
                "spending_pattern": "consistent"
            }
        }

        # This would be the actual agent test
        assert sample_input["time_period"] == "monthly"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
