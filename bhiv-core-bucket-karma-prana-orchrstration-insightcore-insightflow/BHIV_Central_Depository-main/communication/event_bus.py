import asyncio
from typing import Callable, Dict, List
from utils.logger import logger  # Centralized logger

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe a callback to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed callback to event {event_type}")

    async def publish(self, event_type: str, message: Dict):
        """Publish an event to all subscribers."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Error in callback for event {event_type}: {e}")