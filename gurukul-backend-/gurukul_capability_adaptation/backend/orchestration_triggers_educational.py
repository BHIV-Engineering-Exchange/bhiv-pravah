"""
Educational triggers: detect low quiz score / declining performance and execute interventions (tutorbot, quizbot).
Source: Backend/orchestration/unified_orchestration_system/orchestration_api.py (OrchestrationTriggers - educational part only)
"""

import os
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class OrchestrationTriggersEducational:
    """Checks educational triggers and runs tutorbot/quizbot interventions."""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.trigger_thresholds = {
            "low_quiz_score": 60,
            "inactivity_days": 7,
            "repeated_queries": 3,
        }

    def check_educational_triggers(self, user_id: str, quiz_score: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return list of triggers: low_quiz_score, declining_performance."""
        triggers = []
        session = self.memory_manager.get_user_session(user_id)

        if quiz_score is not None and quiz_score < self.trigger_thresholds["low_quiz_score"]:
            triggers.append(
                {
                    "type": "low_quiz_score",
                    "severity": "high",
                    "message": f"Quiz score of {quiz_score}% indicates need for additional support",
                    "recommended_action": "tutoring_session",
                    "sub_agent": "tutorbot",
                }
            )

        quiz_scores = session.get("educational_progress", {}).get("quiz_scores", [])
        if len(quiz_scores) >= 3:
            recent = quiz_scores[-3:]
            if all(s < self.trigger_thresholds["low_quiz_score"] for s in recent):
                triggers.append(
                    {
                        "type": "declining_performance",
                        "severity": "high",
                        "message": "Consistent low quiz scores detected",
                        "recommended_action": "intensive_tutoring",
                        "sub_agent": "tutorbot",
                    }
                )

        return triggers

    async def execute_trigger_actions(self, user_id: str, triggers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tutorbot and quizbot actions for each trigger."""
        results = []
        for trigger in triggers:
            try:
                if trigger.get("sub_agent") == "tutorbot":
                    result = await self._call_tutorbot(user_id, trigger)
                elif trigger.get("sub_agent") == "quizbot":
                    result = await self._call_quizbot(user_id, trigger)
                else:
                    result = {"status": "unknown_agent", "trigger": trigger}
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing trigger action: {e}")
                results.append({"status": "error", "error": str(e), "trigger": trigger})
        return results

    async def _call_tutorbot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        tutorbot_url = os.getenv("TUTORBOT_URL", "http://localhost:8001")
        try:
            if trigger["type"] in ["low_quiz_score", "declining_performance"]:
                request_data = {
                    "user_id": user_id,
                    "user_data": {
                        "learning_preferences": {"difficulty": "beginner", "session_length": 30, "subjects": ["general"]},
                        "progress": {"total_study_time": 0, "current_streak": 0, "recent_performance": "struggling"},
                        "goals": ["improve_understanding", "build_confidence"],
                        "concepts": [],
                    },
                    "target_days": 7,
                    "daily_time_minutes": 30,
                }
                response = requests.post(f"{tutorbot_url}/api/v1/lesson-plan", json=request_data, timeout=30)
                if response.status_code == 200:
                    return {"status": "success", "agent": "tutorbot", "trigger_type": trigger["type"], "intervention": {"type": "personalized_lesson_plan", "lesson_plan": response.json(), "message": "Generated personalized learning plan based on performance analysis"}}
            else:
                response = requests.get(
                    f"{tutorbot_url}/api/v1/suggestions/quick",
                    params={"user_id": user_id, "subject": "general", "time_minutes": 20, "difficulty": "intermediate"},
                    timeout=30,
                )
                if response.status_code == 200:
                    return {"status": "success", "agent": "tutorbot", "trigger_type": trigger["type"], "intervention": {"type": "learning_suggestions", "suggestions": response.json(), "message": "Generated learning suggestions to re-engage student"}}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to tutorbot: {e}")
        return self._get_tutorbot_fallback(trigger)

    def _get_tutorbot_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "fallback",
            "agent": "tutorbot",
            "trigger_type": trigger["type"],
            "intervention": {
                "type": "personalized_lesson_plan",
                "message": "Tutorbot service unavailable. Using fallback recommendations.",
                "recommendations": [
                    "Focus on foundational concepts",
                    "Practice with easier questions first",
                    "Schedule regular review sessions",
                    "Seek help from teachers or peers",
                ],
            },
        }

    async def _call_quizbot(self, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        quizbot_url = os.getenv("QUIZBOT_URL", "http://localhost:8004")
        try:
            session = self.memory_manager.get_user_session(user_id)
            quiz_scores = session.get("educational_progress", {}).get("quiz_scores", [])
            recent_score = quiz_scores[-1] if quiz_scores else 50
            sample_quiz = {
                "id": f"diagnostic_quiz_{user_id}",
                "title": "Diagnostic Assessment",
                "subject": "general",
                "questions": [{"id": "q1", "question_text": "What is the basic unit of life?", "options": ["Cell", "Atom", "Molecule", "Tissue"], "correct_answer": "Cell", "points": 1}],
                "time_limit_minutes": 30,
                "passing_score_percentage": 60.0,
            }
            sample_response = {
                "student_id": user_id,
                "quiz_id": sample_quiz["id"],
                "answers": [{"question_id": "q1", "selected_option": "Cell" if recent_score > 60 else "Atom", "time_taken_seconds": 30}],
                "total_time_taken_minutes": 5,
            }
            response = requests.post(f"{quizbot_url}/api/v1/evaluate-quiz", json={"quiz": sample_quiz, "response": sample_response}, timeout=30)
            if response.status_code == 200:
                return {"status": "success", "agent": "quizbot", "trigger_type": trigger["type"], "intervention": {"type": "diagnostic_evaluation", "evaluation_data": response.json(), "message": "Diagnostic quiz evaluation completed with personalized feedback"}}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to quizbot: {e}")
        return self._get_quizbot_fallback(trigger)

    def _get_quizbot_fallback(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "fallback",
            "agent": "quizbot",
            "trigger_type": trigger["type"],
            "intervention": {
                "type": "adaptive_assessment",
                "message": "Quizbot service unavailable. Using fallback assessment guidance.",
                "next_steps": [
                    "Take a diagnostic quiz to identify knowledge gaps",
                    "Review areas where you scored below 70%",
                    "Practice targeted exercises on weak topics",
                    "Seek additional help from teachers or tutors",
                    "Retake assessments after focused study",
                ],
            },
        }
