"""
LangGraph Service Monitoring
Basic monitoring utilities following BHIV pattern
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LangGraphMonitor:
    """Basic monitoring for LangGraph service"""
    
    def __init__(self):
        self.workflow_count = 0
        self.error_count = 0
        self.start_time = datetime.now(timezone.utc)
    
    def log_workflow_start(self, workflow_id: str, workflow_type: str):
        """Log workflow start"""
        self.workflow_count += 1
        logger.info(f"Workflow started: {workflow_id} ({workflow_type})")
    
    def log_workflow_error(self, workflow_id: str, error: str):
        """Log workflow error"""
        self.error_count += 1
        logger.error(f"Workflow error: {workflow_id} - {error}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        uptime = datetime.now(timezone.utc) - self.start_time
        
        return {
            "status": "healthy",
            "uptime_seconds": int(uptime.total_seconds()),
            "workflows_processed": self.workflow_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.workflow_count, 1),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global monitor instance
monitor = LangGraphMonitor()