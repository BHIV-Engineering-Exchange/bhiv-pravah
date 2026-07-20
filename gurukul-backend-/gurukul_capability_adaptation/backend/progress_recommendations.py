"""
Progress-based recommendations from quiz scores and learning topics.
Source: Backend/Base_backend/api.py (generate_progress_recommendations)
"""

from typing import Dict, Any, List


def generate_progress_recommendations(
    educational_progress: Dict[str, Any], triggers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate recommendations based on user progress and detected triggers."""
    recommendations = []

    quiz_scores = educational_progress.get("quiz_scores", [])
    learning_topics = educational_progress.get("learning_topics", [])

    if quiz_scores:
        avg_score = sum(quiz_scores) / len(quiz_scores)
        if avg_score < 60:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "high",
                    "message": f"Average quiz score is {avg_score:.1f}%. Consider reviewing fundamental concepts.",
                    "action": "schedule_tutoring",
                }
            )
        elif avg_score < 75:
            recommendations.append(
                {
                    "type": "performance",
                    "priority": "medium",
                    "message": f"Good progress with {avg_score:.1f}% average. Focus on challenging topics.",
                    "action": "practice_exercises",
                }
            )

    if len(learning_topics) > 5:
        recent_topics = learning_topics[-5:]
        if len(set(recent_topics)) < 3:
            recommendations.append(
                {
                    "type": "variety",
                    "priority": "medium",
                    "message": "Consider exploring more diverse topics to broaden understanding.",
                    "action": "topic_diversification",
                }
            )

    for trigger in triggers:
        if trigger.get("type") == "low_quiz_score":
            recommendations.append(
                {
                    "type": "intervention",
                    "priority": "high",
                    "message": "Immediate tutoring support recommended due to low quiz performance.",
                    "action": "immediate_tutoring",
                }
            )

    return recommendations
