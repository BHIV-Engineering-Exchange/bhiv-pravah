# app/utils/routing_decision_logger.py
"""
Routing Decision Logger: Audit trail for all routing decisions.

Logs every routing decision with full breakdown for debugging and analytics.
Stores in structured JSON Lines format for easy querying.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class RoutingDecisionLogger:
    """
    Logs all routing decisions for audit trail and analytics.
    
    Log format (JSON Lines):
    {
        "timestamp": "2025-10-29T16:15:00.123Z",
        "request_id": "req-abc123def456",
        "agent_selected": "nlp-001",
        "confidence_score": 0.87,
        "score_breakdown": {...},
        "alternatives": [...],
        "context_summary": "nlp_task, priority=normal",
        "decision_reasoning": "Best match based on weighted feedback scores",
        "response_time_ms": 45
    }
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_file: str = "routing_decisions.jsonl",
        retention_days: int = 30
    ):
        """
        Initialize routing decision logger.
        
        Args:
            log_dir: Directory for log files
            log_file: Log filename
            retention_days: Days to keep logs
        """
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / log_file
        self.retention_days = retention_days
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"RoutingDecisionLogger initialized: {self.log_file}"
        )
    
    def log_decision(
        self,
        agent_selected: str,
        confidence_score: float,
        request_id: Optional[str],
        context: Dict[str, Any],
        score_breakdown: Optional[Dict[str, Any]] = None,
        alternatives: Optional[list] = None,
        response_time_ms: Optional[float] = None,
        reasoning: Optional[str] = None
    ) -> bool:
        """
        Log a routing decision.
        
        Args:
            agent_selected: Selected agent ID
            confidence_score: Final confidence score (0-1)
            request_id: Request identifier
            context: Request context
            score_breakdown: Detailed score components
            alternatives: Alternative agent options
            response_time_ms: Decision time in milliseconds
            reasoning: Decision reasoning string
        
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id or "unknown",
                "agent_selected": agent_selected,
                "confidence_score": float(confidence_score),
                "score_breakdown": score_breakdown or {},
                "alternatives": alternatives or [],
                "context_summary": self._summarize_context(context),
                "decision_reasoning": reasoning or "Standard routing",
            }
            
            if response_time_ms is not None:
                log_entry["response_time_ms"] = float(response_time_ms)
            
            # Atomic write to prevent corruption
            self._atomic_write(json.dumps(log_entry) + '\n')
            
            logger.debug(
                f"Logged routing decision: {agent_selected} "
                f"(confidence={confidence_score:.2f})"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")
            return False
    
    def query_decisions(
        self,
        agent_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Query routing decisions from logs.
        
        Args:
            agent_id: Filter by agent ID
            date_from: From datetime (ISO format)
            date_to: To datetime (ISO format)
            limit: Maximum results to return
        
        Returns:
            List of matching decisions
        """
        try:
            results = []
            
            if not self.log_file.exists():
                logger.warning(f"Log file not found: {self.log_file}")
                return []
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    entry = json.loads(line)
                    
                    # Apply filters
                    if agent_id and entry.get("agent_selected") != agent_id:
                        continue
                    
                    if date_from and entry.get("timestamp") < date_from:
                        continue
                    
                    if date_to and entry.get("timestamp") > date_to:
                        continue
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
            
            logger.debug(
                f"Query returned {len(results)} routing decisions"
            )
            return results
        
        except Exception as e:
            logger.error(f"Error querying routing decisions: {str(e)}")
            return []
    
    def get_statistics(
        self,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about routing decisions.
        
        Args:
            agent_id: Specific agent or None for all
        
        Returns:
            Dictionary with statistics
        """
        try:
            decisions = self.query_decisions(
                agent_id=agent_id,
                limit=10000
            )
            
            if not decisions:
                return {"error": "No decisions found"}
            
            confidences = [d.get("confidence_score", 0) for d in decisions]
            response_times = [
                d.get("response_time_ms", 0) for d in decisions if "response_time_ms" in d
            ]
            
            stats = {
                "total_decisions": len(decisions),
                "avg_confidence": sum(confidences) / len(confidences),
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "unique_agents": len(set(
                    d.get("agent_selected") for d in decisions
                )),
            }
            
            if response_times:
                stats["avg_response_time_ms"] = sum(response_times) / len(response_times)
                stats["max_response_time_ms"] = max(response_times)
            
            return stats
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_old_logs(self) -> int:
        """
        Delete logs older than retention period.
        
        Returns:
            Number of days of logs deleted
        """
        try:
            cutoff_date = (
                datetime.utcnow() - timedelta(days=self.retention_days)
            ).isoformat()
            
            if not self.log_file.exists():
                return 0
            
            # Read all logs and filter
            remaining_logs = []
            deleted_count = 0
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get("timestamp", "") > cutoff_date:
                            remaining_logs.append(line)
                        else:
                            deleted_count += 1
            
            # Write back filtered logs
            with open(self.log_file, 'w') as f:
                f.writelines(remaining_logs)
            
            logger.info(
                f"Deleted {deleted_count} old log entries "
                f"(before {cutoff_date})"
            )
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {str(e)}")
            return 0
    
    def _atomic_write(self, content: str) -> None:
        """
        Atomically write content to log file to prevent corruption.
        
        Args:
            content: Content to write
        """
        import tempfile
        
        # Write to temporary file first
        temp_file = self.log_file.with_suffix('.tmp')
        
        try:
            # If log file exists, copy existing content to temp file
            if self.log_file.exists():
                with open(self.log_file, 'r') as src, open(temp_file, 'w') as dst:
                    dst.write(src.read())
                    dst.write(content)
            else:
                # New file
                with open(temp_file, 'w') as f:
                    f.write(content)
            
            # Atomic move (rename) - this is atomic on most filesystems
            temp_file.replace(self.log_file)
            
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    @staticmethod
    def _summarize_context(context: Dict[str, Any]) -> str:
        """Create summary string from context"""
        parts = []
        
        if "agent_type" in context:
            parts.append(context["agent_type"])
        
        if "priority" in context:
            parts.append(f"priority={context['priority']}")
        
        if "user_id" in context:
            parts.append(f"user={context['user_id'][:8]}")
        
        return ", ".join(parts) if parts else "standard"


# Global logger instance
_routing_logger: Optional[RoutingDecisionLogger] = None


def get_routing_logger() -> RoutingDecisionLogger:
    """Get or create routing decision logger instance"""
    global _routing_logger
    if _routing_logger is None:
        _routing_logger = RoutingDecisionLogger()
    return _routing_logger