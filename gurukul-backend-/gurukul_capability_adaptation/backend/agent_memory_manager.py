"""
Agent Memory Manager - User session and educational progress tracking.
Source: Backend/orchestration/unified_orchestration_system/orchestration_api.py (AgentMemoryManager class)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AgentMemoryManager:
    """
    Common agent memory and state manager. Tracks per-user:
    - educational_progress: quiz_scores, learning_topics, last_activity
    - wellness_metrics, spiritual_journey (optional for capability feature)
    """

    def __init__(self, storage_dir: str = "agent_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.user_sessions = {}
        self.interaction_history = {}

    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """Get or create user session data."""
        if user_id not in self.user_sessions:
            session_file = self.storage_dir / f"user_{user_id}.json"
            if session_file.exists():
                with open(session_file, "r") as f:
                    self.user_sessions[user_id] = json.load(f)
            else:
                self.user_sessions[user_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat(),
                    "interaction_count": 0,
                    "preferences": {},
                    "wellness_metrics": {
                        "mood_trend": [],
                        "stress_level": "moderate",
                        "last_wellness_check": None,
                    },
                    "educational_progress": {
                        "quiz_scores": [],
                        "learning_topics": [],
                        "last_activity": None,
                    },
                    "spiritual_journey": {
                        "topics_explored": [],
                        "favorite_teachings": [],
                        "last_vedas_query": None,
                    },
                }
        return self.user_sessions[user_id]

    def update_user_session(self, user_id: str, updates: Dict[str, Any]):
        """Update user session with new data and persist to file."""
        session = self.get_user_session(user_id)
        session.update(updates)
        session["last_active"] = datetime.now().isoformat()
        session["interaction_count"] += 1

        session_file = self.storage_dir / f"user_{user_id}.json"
        with open(session_file, "w") as f:
            json.dump(session, f, indent=2)

        self.user_sessions[user_id] = session

    def add_interaction(self, user_id: str, agent_type: str, query: str, response: Dict[str, Any]):
        """Record an interaction for trigger analysis."""
        if user_id not in self.interaction_history:
            self.interaction_history[user_id] = []

        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent_type": agent_type,
            "query": query,
            "response_summary": self._summarize_response(response),
            "user_satisfaction": None,
        }
        self.interaction_history[user_id].append(interaction)

        if len(self.interaction_history[user_id]) > 50:
            self.interaction_history[user_id] = self.interaction_history[user_id][-50:]

    def _summarize_response(self, response: Dict[str, Any]) -> str:
        if "wisdom" in response:
            return f"Vedas guidance on {response.get('query', 'spiritual topic')}"
        elif "explanation" in response:
            return f"Educational content about {response.get('query', 'learning topic')}"
        elif "advice" in response:
            return f"Wellness advice for {response.get('query', 'health concern')}"
        return "General response"
