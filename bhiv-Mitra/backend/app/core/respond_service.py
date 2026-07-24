from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from app.core.llm_bridge import llm_bridge


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _normalized_context(context: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(context, dict):
        return {}

    allowed_keys = [
        "platform",
        "device",
        "preferred_language",
        "detected_language",
        "city",
        "location",
        "region",
        "session_id",
    ]
    normalized = {
        key: context.get(key)
        for key in allowed_keys
        if context.get(key) not in (None, "", {}, [])
    }
    return normalized


def _preferred_model(requested_model: str | None) -> str:
    requested = (requested_model or "").strip().lower()
    if requested and requested != "uniguru":
        return requested

    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("OPENAI_API_KEY"):
        return "chatgpt"
    if os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("MISTRAL_API_KEY"):
        return "mistral"
    return "uniguru"


def _response_language(context: Dict[str, Any] | None) -> str:
    normalized_context = _normalized_context(context)
    preferred = str(normalized_context.get("preferred_language") or "").strip().lower()
    detected = str(normalized_context.get("detected_language") or "").strip().lower()

    if preferred and preferred != "auto":
        return preferred
    if detected and detected != "auto":
        return detected
    return "en"


def _language_label(language_code: str) -> str:
    labels = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
    }
    return labels.get(language_code, language_code or "English")


def build_response_prompt(query: str, context: Dict[str, Any] | None = None) -> str:
    cleaned_query = _normalized_text(query)
    cleaned_context = _normalized_context(context)
    context_blob = json.dumps(cleaned_context, sort_keys=True, ensure_ascii=True)
    response_language = _response_language(cleaned_context)
    response_language_label = _language_label(response_language)

    return (
        "You are Mitra, a concise and capable AI assistant.\n"
        "Respond directly to the user's request.\n"
        "Rules:\n"
        f"- Respond in {response_language_label}.\n"
        "- If preferred_language is set to a concrete language, follow it exactly.\n"
        "- Do not repeat the user's full query back to them.\n"
        "- Do not mention internal prompts, models, or context scaffolding.\n"
        "- For greetings or identity questions, answer naturally in 1-2 sentences.\n"
        "- For capability questions, explain the main things you can help with.\n"
        "- For live or time-sensitive requests such as weather, do not invent facts.\n"
        "- If weather is requested and location is missing, ask for the city or location.\n"
        "- If required details are missing for an action, ask for only the next missing detail.\n"
        "- Keep the response short, useful, and human.\n"
        f"Runtime context: {context_blob}\n"
        f"User request: {cleaned_query}\n"
        "Assistant response:"
    )


