import redis
import json
import os
from typing import Dict, Any, Optional
from utils.logger import logger
from database.mongo_db import MongoDBClient
from dotenv import load_dotenv

load_dotenv()

class AgentRunner:
    def __init__(self, agent_name: str, stateful: bool = False):
        self.agent_name = agent_name
        self.stateful = stateful
        self.mongo_client = MongoDBClient()
        self.redis_client = None
        self.memory_fallback = {}
        
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis for agent {agent_name}")
        except (redis.ConnectionError, redis.RedisError) as e:
            logger.warning(f"Redis connection failed for {agent_name}: {e}. Using in-memory fallback")
            self.redis_client = None

    def store_state(self, key: str, value: Any) -> bool:
        try:
            state_data = json.dumps(value)
            if self.redis_client:
                self.redis_client.set(f"{self.agent_name}:{key}", state_data)
                logger.debug(f"Stored state in Redis for {self.agent_name}: {key}")
            else:
                self.memory_fallback[f"{self.agent_name}:{key}"] = state_data
                logger.debug(f"Stored state in memory for {self.agent_name}: {key}")
            self.mongo_client.store_log(self.agent_name, f"Stored state: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store state for {self.agent_name}: {e}")
            self.mongo_client.store_log(self.agent_name, f"State store error: {str(e)}")
            return False

    def retrieve_state(self, key: str) -> Optional[Any]:
        try:
            if self.redis_client:
                state_data = self.redis_client.get(f"{self.agent_name}:{key}")
            else:
                state_data = self.memory_fallback.get(f"{self.agent_name}:{key}")
            
            if state_data:
                result = json.loads(state_data)
                logger.debug(f"Retrieved state for {self.agent_name}: {key}")
                self.mongo_client.store_log(self.agent_name, f"Retrieved state: {key}")
                return result
            logger.warning(f"No state found for {self.agent_name}: {key}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve state for {self.agent_name}: {e}")
            self.mongo_client.store_log(self.agent_name, f"State retrieve error: {str(e)}")
            return None

    async def run(self, agent_module, input_data: Dict) -> Dict:
        try:
            if self.stateful:
                prev_state = self.retrieve_state("last_execution")
                if prev_state:
                    input_data["previous_state"] = prev_state
                result = await agent_module.process(input_data)
                self.store_state("last_execution", result)
            else:
                result = await agent_module.process(input_data)
            
            self.mongo_client.store_log(self.agent_name, f"Execution result: {result}")
            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_name} execution failed: {e}")
            self.mongo_client.store_log(self.agent_name, f"Execution error: {str(e)}")
            return {"error": str(e)}

    def close(self):
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.debug(f"Closed Redis connection for {self.agent_name}")
            except Exception as e:
                logger.error(f"Error closing Redis for {self.agent_name}: {e}")
        if self.mongo_client:
            self.mongo_client.close()