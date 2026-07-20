import uuid
import os
import re
from app.services.voice_provider import provider


# Deprecated: Using VoiceProvider instead
def initialize_tts_engine(language='en'):
    pass

def text_to_speech_simple(text, output_filename=None):
    """Legacy wrapper - now using unified VoiceProvider"""
    return "deprecated_now_use_streaming"


def remove_emojis(text):
    """
    Remove emojis and emoji-like symbols from text
    
    Args:
        text (str): Text that may contain emojis
        
    Returns:
        str: Text with emojis removed
    """
    # Remove emojis using regex pattern
    # This pattern matches most emoji ranges in Unicode
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "]+", 
        flags=re.UNICODE
    )
    
    # Remove emojis and clean up extra spaces
    text_without_emojis = emoji_pattern.sub('', text)
    # Clean up multiple spaces
    text_without_emojis = re.sub(r'\s+', ' ', text_without_emojis).strip()
    
    return text_without_emojis


def translate_text(text, target_language='en'):
    """
    Translate text to target language using Groq API
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (e.g., 'en', 'es', 'fr', 'ja')
        
    Returns:
        str: Translated text
    """
    # Remove emojis before translation
    text = remove_emojis(text)
    
    # Language name mapping for better translation prompts
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh': 'Chinese (Simplified)',
        'ja': 'Japanese',
        'ko': 'Korean',
        'hi': 'Hindi',
        'ar': 'Arabic',
    }
    
    target_lang_name = language_names.get(target_language.lower(), 'English')
    
    # If target is English, no translation needed
    if target_language.lower() == 'en':
        return text
    
    try:
        import os
        import requests
        from app.core.config import settings
        
        # Get Groq API key
        api_key = settings.GROQ_API_KEY or os.getenv('GROQ_API_KEY')
        if not api_key:
            print(f"[TTS] No GROQ_API_KEY found, skipping translation")
            return text
        
        # Strict translation prompt - only translate, no additions
        # Calculate max_tokens based on input length (translation shouldn't be much longer)
        word_count = len(text.split())
        # Limit max_tokens to prevent model from generating extra content
        max_tokens = min(max(word_count * 2, 100), 300)  # More conservative: 100-300 tokens
        
        # Very strict system prompt to prevent hallucinations
        system_prompt = f"""You are a translation tool. Your ONLY job is to translate the given text to {target_lang_name}.

RULES:
- Translate ONLY the provided text
- Do NOT add any explanations, notes, or additional information
- Do NOT add context or examples
- Do NOT mention other languages or topics
- Return ONLY the translation, nothing else
- If the text is already in {target_lang_name}, return it unchanged"""

        # Simple user prompt with clear delimiter
        translation_prompt = f"Translate this text to {target_lang_name}:\n\n{text}"
        
        # Call Groq API using requests (same way as other services)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Try to use a faster model for translation (smaller = faster)
        default_model = settings.GROQ_MODEL_NAME or "llama-3.3-70b-versatile"
        # Use fastest available model - try smaller models first for speed
        fast_model = "llama-3.1-8b-instant"  # Fastest Groq model
        
        # Try with fast model first (without stop sequences - they might cause 400 errors)
        payload = {
            "model": fast_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": translation_prompt}
            ],
            "temperature": 0.0,  # Zero temperature for fastest, most deterministic output
            "max_tokens": max_tokens
            # Note: Not using stop sequences as they might cause 400 errors with some models
        }
        
        try:
            response = requests.post(
                settings.GROQ_API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=10  # Even shorter timeout
            )
            # If fast model fails, try with default model
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = error_data.get('error', {}).get('message', '')
                except:
                    error_detail = response.text[:200]
                raise Exception(f"Fast model returned {response.status_code}: {error_detail}")
        except Exception as e:
            # Fallback to default model if fast model fails
            print(f"[TTS] Fast model failed, using default: {e}")
            # Create fresh payload for default model (without stop sequences)
            payload_fallback = {
                "model": default_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": translation_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": max_tokens
            }
            
            try:
                response = requests.post(
                    settings.GROQ_API_ENDPOINT,
                    headers=headers,
                    json=payload_fallback,
                    timeout=15
                )
            except Exception as fallback_error:
                print(f"[TTS] Default model also failed: {fallback_error}")
                raise fallback_error
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result['choices'][0]['message']['content'].strip()
            
            # Clean up the translation - remove any extra content
            # Remove quotation marks
            translated_text = translated_text.strip('"').strip("'").strip()
            
            # Remove common prefixes that models add
            prefixes_to_remove = [
                f"{target_lang_name}:",
                f"Translation:",
                f"Translated text:",
                f"Here is the translation:",
                f"The translation is:",
            ]
            for prefix in prefixes_to_remove:
                if translated_text.lower().startswith(prefix.lower()):
                    translated_text = translated_text[len(prefix):].strip()
            
            # Remove any notes or explanations that might have been added
            # Split by common separators and take only the first part
            separators = ["\n\nNote:", "\n\nAlso:", "\n\nAdditionally:", "\n\n---", "\n\nNote that"]
            for sep in separators:
                if sep in translated_text:
                    translated_text = translated_text.split(sep)[0].strip()
            
            # Limit length - if translation is way longer than original, truncate
            original_length = len(text)
            if len(translated_text) > original_length * 3:  # If 3x longer, something's wrong
                # Take first part that's roughly similar length
                words = translated_text.split()
                original_words = text.split()
                max_words = len(original_words) * 2  # Allow 2x word count max
                translated_text = " ".join(words[:max_words])
                print(f"[TTS] Warning: Translation was too long, truncated to {max_words} words")
            
            print(f"[TTS] Translated text to {target_lang_name} (length: {len(translated_text)} vs original: {len(text)})")
            return translated_text
        else:
            print(f"[TTS] Translation API error: {response.status_code}, using original text")
            return text
        
    except Exception as e:
        print(f"[TTS] Translation failed: {e}, using original text")
        return text


async def text_to_speech_stream(text, language='en', use_google_tts=True, translate=True):
    """
    Sovereign Voice Stream - Uses Vaani via VoiceProvider
    """
    if not text:
        raise ValueError("Text is required")
    
    # Remove emojis from text before processing
    text = remove_emojis(text)
    
    # Translate text if needed and not English
    if translate and language.lower() != 'en':
        text = translate_text(text, language)
    
    print(f"[VoiceModule] Generating audio for {language} ({len(text)} chars)")
    
    # Always use the unified provider
    return await provider.generate_audio(text, language)


def speak_text_directly(text):
    print(f"[VoiceModule] Local playback (say) is disabled in production stability mode.")


# Example usage
if __name__ == "__main__":
    sample_text = "Hello, this is a text to speech example."
    
    # Method 1: Save to file
    filename = text_to_speech_simple(sample_text, "example_output.wav")
    print(f"Audio saved to: {filename}")
    
    # Method 2: Speak directly
    speak_text_directly("This will be spoken directly.")