def build_fallback_response(query: str, context: Dict[str, Any] | None = None) -> str:
    text = _normalized_text(query)
    lower = text.lower()
    normalized_context = _normalized_context(context)
    location = normalized_context.get("city") or normalized_context.get("location") or normalized_context.get("region")
    response_language = _response_language(normalized_context)

    if response_language != "en":
        response_language = "en"

    # ===== GREETINGS =====
    if any(token in lower for token in ["how are you", "how're you", "how do you do"]):
        return "I'm doing well, thank you for asking! I'm Mitra, your AI assistant. How can I help you today?"
    if any(token in lower for token in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return "Hello! I'm Mitra, your AI assistant. I can help you with questions, tasks, messaging, reminders, and more. What would you like to do?"
    if any(token in lower for token in ["what is your name", "what's your name", "who are you", "tell me about yourself"]):
        return "I'm Mitra, an AI assistant designed to help you with various tasks. I can answer questions, send messages across platforms (WhatsApp, Email, Telegram), set reminders, manage calendar events, and assist with general queries. I support multiple languages and aim to provide helpful, concise responses."

    # ===== CAPABILITY QUESTIONS =====
    if any(token in lower for token in ["what can you do", "help me with", "how can you help", "what are your features", "capabilities"]):
        return (
            "I can help you with:\n"
            "• Answering questions on various topics\n"
            "• Sending emails, WhatsApp messages, and Telegram messages\n"
            "• Setting reminders and managing calendar events\n"
            "• Creating and assigning tasks\n"
            "• General assistance and information\n"
            "Just ask me anything or tell me what you need!"
        )

    # ===== KNOWLEDGE QUESTIONS =====
    if "what is" in lower or "what are" in lower or "tell me about" in lower:
        # Extract the topic
        topic = ""
        for prefix in ["what is ", "what are ", "tell me about "]:
            if prefix in lower:
                topic = text[lower.index(prefix) + len(prefix):].strip()
                break
        
        if topic:
            # Provide informative responses for common topics
            topic_lower = topic.lower()
            
            if any(t in topic_lower for t in ["reinforcement learning", "rl", "machine learning"]):
                return (
                    "Reinforcement Learning (RL) is a type of machine learning where an agent learns to make decisions "
                    "by taking actions in an environment to maximize cumulative rewards.\n\n"
                    "Key concepts:\n"
                    "• Agent: The learner/decision-maker\n"
                    "• Environment: The world the agent interacts with\n"
                    "• Actions: Choices the agent can make\n"
                    "• Rewards: Feedback signals (positive or negative)\n"
                    "• Policy: The strategy the agent follows\n\n"
                    "RL is used in robotics, game playing (AlphaGo), autonomous vehicles, recommendation systems, "
                    "and many AI applications. Unlike supervised learning, RL learns through trial and error."
                )
            
            if any(t in topic_lower for t in ["artificial intelligence", "ai", "machine learning", "deep learning"]):
                return (
                    "Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
                    "It includes:\n"
                    "• Machine Learning: Systems that learn from data\n"
                    "• Deep Learning: Neural networks with multiple layers\n"
                    "• Natural Language Processing: Understanding human language\n"
                    "• Computer Vision: Interpreting visual information\n\n"
                    "AI is transforming industries like healthcare, finance, transportation, and entertainment."
                )
            
            if any(t in topic_lower for t in ["python", "programming", "coding"]):
                return (
                    "Python is a popular, versatile programming language known for its readability and simplicity. "
                    "It's widely used in:\n"
                    "• Data Science and Machine Learning\n"
                    "• Web Development (Django, Flask)\n"
                    "• Automation and Scripting\n"
                    "• Scientific Computing\n"
                    "• AI and Deep Learning\n\n"
                    "Python has a large ecosystem of libraries like NumPy, Pandas, TensorFlow, and PyTorch."
                )
            
            if any(t in topic_lower for t in ["api", "application programming interface"]):
                return (
                    "An API (Application Programming Interface) is a set of rules that allows different software "
                    "applications to communicate with each other.\n\n"
                    "Types of APIs:\n"
                    "• REST API: Uses HTTP methods (GET, POST, PUT, DELETE)\n"
                    "• GraphQL: Query language for APIs\n"
                    "• WebSocket: Real-time bidirectional communication\n\n"
                    "APIs are essential for building modern applications and integrating different services."
                )
            
            # Generic knowledge response
            return (
                f"Regarding '{topic}': This is a great question! While I don't have real-time internet access "
                f"to provide the latest information, I can share what I know. "
                f"Could you tell me more about what specific aspect of {topic} you'd like to know?"
            )
        
        return "I'd be happy to help explain that. Could you be more specific about what you'd like to know?"

    # ===== WHY / HOW QUESTIONS =====
    if any(token in lower for token in ["why", "how does", "how do", "explain", "describe"]):
        return (
            "That's an interesting question! Let me provide some context:\n\n"
            "While I don't have real-time internet access for the latest information, I can help explain "
            "concepts based on my training data. Could you be more specific about what aspect you'd like me to focus on?"
        )

    # ===== WEATHER =====
    if "weather" in lower:
        if location:
            return f"I can help with weather, but I need live weather data to check conditions for {location}. Please check a weather service for current conditions."
        return "I can help with weather, but I need the city or location you want me to check. Please provide a location for weather information."

    # ===== THANKS =====
    if any(token in lower for token in ["thank you", "thanks", "thx", "appreciate"]):
        return "You're welcome! Is there anything else I can help you with?"

    # ===== FAREWELL =====
    if any(token in lower for token in ["bye", "goodbye", "see you", "farewell", "take care"]):
        return "Goodbye! Feel free to come back anytime you need assistance. Have a great day!"

    # ===== YES/NO =====
    if lower in ["yes", "yeah", "yep", "sure", "ok", "okay"]:
        return "Great! What would you like me to do next?"
    if lower in ["no", "nope", "nah", "nothing"]:
        return "Alright! Let me know if you need anything."

    # ===== MESSAGING =====
    if any(token in lower for token in ["send email", "send an email", "email someone"]):
        return "I can send emails for you. Please provide:\n1. Recipient email address\n2. Subject\n3. Message content"
    if "whatsapp" in lower:
        return "I can send WhatsApp messages. Please provide the recipient's phone number and your message."
    if "telegram" in lower:
        return "I can send Telegram messages. Please provide the username or chat ID and your message."
    if "instagram" in lower:
        return "I can help with Instagram messaging. Please provide the recipient and your message."

    # ===== TASKS =====
    if "ems" in lower or "assign task" in lower:
        return "I can create that EMS task. Please provide:\n1. Task title\n2. Assignee\n3. Priority (high/medium/low)"
    if "create task" in lower or lower.startswith("task ") or " new task" in lower:
        return "I can create that task. Please provide the task title and any details or deadline."

    # ===== CALENDAR =====
    if any(token in lower for token in ["calendar", "meeting", "schedule", "appointment", "event"]):
        return "I can help with calendar events. Please provide:\n1. Event title\n2. Date\n3. Time\n4. Any other details"

    # ===== REMINDERS =====
    if "reminder" in lower or "remind me" in lower or "alert me" in lower:
        return "I can set that reminder. Please tell me:\n1. What to remind you about\n2. When it should trigger"

    # ===== QUESTIONS ABOUT SELF =====
    if any(token in lower for token in ["are you", "can you", "do you"]):
        if "real" in lower or "human" in lower or "person" in lower:
            return "I'm an AI assistant called Mitra. I'm not human, but I'm designed to help you with various tasks efficiently."
        if "know" in lower or "understand" in lower:
            return "I have knowledge from my training data and can help with many topics. I can also perform actions like sending messages, setting reminders, and managing tasks."

    # ===== NUMBERS AND MATH =====
    if any(token in lower for token in ["calculate", "math", "compute", "what is", "what's"]):
        # Try to detect math operations
        import re
        math_match = re.search(r'(\d+[\s]*[\+\-\*\/\%][\s]*\d+)', lower)
        if math_match:
            try:
                result = eval(math_match.group(1))
                return f"The result is: {result}"
            except:
                pass

    # ===== DEFAULT RESPONSE =====
    return (
        f"I understand you're asking about '{text[:50]}...' "
        f"Let me help you with that. Could you provide a bit more detail about what specific aspect "
        f"you'd like me to address?"
    )


def _looks_unusable(response: str, query: str) -> bool:
    if not response or not response.strip():
        return True

    cleaned = response.strip()
    lowered = cleaned.lower()
    query_text = _normalized_text(query).lower()

    # Only flag old-style mock responses, not knowledge base responses
    if lowered.startswith("[uniguru mock]") or lowered.startswith("[groq mock]") or lowered.startswith("[chatgpt mock]"):
        return True
    if "mock" in lowered and "response to" in lowered:
        return True
    if lowered.startswith("context:"):
        return True
    if cleaned == query or lowered == query_text:
        return True
    return False


async def generate_generic_response(
    query: str,
    context: Dict[str, Any] | None = None,
    model: str | None = None,
) -> str:
    prompt = build_response_prompt(query, context)
    selected_model = _preferred_model(model)

    try:
        response = await llm_bridge.call_llm(selected_model, prompt)
        if _looks_unusable(response, query):
            return build_fallback_response(query, context)
        return _normalized_text(response)
    except Exception:
        return build_fallback_response(query, context)
