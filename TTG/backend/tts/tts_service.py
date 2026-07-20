import pyttsx3
import uuid
import os
import re
import requests
import json
import hashlib

# Translation cache
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'translation_cache.json')

def load_cache():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass


def initialize_tts_engine(language='en'):
    """
    Initialize and configure the TTS engine with language support
    """
    engine = pyttsx3.init()
    
    # Language to voice mapping (based on common SAPI5 voice names and language codes)
    language_mapping = {
        'en': ['english', 'zira', 'david', 'mark', 'en-us', 'en_us', 'en_gb'],
        'es': ['spanish', 'helena', 'sabina', 'es-es', 'es_es', 'es-mx', 'es_mx'],
        'fr': ['french', 'hortense', 'denis', 'fr-fr', 'fr_fr', 'fr-ca', 'fr_ca'],
        'de': ['german', 'hedda', 'stefan', 'de-de', 'de_de'],
        'it': ['italian', 'elsa', 'cosimo', 'it-it', 'it_it'],
        'pt': ['portuguese', 'heloisa', 'daniel', 'pt-pt', 'pt_pt', 'pt-br', 'pt_br'],
        'ru': ['russian', 'irina', 'pavel', 'ru-ru', 'ru_ru'],
        'zh': ['chinese', 'huihui', 'kangkang', 'zh-cn', 'zh_cn', 'zh-tw', 'zh_tw'],
        'ja': ['japanese', 'haruka', 'ichiro', 'ja-jp', 'ja_jp'],
        'ko': ['korean', 'heami', 'ko-kr', 'ko_kr'],
        'hi': ['hindi', 'kalpana', 'hemant', 'hi-in', 'hi_in'],
        'ar': ['arabic', 'hoda', 'naayf', 'ar-sa', 'ar_sa', 'ar-eg', 'ar_eg'],
    }
    
    # Configure TTS settings for better quality
    voices = engine.getProperty('voices')
    if voices:
        target_keywords = language_mapping.get(language.lower(), ['english', 'zira', 'en-us'])
        voice_found = False
        
        # Try to find a voice matching the language
        for voice in voices:
            voice_name_lower = voice.name.lower()
            voice_id_lower = voice.id.lower()
            
            for keyword in target_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in voice_name_lower or keyword_lower in voice_id_lower:
                    engine.setProperty('voice', voice.id)
                    voice_found = True
                    # print(f"[TTS] Selected voice for language '{language}': {voice.name}")
                    break
            
            if voice_found:
                break
        
        # Fallback: use first available voice if language not found
        if not voice_found and voices:
            engine.setProperty('voice', voices[0].id)
            # print(f"[TTS] Language '{language}' not found, using default voice: {voices[0].name}")

    # Set speech rate (words per minute)
    engine.setProperty('rate', 180)  # Slightly slower for clarity

    # Set volume (0.0 to 1.0)
    engine.setProperty('volume', 0.9)
    
    return engine


def text_to_speech_simple(text, output_filename=None):
    """
    Convert text to speech and save as an audio file
    """
    if not text:
        raise ValueError("Text is required")
    
    if not output_filename:
        output_filename = f"tts_{uuid.uuid4()}.wav"
    
    if not output_filename.endswith('.wav'):
        output_filename += '.wav'
    
    # Initialize TTS engine
    engine = initialize_tts_engine()
    
    # Generate audio file
    engine.save_to_file(text, output_filename)
    engine.runAndWait()
    
    # Verify file was created
    if not os.path.exists(output_filename):
        raise Exception("Audio generation failed - file not created")
    
    # Check file size
    file_size = os.path.getsize(output_filename)
    if file_size == 0:
        os.remove(output_filename)  # Remove empty file
        raise Exception("Audio generation failed - empty file")
    
    return output_filename


def remove_emojis(text):
    """
    Remove emojis and emoji-like symbols from text
    """
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
    
    text_without_emojis = emoji_pattern.sub('', text)
    text_without_emojis = re.sub(r'\s+', ' ', text_without_emojis).strip()
    return text_without_emojis


