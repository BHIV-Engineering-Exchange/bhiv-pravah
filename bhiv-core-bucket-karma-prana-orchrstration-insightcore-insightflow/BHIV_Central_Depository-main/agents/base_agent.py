from abc import ABC, abstractmethod
from communication.event_bus import EventBus
from database.mongo_db import MongoDBClient
from utils.logger import logger
from typing import Dict

class BaseAgent(ABC):
    def __init__(self, name: str, event_bus: EventBus):
        self.name = name
        self.event_bus = event_bus
        self.mongo_client = MongoDBClient()
        if not self.event_bus:
            logger.error("EventBus not provided")
            raise ValueError("EventBus not provided")
        if not self.mongo_client.db:
            logger.error("MongoDBClient initialization failed")
            raise ValueError("MongoDBClient initialization failed")
        try:
            self.event_bus.subscribe(f"{self.name}_input", self.process_message)
            logger.info(f"Agent {self.name} subscribed to event bus")
        except Exception as e:
            logger.error(f"Failed to subscribe to event bus: {e}")
            raise

    @abstractmethod
    async def process_message(self, message: Dict) -> Dict:
        pass

    async def send_message(self, target_agent: str, message: Dict) -> bool:
        try:
            await self.event_bus.publish(f"{target_agent}_input", {
                "sender": self.name,
                "content": message
            })
            self.mongo_client.store_log(self.name, f"Sent message to {target_agent}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {target_agent}: {e}")
            self.mongo_client.store_log(self.name, f"Failed to send message to {target_agent}: {str(e)}")
            return False