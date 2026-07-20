import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

class VaaniClient {
    constructor() {
        this.cache = new Map();
        this.audioElement = new Audio();
        this.playbackRate = 1.0;
        this.isMuted = false;
        this.isPlaying = false;

        this.audioElement.onplay = () => { this.isPlaying = true; };
        this.audioElement.onended = () => { this.isPlaying = false; };
        this.audioElement.onpause = () => { this.isPlaying = false; };
    }

    setRate(rate) {
        this.playbackRate = rate;
        this.audioElement.playbackRate = rate;
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        this.audioElement.muted = this.isMuted;
        return this.isMuted;
    }

    /**
     * Authenticate with the system.
     */
    async login() {
        console.log('Vaani Client: Checking auth status...');
        return true;
    }

    /**
     * Generate TTS and return the audio URL.
     */
    async generateTTS(text, language = 'en') {
        if (this.isMuted) return null;

        try {
            const response = await axios.post(`${API_BASE_URL}/api/v1/agent/tts`, {
                text,
                language
            }, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.data.status === 'success') {
                const audioUrl = `${API_BASE_URL}${response.data.audio_url}`;
                return audioUrl;
            } else {
                throw new Error(response.data.message || 'TTS generation failed');
            }
        } catch (error) {
            console.error('Vaani Client Error:', error);
            throw error;
        }
    }

    /**
     * Play the audio for a given text.
     */
    async speak(text, language = 'en') {
        if (this.isMuted) return true;

        try {
            const audioUrl = await this.generateTTS(text, language);
            if (!audioUrl) return true;

            this.audioElement.src = audioUrl;
            this.audioElement.playbackRate = this.playbackRate;
            await this.audioElement.play();
            return true;
        } catch (error) {
            console.error('Playback failed:', error);
            return false;
        }
    }

    pause() {
        this.audioElement.pause();
    }

    resume() {
        if (this.audioElement.src) {
            this.audioElement.play();
        }
    }

    stop() {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
    }
}

const vaaniClient = new VaaniClient();
export default vaaniClient;
