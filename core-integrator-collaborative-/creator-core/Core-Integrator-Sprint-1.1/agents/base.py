from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAgent(ABC):
    """Base class for all agents"""
    
    @abstractmethod
    def handle_request(self, intent: str, data: Dict[str, Any], 
                      context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle incoming request with optional context"""
        pass