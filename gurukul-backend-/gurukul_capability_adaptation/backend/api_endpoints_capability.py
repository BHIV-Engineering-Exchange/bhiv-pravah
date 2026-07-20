"""
API endpoints for user progress, trigger intervention, and enhanced lesson (with quiz_score/user_id).
Source: Backend/Base_backend/api.py
Use these as reference to mount in your new Gurukul app (FastAPI/Flask).
"""

from datetime import datetime
from typing import Optional

# Pydantic
class EnhancedLessonRequest:
    """Request body for enhanced lesson creation."""
    subject: str
    topic: str
    user_id: Optional[str] = "guest-user"
    quiz_score: Optional[float] = None
    use_orchestration: Optional[bool] = True
    include_triggers: Optional[bool] = True
    include_wikipedia: Optional[bool] = True


# --- Endpoint logic (assumes orchestration_engine and generate_progress_recommendations exist) ---

# GET /user-progress/{user_id}
def get_user_progress_logic(orchestration_engine, user_id: str):
    if not orchestration_engine:
        return None, "Orchestration system not available"
    session = orchestration_engine.memory_manager.get_user_session(user_id)
    educational_progress = session.get("educational_progress", {})
    triggers = orchestration_engine.triggers.check_educational_triggers(user_id)
    from .progress_recommendations import generate_progress_recommendations
    recommendations = generate_progress_recommendations(educational_progress, triggers)
    return {
        "user_id": user_id,
        "educational_progress": educational_progress,
        "triggers_detected": triggers,
        "last_active": session.get("last_active"),
        "interaction_count": session.get("interaction_count", 0),
        "quiz_scores": educational_progress.get("quiz_scores", []),
        "learning_topics": educational_progress.get("learning_topics", []),
        "recommendations": recommendations,
    }, None


# POST /trigger-intervention/{user_id}?quiz_score=55
async def trigger_intervention_logic(orchestration_engine, user_id: str, quiz_score: Optional[float] = None):
    if not orchestration_engine:
        return None, "Orchestration system not available"
    triggers = orchestration_engine.triggers.check_educational_triggers(user_id, quiz_score)
    if not triggers:
        return {"user_id": user_id, "message": "No interventions needed", "triggers_detected": [], "interventions": []}, None
    interventions = await orchestration_engine.triggers.execute_trigger_actions(user_id, triggers)
    return {
        "user_id": user_id,
        "message": f"Executed {len(interventions)} interventions",
        "triggers_detected": triggers,
        "interventions": interventions,
        "timestamp": datetime.now().isoformat(),
    }, None


# POST /lessons/enhanced (body: EnhancedLessonRequest)
async def create_enhanced_lesson_logic(orchestration_engine, lesson_request: EnhancedLessonRequest):
    if not orchestration_engine or not lesson_request.use_orchestration:
        return None, "use_basic_lesson_fallback"
    query = f"Create a detailed lesson about {lesson_request.topic} in {lesson_request.subject}. Provide comprehensive explanations, examples, and practical applications."
    # Call your ask_edumentor (or engine.ask_edumentor) with lesson_request.user_id and lesson_request.quiz_score
    # orchestration_response = await orchestration_engine.ask_edumentor(query=query, user_id=lesson_request.user_id, quiz_score=lesson_request.quiz_score)
    # Then: transform_orchestration_to_lesson(orchestration_response, subject, topic, user_id)
    return None, "integrate_ask_edumentor_and_transform"


def transform_orchestration_to_lesson(orchestration_response: dict, subject: str, topic: str, user_id: str) -> dict:
    """Convert orchestration response to lesson format for frontend."""
    explanation = orchestration_response.get("explanation", "")
    activity = orchestration_response.get("activity", {})
    triggers = orchestration_response.get("triggers_detected", [])
    interventions = orchestration_response.get("trigger_interventions", [])
    return {
        "subject": subject,
        "topic": topic,
        "user_id": user_id,
        "content": explanation,
        "source": "orchestration_enhanced",
        "enhanced_features": {"activity": activity, "triggers_detected": len(triggers)},
        "orchestration_data": {
            "query_id": orchestration_response.get("query_id"),
            "activity_details": activity,
            "triggers": triggers,
            "interventions": interventions,
            "timestamp": orchestration_response.get("timestamp"),
        },
        "generated_at": datetime.now().isoformat(),
        "status": "success",
    }
