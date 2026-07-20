from typing import Dict, Any
from agents.finance import FinanceAgent
from agents.education import EducationAgent  
from agents.creator import CreatorAgent
from modules.sample_text.module import SampleTextModule
from db.memory import ContextMemory
from utils.logger import setup_logger
from app_config import DB_PATH

class Gateway:
    """Central gateway for routing requests to appropriate agents"""
    
    def __init__(self):
        self.agents = {
            "finance": FinanceAgent(),
            "education": EducationAgent(),
            "creator": CreatorAgent(),
            "sample_text": SampleTextModule()
        }
        self.memory = ContextMemory(DB_PATH)
        self.logger = setup_logger(__name__)
    
    def process_request(self, module: str, intent: str, user_id: str, 
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request and route to appropriate agent"""
        
        # Get user context
        context = self.memory.get_context(user_id) if user_id else []
        
        # Log request
        self.logger.info(
            f"Processing request for module: {module}, intent: {intent}",
            extra={"user_id": user_id, "request_data": {"module": module, "intent": intent, "data": data}}
        )
        
        # Route to agent
        if module not in self.agents:
            response = {
                "status": "error",
                "message": f"Unknown module: {module}",
                "result": None
            }
        else:
            agent = self.agents[module]
            try:
                if module == "sample_text":
                    response = agent.process(data, context)
                else:
                    response = agent.handle_request(intent, data, context)
            except Exception as e:
                response = {
                    "status": "error",
                    "message": f"Agent processing failed: {str(e)}",
                    "result": {}
                }
        
        # Store interaction
        if user_id:
            request_data = {"module": module, "intent": intent, "user_id": user_id, "data": data}
            self.memory.store_interaction(user_id, request_data, response)
        
        # Log response
        self.logger.info(
            f"Request processed with status: {response['status']}",
            extra={"user_id": user_id, "response_data": response}
        )
        
        return response