from datetime import datetime
from app.utils.database import db_manager
from app.utils.helpers import load_json, save_json
import logging

logger = logging.getLogger(__name__)

class DecisionEngine:
    """Decision logging and tracking engine"""
    
    @staticmethod
    def log_decision(candidate_id: int, decision: str, score: int, reasoning: str, hr_name: str = "System"):
        """Log HR decision with full context"""
        try:
            decision_data = {
                "candidate_id": candidate_id,
                "decision": decision,
                "score": score,
                "reasoning": reasoning,
                "hr_name": hr_name,
                "timestamp": datetime.now().isoformat(),
                "decision_id": f"DEC_{candidate_id}_{int(datetime.now().timestamp())}"
            }
            
            # Log to database
            db_manager.log_system_event(
                "INFO",
                "decision_logged",
                f"HR decision: {decision} for candidate {candidate_id}",
                decision_data
            )
            
            # Log to decision history file
            decisions = load_json("feedback/decision_history.json")
            if not isinstance(decisions, list):
                decisions = []
            
            decisions.append(decision_data)
            save_json("feedback/decision_history.json", decisions)
            
            logger.info(f"Decision logged: {decision} for candidate {candidate_id}")
            return decision_data["decision_id"]
            
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            return None
    
    @staticmethod
    def get_decision_history(candidate_id: int = None):
        """Get decision history for candidate or all"""
        try:
            decisions = load_json("feedback/decision_history.json")
            if not isinstance(decisions, list):
                return []
            
            if candidate_id:
                return [d for d in decisions if d.get("candidate_id") == candidate_id]
            
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to get decision history: {e}")
            return []
    
    @staticmethod
    def get_decision_analytics():
        """Get decision analytics and patterns"""
        try:
            decisions = DecisionEngine.get_decision_history()
            
            if not decisions:
                return {"total": 0, "patterns": {}}
            
            analytics = {
                "total_decisions": len(decisions),
                "decision_breakdown": {},
                "average_score": 0,
                "recent_decisions": decisions[-10:],
                "decision_trends": {}
            }
            
            # Calculate breakdown
            for decision in decisions:
                outcome = decision.get("decision", "unknown")
                analytics["decision_breakdown"][outcome] = analytics["decision_breakdown"].get(outcome, 0) + 1
            
            # Calculate average score
            scores = [d.get("score", 0) for d in decisions if d.get("score")]
            if scores:
                analytics["average_score"] = sum(scores) / len(scores)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get decision analytics: {e}")
            return {"total": 0, "error": str(e)}

# Event timeline logging
class EventTimeline:
    """Event timeline tracking for candidates"""
    
    @staticmethod
    def log_event(candidate_id: int, event_type: str, details: dict = None):
        """Log timeline event for candidate"""
        try:
            event_data = {
                "candidate_id": candidate_id,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "details": details or {},
                "event_id": f"EVT_{candidate_id}_{int(datetime.now().timestamp())}"
            }
            
            # Log to database
            db_manager.log_system_event(
                "INFO",
                f"timeline_event_{event_type}",
                f"Timeline event: {event_type} for candidate {candidate_id}",
                event_data
            )
            
            # Log to timeline file
            timeline = load_json("feedback/event_timeline.json")
            if not isinstance(timeline, list):
                timeline = []
            
            timeline.append(event_data)
            save_json("feedback/event_timeline.json", timeline)
            
            logger.info(f"Timeline event logged: {event_type} for candidate {candidate_id}")
            return event_data["event_id"]
            
        except Exception as e:
            logger.error(f"Failed to log timeline event: {e}")
            return None
    
    @staticmethod
    def get_candidate_timeline(candidate_id: int):
        """Get complete timeline for candidate"""
        try:
            timeline = load_json("feedback/event_timeline.json")
            if not isinstance(timeline, list):
                return []
            
            candidate_events = [e for e in timeline if e.get("candidate_id") == candidate_id]
            return sorted(candidate_events, key=lambda x: x.get("timestamp", ""))
            
        except Exception as e:
            logger.error(f"Failed to get candidate timeline: {e}")
            return []
    
    @staticmethod
    def get_recent_events(limit: int = 50):
        """Get recent events across all candidates"""
        try:
            timeline = load_json("feedback/event_timeline.json")
            if not isinstance(timeline, list):
                return []
            
            sorted_events = sorted(timeline, key=lambda x: x.get("timestamp", ""), reverse=True)
            return sorted_events[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []