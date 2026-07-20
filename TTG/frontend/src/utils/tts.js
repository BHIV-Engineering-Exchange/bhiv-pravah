let ttsEnabled = false;
let autoEnableAttempted = false;

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3000';

const autoEnableTTS = () => {
  if (!autoEnableAttempted) {
    autoEnableAttempted = true;
    ttsEnabled = true;
  }
};

if (typeof window !== 'undefined') {
  window.addEventListener('click', autoEnableTTS, { once: true });
}

export const speak = async (text) => {
  if (!ttsEnabled) return;
  
  const language = localStorage.getItem('pref_language') || 'en';
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/tts/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language })
    });
    
    if (response.ok) {
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
      audio.onended = () => URL.revokeObjectURL(audioUrl);
    }
  } catch (err) {
    console.error('TTS error:', err);
  }
};

export const enableTTS = () => {
  ttsEnabled = true;
  autoEnableAttempted = true;
  speak('Voice enabled');
};

export const isTTSEnabled = () => ttsEnabled;
