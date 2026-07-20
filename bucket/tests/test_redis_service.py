import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from utils.redis_service import RedisService
import redis

class TestRedisService:
    """Test suite for Redis service functionality"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_client.get.return_value = "test_value"
        mock_client.delete.return_value = 1
        mock_client.lpush.return_value = 1
        mock_client.lrange.return_value = ['{"test": "data"}']
        mock_client.hset.return_value = 1
        mock_client.hget.return_value = '{"state": "test"}'
        mock_client.expire.return_value = True
        mock_client.ltrim.return_value = True
        return mock_client
    
    @pytest.fixture
    def redis_service(self, mock_redis_client):
        """Redis service with mocked client"""
        with patch('utils.redis_service.redis.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client
            service = RedisService()
            service.client = mock_redis_client
            service.connected = True
            return service
    
    def test_connection_success(self, mock_redis_client):
        """Test successful Redis connection"""
        with patch('utils.redis_service.redis.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client
            service = RedisService()
            assert service.connected is True
            assert service.client is not None
    
    def test_connection_failure(self):
        """Test Redis connection failure"""
        with patch('utils.redis_service.redis.Redis') as mock_redis:
            mock_redis.side_effect = redis.ConnectionError("Connection failed")
            service = RedisService()
            assert service.connected is False
            assert service.client is None
    
    def test_is_connected(self, redis_service):
        """Test connection status check"""
        assert redis_service.is_connected() is True
        
        # Test when ping fails
        redis_service.client.ping.side_effect = redis.ConnectionError()
        assert redis_service.is_connected() is False
    
    def test_store_execution_log(self, redis_service):
        """Test storing execution logs"""
        execution_id = "test_exec_123"
        agent_name = "test_agent"
        step = "test_step"
        data = {"key": "value"}
        
        redis_service.store_execution_log(execution_id, agent_name, step, data)
        
        # Verify lpush was called for execution logs
        redis_service.client.lpush.assert_called()
        redis_service.client.expire.assert_called()
    
    def test_store_agent_state(self, redis_service):
        """Test storing agent state"""
        agent_name = "test_agent"
        execution_id = "test_exec_123"
        state = {"status": "running"}
        
        redis_service.store_agent_state(agent_name, execution_id, state)
        
        redis_service.client.hset.assert_called()
        redis_service.client.expire.assert_called()
    
    def test_get_agent_state(self, redis_service):
        """Test retrieving agent state"""
        agent_name = "test_agent"
        execution_id = "test_exec_123"
        
        redis_service.client.hget.return_value = '{"status": "running"}'
        
        state = redis_service.get_agent_state(agent_name, execution_id)
        
        assert state == {"status": "running"}
        redis_service.client.hget.assert_called()
    
    def test_store_basket_execution(self, redis_service):
        """Test storing basket execution metadata"""
        basket_name = "test_basket"
        execution_id = "test_exec_123"
        config = {"agents": ["agent1", "agent2"]}
        
        redis_service.store_basket_execution(basket_name, execution_id, config)
        
        redis_service.client.hset.assert_called()
        redis_service.client.lpush.assert_called()
        redis_service.client.expire.assert_called()
    
    def test_update_basket_status(self, redis_service):
        """Test updating basket execution status"""
        basket_name = "test_basket"
        execution_id = "test_exec_123"
        status = "completed"
        result = {"output": "success"}
        
        redis_service.update_basket_status(basket_name, execution_id, status, result)
        
        redis_service.client.hset.assert_called()
    
    def test_get_execution_logs(self, redis_service):
        """Test retrieving execution logs"""
        execution_id = "test_exec_123"
        
        redis_service.client.lrange.return_value = [
            '{"execution_id": "test_exec_123", "step": "start"}',
            '{"execution_id": "test_exec_123", "step": "end"}'
        ]
        
        logs = redis_service.get_execution_logs(execution_id)
        
        assert len(logs) == 2
        assert logs[0]["execution_id"] == execution_id
        redis_service.client.lrange.assert_called()
    
    def test_store_agent_output(self, redis_service):
        """Test storing agent output"""
        execution_id = "test_exec_123"
        agent_name = "test_agent"
        output = {"result": "success"}
        
        redis_service.store_agent_output(execution_id, agent_name, output)
        
        redis_service.client.set.assert_called()
    
    def test_get_agent_output(self, redis_service):
        """Test retrieving agent output"""
        execution_id = "test_exec_123"
        agent_name = "test_agent"
        
        redis_service.client.get.return_value = '{"result": "success"}'
        
        output = redis_service.get_agent_output(execution_id, agent_name)
        
        assert output == {"result": "success"}
        redis_service.client.get.assert_called()
    
    def test_generate_execution_id(self, redis_service):
        """Test execution ID generation"""
        exec_id = redis_service.generate_execution_id()
        
        assert isinstance(exec_id, str)
        assert "_" in exec_id
        assert len(exec_id) > 10
    
    def test_get_stats(self, redis_service):
        """Test getting Redis statistics"""
        redis_service.client.info.return_value = {
            "used_memory_human": "1.5M",
            "connected_clients": 5,
            "total_commands_processed": 1000
        }
        
        stats = redis_service.get_stats()
        
        assert stats["connected"] is True
        assert "used_memory" in stats
        redis_service.client.info.assert_called()
    
    def test_disconnected_operations(self):
        """Test operations when Redis is disconnected"""
        service = RedisService()
        service.connected = False
        service.client = None
        
        # These should not raise exceptions
        service.store_execution_log("id", "agent", "step", {})
        service.store_agent_state("agent", "id", {})
        
        assert service.get_agent_state("agent", "id") is None
        assert service.get_execution_logs("id") == []
        assert service.get_agent_logs("agent") == []

if __name__ == "__main__":
    pytest.main([__file__])