def translate_text(text, target_language='en'):
    """
    Translate text to target language using Groq API (Decoupled version)
    """
    text = remove_emojis(text)
    
    if target_language.lower() == 'en':
        return text
    
    # Pre-translated common phrases (instant)
    common_phrases = {
        'hi': {
            'runner game ready': 'रनर गेम तैयार',
            'Voice enabled': 'आवाज सक्षम',
            'User connected': 'उपयोगकर्ता जुड़ा',
            'Engine disconnected': 'इंजन डिस्कनेक्ट',
            'Engine connected': 'इंजन कनेक्ट',
            'Compiled runner game': 'रनर गेम संकलित',
            'Sent to engine': 'इंजन को भेजा गया',
            'Job completed': 'काम पूरा हुआ',
            'Game started': 'गेम शुरू हुआ',
            'Game over': 'गेम खत्म'
        },
        'es': {
            'runner game ready': 'juego de corredor listo',
            'Voice enabled': 'Voz habilitada',
            'User connected': 'Usuario conectado',
            'Engine connected': 'Motor conectado',
            'Sent to engine': 'Enviado al motor',
            'Job completed': 'Trabajo completado',
            'Game started': 'Juego iniciado',
            'Game over': 'Juego terminado'
        }
    }
    
    if target_language in common_phrases and text in common_phrases[target_language]:
        print(f"[TTS] Using pre-translated phrase for '{text}'")
        return common_phrases[target_language][text]
    
    # Check cache first
    cache_key = f"{text}:{target_language}"
    cache = load_cache()
    if cache_key in cache:
        print(f"[TTS] Using cached translation for '{text}'")
        return cache[cache_key]
    
    language_names = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
        'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese (Simplified)',
        'ja': 'Japanese', 'ko': 'Korean', 'hi': 'Hindi', 'ar': 'Arabic',
    }
    
    target_lang_name = language_names.get(target_language.lower(), 'English')
    
    try:
        # Get Groq configuration from environment variables
        api_key = os.getenv('GROQ_API_KEY')
        api_endpoint = os.getenv('GROQ_API_ENDPOINT', "https://api.groq.com/openai/v1/chat/completions")
        default_model = os.getenv('GROQ_MODEL_NAME', "llama-3.3-70b-versatile")
        
        if not api_key:
            print(f"[TTS] No GROQ_API_KEY found, skipping translation")
            return text
        
        word_count = len(text.split())
        max_tokens = min(max(word_count * 2, 100), 300)
        
        system_prompt = f"""You are a translation tool. Your ONLY job is to translate the given text to {target_lang_name}.
Return ONLY the translation, nothing else."""

        translation_prompt = f"Translate this text to {target_lang_name}:\n\n{text}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        fast_model = "llama-3.1-8b-instant"
        
        payload = {
            "model": fast_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": translation_prompt}
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(api_endpoint, headers=headers, json=payload, timeout=2)
            if response.status_code != 200:
                raise Exception(f"Fast model failed")
        except:
            # Fallback
            payload["model"] = default_model
            response = requests.post(api_endpoint, headers=headers, json=payload, timeout=3)
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result['choices'][0]['message']['content'].strip()
            # Basic cleanup
            translated_text = translated_text.strip('"').strip("'").strip()
            
            # Save to cache
            cache[cache_key] = translated_text
            save_cache(cache)
            
            return translated_text
        return text
        
    except Exception as e:
        print(f"[TTS] Translation failed: {e}")
        return text


def text_to_speech_stream(text, language='en', use_google_tts=True, translate=True):
    """
    Convert text to speech and return the audio data directly
    """
    if not text:
        raise ValueError("Text is required")
    
    import tempfile
    text = remove_emojis(text)
    
    if translate and language.lower() != 'en':
        text = translate_text(text, language)
    
    if use_google_tts:
        try:
            from gtts import gTTS
            import io
            tts = gTTS(text=text, lang=language.lower(), slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_data = audio_buffer.read()
            if audio_data:
                return audio_data
        except Exception as e:
            print(f"[TTS] Google TTS failed: {e}, falling back to pyttsx3")
            use_google_tts = False
    
    if not use_google_tts:
        engine = initialize_tts_engine(language)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filepath = temp_file.name

        try:
            engine.save_to_file(text, temp_filepath)
            engine.runAndWait()
            with open(temp_filepath, 'rb') as audio_file:
                audio_data = audio_file.read()
            os.unlink(temp_filepath)
            return audio_data
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
            raise e


def speak_text_directly(text):
    """
    Speak text directly without saving to file
    """
    if not text:
        raise ValueError("Text is required")
    engine = initialize_tts_engine()
    engine.say(text)
    engine.runAndWait()


if __name__ == "__main__":
    sample_text = "Hello, this is a portable text to speech example."
    print("Testing speak_text_directly...")
    # speak_text_directly(sample_text)
    print("Test complete.")
