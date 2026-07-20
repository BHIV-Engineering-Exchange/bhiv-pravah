import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
from baskets.basket_manager import AgentBasket
from agents.agent_registry import AgentRegistry
from communication.event_bus import EventBus
from utils.redis_service import RedisService

class TestAgentBasket:
    """Test suite for AgentBasket functionality"""
    
    @pytest.fixture
    def mock_registry(self):
        """Mock agent registry"""
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
    
    @pytest.fixture
    def mock_redis_service(self):
        """Mock Redis service"""
        redis_service = Mock(spec=RedisService)
        redis_service.generate_execution_id.return_value = "test_exec_123"
        redis_service.store_execution_log = Mock()
        redis_service.store_basket_execution = Mock()
        redis_service.update_basket_status = Mock()
        redis_service.store_agent_state = Mock()
        redis_service.store_agent_output = Mock()
        return redis_service
    
    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoDB client"""
        with patch('baskets.basket_manager.MongoDBClient') as mock_mongo:
            mock_client = Mock()
            mock_client.db = Mock()  # Simulate successful connection
            mock_client.store_log = Mock()
            mock_mongo.return_value = mock_client
            return mock_client
    
    @pytest.fixture
    def sample_basket_spec(self):
        """Sample basket specification"""
        return {
            "basket_name": "test_basket",
            "agents": ["test_agent1", "test_agent2"],
            "execution_strategy": "sequential",
            "description": "Test basket for unit testing"
        }
    
    @pytest.fixture
    def agent_basket(self, sample_basket_spec, mock_registry, mock_event_bus, mock_redis_service, mock_mongo_client):
        """Create AgentBasket instance for testing"""
        with patch('baskets.basket_manager.Path.mkdir'):
            basket = AgentBasket(sample_basket_spec, mock_registry, mock_event_bus, mock_redis_service)
            return basket
    
    def test_basket_initialization(self, agent_basket, mock_redis_service):
        """Test basket initialization"""
        assert agent_basket.name == "test_basket"
        assert agent_basket.agents == ["test_agent1", "test_agent2"]
        assert agent_basket.strategy == "sequential"
        assert agent_basket.execution_id == "test_exec_123"
        
        # Verify Redis calls
        mock_redis_service.store_execution_log.assert_called()
        mock_redis_service.store_basket_execution.assert_called()
    
    def test_invalid_basket_no_agents(self, mock_registry, mock_event_bus, mock_redis_service, mock_mongo_client):
        """Test basket initialization with no agents"""
        basket_spec = {
            "basket_name": "empty_basket",
            "agents": [],
            "execution_strategy": "sequential"
        }
        
        with pytest.raises(ValueError, match="No agents specified"):
            AgentBasket(basket_spec, mock_registry, mock_event_bus, mock_redis_service)
    
    def test_invalid_execution_strategy(self, mock_registry, mock_event_bus, mock_redis_service, mock_mongo_client):
        """Test basket initialization with invalid strategy"""
        basket_spec = {
            "basket_name": "invalid_basket",
            "agents": ["test_agent"],
            "execution_strategy": "invalid_strategy"
        }
        
        with pytest.raises(ValueError, match="Invalid execution strategy"):
            AgentBasket(basket_spec, mock_registry, mock_event_bus, mock_redis_service)
    
    @pytest.mark.asyncio
    async def test_execute_sequential_success(self, agent_basket, mock_registry, mock_redis_service):
        """Test successful sequential execution"""
        # Mock agent module and runner
        mock_agent_module = Mock()
        mock_runner = Mock()
        mock_runner.run = AsyncMock(return_value={"result": "success", "step": 1})
        mock_runner.close = Mock()
        
        with patch('baskets.basket_manager.importlib.import_module', return_value=mock_agent_module), \
             patch('baskets.basket_manager.AgentRunner', return_value=mock_runner), \
             patch('baskets.basket_manager.Path.open', create=True) as mock_open:
            
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            input_data = {"input": "test"}
            result = await agent_basket.execute(input_data)
            
            assert "error" not in result
            assert result["result"] == "success"
            
            # Verify Redis logging
            assert mock_redis_service.store_execution_log.call_count >= 2
            mock_redis_service.update_basket_status.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, agent_basket, mock_registry, mock_redis_service):
        """Test execution when agent is not found"""
        mock_registry.get_agent.return_value = None
        
        with patch('baskets.basket_manager.Path.open', create=True):
            input_data = {"input": "test"}
            result = await agent_basket.execute(input_data)
            
            assert "error" in result
            assert "not found" in result["error"]
            
            # Verify error logging
            mock_redis_service.update_basket_status.assert_called_with(
                agent_basket.name, agent_basket.execution_id, "failed", result
            )
    
    @pytest.mark.asyncio
    async def test_execute_compatibility_error(self, agent_basket, mock_registry, mock_redis_service):
        """Test execution with input compatibility error"""
        mock_registry.validate_compatibility.return_value = False
        
        with patch('baskets.basket_manager.importlib.import_module'), \
             patch('baskets.basket_manager.AgentRunner'), \
             patch('baskets.basket_manager.Path.open', create=True):
            
            input_data = {"input": "test"}
            result = await agent_basket.execute(input_data)
            
            assert "error" in result
            assert "incompatible" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_agent_execution_error(self, agent_basket, mock_registry, mock_redis_service):
        """Test execution when agent raises exception"""
        mock_agent_module = Mock()
        mock_runner = Mock()
        mock_runner.run = AsyncMock(side_effect=Exception("Agent execution failed"))
        mock_runner.close = Mock()
        
        with patch('baskets.basket_manager.importlib.import_module', return_value=mock_agent_module), \
             patch('baskets.basket_manager.AgentRunner', return_value=mock_runner), \
             patch('baskets.basket_manager.Path.open', create=True):
            
            input_data = {"input": "test"}
            result = await agent_basket.execute(input_data)
            
            assert "error" in result
            assert "Agent execution failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_agent_returns_error(self, agent_basket, mock_registry, mock_redis_service):
        """Test execution when agent returns error result"""
        mock_agent_module = Mock()
        mock_runner = Mock()
        mock_runner.run = AsyncMock(return_value={"error": "Agent internal error"})
        mock_runner.close = Mock()
        
        with patch('baskets.basket_manager.importlib.import_module', return_value=mock_agent_module), \
             patch('baskets.basket_manager.AgentRunner', return_value=mock_runner), \
             patch('baskets.basket_manager.Path.open', create=True):
            
            input_data = {"input": "test"}
            result = await agent_basket.execute(input_data)
            
            assert "error" in result
            assert "Agent internal error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_parallel_fallback(self, mock_registry, mock_event_bus, mock_redis_service, mock_mongo_client):
        """Test parallel execution falls back to sequential"""
        basket_spec = {
            "basket_name": "parallel_basket",
            "agents": ["test_agent"],
            "execution_strategy": "parallel"
        }
        
        with patch('baskets.basket_manager.Path.mkdir'):
            basket = AgentBasket(basket_spec, mock_registry, mock_event_bus, mock_redis_service)
            
            mock_agent_module = Mock()
            mock_runner = Mock()
            mock_runner.run = AsyncMock(return_value={"result": "success"})
            mock_runner.close = Mock()
            
            with patch('baskets.basket_manager.importlib.import_module', return_value=mock_agent_module), \
                 patch('baskets.basket_manager.AgentRunner', return_value=mock_runner), \
                 patch('baskets.basket_manager.Path.open', create=True):
                
                input_data = {"input": "test"}
                result = await basket.execute(input_data)
                
                assert "error" not in result
                assert result["result"] == "success"
    
    def test_close(self, agent_basket):
        """Test basket cleanup"""
        agent_basket.close()
        # Should not raise any exceptions

if __name__ == "__main__":
    pytest.main([__file__])
