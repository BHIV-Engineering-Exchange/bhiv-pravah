import React, { createContext, useContext, useState, useEffect } from 'react';
import vaaniClient from '../utils/vaaniClient';

const VoiceContext = createContext(null);

export const useVoice = () => useContext(VoiceContext);

export const VoiceManager = ({ children }) => {
    const [isNarrating, setIsNarrating] = useState(false);
    const [currentText, setCurrentText] = useState('');
    const [error, setError] = useState(null);
    const [playbackRate, setPlaybackRate] = useState(vaaniClient.playbackRate);
    const [isMuted, setIsMuted] = useState(vaaniClient.isMuted);

    const speak = async (text, lang) => {
        setIsNarrating(true);
        setCurrentText(text);
        setError(null);
        try {
            const success = await vaaniClient.speak(text, lang);
            if (!success) {
                setError('Failed to generate speech');
            }
            return success;
        } catch (err) {
            setError(err.message);
            return false;
        } finally {
            setIsNarrating(false);
        }
    };

    const stop = () => {
        vaaniClient.stop();
        setIsNarrating(false);
        setCurrentText('');
    };

    const setRate = (rate) => {
        vaaniClient.setRate(rate);
        setPlaybackRate(rate);
    };

    const toggleMute = () => {
        const muted = vaaniClient.toggleMute();
        setIsMuted(muted);
    };

    const value = {
        isNarrating,
        currentText,
        error,
        speak,
        stop,
        playbackRate,
        setRate,
        isMuted,
        toggleMute,
        isPlaying: vaaniClient.isPlaying
    };

    return (
        <VoiceContext.Provider value={value}>
            {children}
            {/* Global Voice Overlay or Feedback could go here */}
        </VoiceContext.Provider>
    );
};

export default VoiceManager;
