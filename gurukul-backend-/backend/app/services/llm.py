
import requests
from fastapi import HTTPException
from app.core.config import settings
from typing import Optional

def create_teaching_prompt(subject: str, topic: str, grade: Optional[str] = None) -> str:
    """
    Create a teaching prompt with optional grade-level customization.
    
    Args:
        subject: Subject name
        topic: Topic name
        grade: Optional grade level (e.g., "3", "9", "12")
    """
    from app.utils.grade_helper import get_grade_level_description, get_grade_complexity_guidelines
    
    grade_description = get_grade_level_description(grade)
    complexity_guidelines = get_grade_complexity_guidelines(grade)
    
    grade_context = f" for a {grade_description} student" if grade else ""
    grade_instruction = f"""

IMPORTANT: You are teaching a {grade_description} student. Please adjust your content accordingly:
{complexity_guidelines}

Ensure all explanations, examples, vocabulary, and practice questions are appropriate for this grade level.""" if grade else ""
    
    return f"""You are an expert teacher specializing in {subject}. Your task is to teach the topic "{topic}" to a student{grade_context}.

Please provide comprehensive, clear, and engaging educational notes that include:

1. **Introduction**: A brief overview of the topic and why it's important
2. **Key Concepts**: Break down the main concepts in simple, understandable terms
3. **Detailed Explanation**: Provide a thorough explanation with examples
4. **Real-world Applications**: Show how this topic applies in real life
5. **Summary**: A concise recap of the key points
6. **Practice Questions**: 2-3 questions to help reinforce learning

Write in a friendly, encouraging tone as if you're speaking directly to a student. Use simple language, analogies, and examples to make complex concepts easy to understand. Structure the content with clear headings and bullet points for better readability.
{grade_instruction}

Subject: {subject}
Topic: {topic}

Now, provide the educational notes:"""

async def generate_text(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Generic LLM interface to call standard inference (Groq or Ollama)
    """
    # 1. Try Groq
    if settings.GROQ_API_KEY:
        try:
            return await _call_groq_generic(system_prompt, user_prompt, temperature)
        except Exception as e:
            print(f"[LLM] Groq Failed: {e}. Falling back to Ollama...")
    
    # 2. Try Ollama
    return await _call_ollama_generic(system_prompt, user_prompt, temperature)

async def _call_groq_generic(system_prompt: str, user_prompt: str, temperature: float) -> str:
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.GROQ_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2048
        }
        
        response = requests.post(settings.GROQ_API_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

async def _call_ollama_generic(system_prompt: str, user_prompt: str, temperature: float) -> str:
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    
    # Ollama "system" message handling varies, but we can prepend it or use the 'system' field if supported.
    # For simple generate endpoint, 'system' parameter is supported in newer versions.
    # Safe fallback: Prepend to prompt.
    
    payload = {
        "model": settings.OLLAMA_MODEL_PRIMARY,
        "system": system_prompt, # Prompt for system behavior
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 2048
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Error generating response from Ollama")
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"LLM Generation Failed (Groq & Ollama): {str(e)}")

# Legacy Wrappers for Existing Calls (to keep backward compatibility)
async def call_groq_api(subject: str, topic: str) -> str:
    prompt = create_teaching_prompt(subject, topic)
    return await _call_groq_generic("You are an expert teacher who explains concepts clearly and simply.", prompt, 0.7)

async def call_ollama_api(subject: str, topic: str) -> str:
    prompt = create_teaching_prompt(subject, topic)
    return await _call_ollama_generic("You are an expert teacher who explains concepts clearly and simply.", prompt, 0.7)
