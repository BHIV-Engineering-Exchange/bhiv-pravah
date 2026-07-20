"""
Edumentor handler: educational query with RAG, trigger check, and session update.
Explanation/activity generation does NOT yet use user capability in the prompt (see IMPLEMENTATION_GUIDE.md).
Source: Backend/orchestration/unified_orchestration_system/orchestration_api.py (ask_edumentor + generate_dynamic_response)
"""

import json
import re
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


async def ask_edumentor(
    *,
    query: str,
    user_id: str,
    quiz_score: Optional[float],
    memory_manager,
    triggers_engine,
    vector_stores: Dict,
    gemini_generate_content_fn,
    generate_dynamic_response_fn,
) -> Dict[str, Any]:
    """
    Handle educational query: check triggers, retrieve docs, generate explanation + activity,
    update educational_progress (quiz_scores, learning_topics). Requires callers to pass
    memory_manager, triggers_engine, vector_stores, and LLM helpers.
    """
    session = memory_manager.get_user_session(user_id)
    triggers = triggers_engine.check_educational_triggers(user_id, quiz_score)
    trigger_results = []
    if triggers:
        trigger_results = await triggers_engine.execute_trigger_actions(user_id, triggers)

    if "educational" in vector_stores:
        retriever = vector_stores["educational"].as_retriever(search_kwargs={"k": 5})
        relevant_docs = retriever.get_relevant_documents(query)
    elif "unified" in vector_stores:
        retriever = vector_stores["unified"].as_retriever(search_kwargs={"k": 5})
        relevant_docs = retriever.get_relevant_documents(query)
    else:
        relevant_docs = []

    context = "\n\n".join([doc.page_content[:500] for doc in relevant_docs[:4]])

    # NOTE: Prompt does NOT include user's educational_progress or capability level yet.
    explanation_prompt = f"""You are an expert educator who excels at making complex topics accessible and engaging for students. Based on the educational content provided, create a comprehensive yet understandable explanation.

EDUCATIONAL CONTEXT:
{context}

STUDENT'S QUESTION: {query}

Create an engaging explanation that:
- Uses clear, age-appropriate language
- Includes concrete examples and analogies
- Connects to students' everyday experiences
- Builds understanding step by step
- Sparks curiosity and interest
- Is scientifically/academically accurate

Make the explanation conversational and enthusiastic. Provide a comprehensive explanation in 2-3 paragraphs."""

    explanation_response = gemini_generate_content_fn(explanation_prompt) if callable(gemini_generate_content_fn) else None
    explanation = explanation_response if explanation_response else f"Let me explain {query} in an engaging way!"

    activity_prompt = f"""Based on the educational content, design a hands-on activity for students.

EDUCATIONAL CONTEXT:
{context}

LEARNING TOPIC: {query}

Respond in JSON format:
{{
    "title": "Creative title for the activity",
    "description": "What students will learn and do",
    "instructions": ["Step 1", "Step 2", "Step 3"],
    "materials_needed": ["Item 1", "Item 2"]
}}
Make the activity pedagogically sound, age-appropriate, and safe."""

    activity_fallback = {
        "title": f"Exploring {query}",
        "description": "A hands-on exploration activity.",
        "instructions": ["Research the topic", "Create a diagram", "Discuss findings", "Write three facts"],
        "materials_needed": ["Paper", "Pencils", "Access to books or internet"],
    }
    activity = generate_dynamic_response_fn(activity_prompt, activity_fallback) if callable(generate_dynamic_response_fn) else activity_fallback

    educational_progress = session.get("educational_progress", {})
    if quiz_score is not None:
        quiz_scores = educational_progress.get("quiz_scores", [])
        quiz_scores.append(quiz_score)
        educational_progress["quiz_scores"] = quiz_scores[-10:]
    learning_topics = educational_progress.get("learning_topics", [])
    learning_topics.append(query)
    educational_progress["learning_topics"] = learning_topics[-20:]
    educational_progress["last_activity"] = datetime.now().isoformat()
    memory_manager.update_user_session(user_id, {"educational_progress": educational_progress})

    return {
        "query_id": str(uuid.uuid4()),
        "query": query,
        "explanation": explanation,
        "activity": activity,
        "triggers_detected": triggers,
        "trigger_interventions": trigger_results,
        "source_documents": [{"text": doc.page_content[:800], "metadata": getattr(doc, "metadata", {})} for doc in relevant_docs],
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
    }


def generate_dynamic_response(prompt: str, fallback_response: Dict[str, Any], gemini_generate_content_fn) -> Dict[str, Any]:
    """Parse LLM response as JSON when possible; otherwise return fallback."""
    try:
        response = gemini_generate_content_fn(prompt) if callable(gemini_generate_content_fn) else None
        if response:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {"content": response}
    except Exception as e:
        logger.warning(f"Dynamic response generation failed: {e}")
    return fallback_response
