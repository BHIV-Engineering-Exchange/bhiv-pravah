import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Volume2, Square, Loader, ChevronDown } from 'lucide-react';
import { taskService } from '../services/taskService';

// Static fallback languages shown before API loads
const FALLBACK_LANGUAGES = {
    en: { language_name: 'English', tones: ['neutral', 'educational', 'formal', 'friendly', 'excited', 'calm'] },
    hi: { language_name: 'Hindi',   tones: ['neutral', 'educational', 'friendly'] },
    ar: { language_name: 'Arabic',  tones: ['neutral', 'educational', 'formal', 'friendly', 'excited', 'calm'] },
    fr: { language_name: 'French',  tones: ['neutral', 'educational'] },
    de: { language_name: 'German',  tones: ['neutral', 'formal'] },
    es: { language_name: 'Spanish', tones: ['neutral', 'friendly'] },
};

// Shared language cache — fetched once per session
let _langCache = null;
let _langFetchPromise = null;

const fetchLanguages = () => {
    if (_langCache) return Promise.resolve(_langCache);
    if (_langFetchPromise) return _langFetchPromise;
    _langFetchPromise = taskService.getTtsLanguages()
        .then(data => { _langCache = data.supported_languages; return _langCache; })
        .catch(() => { _langCache = FALLBACK_LANGUAGES; return _langCache; });
    return _langFetchPromise;
};

/**
 * VaaniTtsButton
 * Props:
 *   text      — string to speak (required)
 *   lang      — default language code (default: 'en')
 *   tone      — default tone (default: 'neutral')
 *   showControls — show lang/tone selectors (default: false)
 *   className — extra CSS classes
 */
const TtsButton = ({
    text,
    lang: defaultLang = 'en',
    tone: defaultTone = 'neutral',
    showControls = false,
    className = ''
}) => {
    const [state, setState]         = useState('idle'); // idle|loading|playing|error
    const [lang, setLang]           = useState(defaultLang);
    const [tone, setTone]           = useState(defaultTone);
    const [languages, setLanguages] = useState(FALLBACK_LANGUAGES);
    const [open, setOpen]           = useState(false);
    const audioRef                  = useRef(null);
    const dropdownRef               = useRef(null);

    // Load languages from Vaani API once
    useEffect(() => {
        fetchLanguages().then(setLanguages);
    }, []);

    // Reset tone when language changes if current tone not available
    useEffect(() => {
        const available = languages[lang]?.tones || ['neutral'];
        if (!available.includes(tone)) setTone(available[0]);
    }, [lang, languages]);

    // Cleanup audio on text change or unmount
    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.src = '';
                audioRef.current = null;
            }
        };
    }, [text]);

    // Close dropdown on outside click
    useEffect(() => {
        if (!open) return;
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    const handleToggle = useCallback(() => {
        if (state === 'playing') {
            audioRef.current?.pause();
            if (audioRef.current) audioRef.current.currentTime = 0;
            setState('idle');
            return;
        }
        if (!text?.trim()) return;

        setState('loading');
        const url = taskService.getTtsStream(text, lang, tone);

        if (!audioRef.current) audioRef.current = new Audio();
        audioRef.current.src = url;
        audioRef.current.onended = () => setState('idle');
        audioRef.current.onerror = () => setState('error');
        audioRef.current.play()
            .then(() => setState('playing'))
            .catch(() => setState('error'));
    }, [state, text, lang, tone]);

    const availableTones = languages[lang]?.tones || ['neutral'];
    const langName       = languages[lang]?.language_name || lang.toUpperCase();

    const icon = {
        idle:    <Volume2 size={14} />,
        loading: <Loader  size={14} className="animate-spin" />,
        playing: <Square  size={14} fill="currentColor" />,
        error:   <Volume2 size={14} className="opacity-40" />,
    }[state];

    const label = {
        idle:    'Listen',
        loading: 'Loading…',
        playing: 'Stop',
        error:   'Unavailable',
    }[state];

    return (
        <div className={`inline-flex items-center gap-1 ${className}`} ref={dropdownRef}>
            {/* Main speak button */}
            <button
                onClick={handleToggle}
                disabled={state === 'loading' || state === 'error' || !text?.trim()}
                title={state === 'error' ? 'TTS unavailable' : `${label} (${langName} · ${tone})`}
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold
                    text-blue-600 dark:text-blue-400
                    hover:bg-blue-50 dark:hover:bg-blue-900/20
                    disabled:opacity-40 disabled:cursor-not-allowed
                    transition-colors"
            >
                {icon}
                <span>{label}</span>
            </button>

            {/* Controls toggle */}
            {showControls && (
                <div className="relative">
                    <button
                        onClick={() => setOpen(o => !o)}
                        title="Language & tone settings"
                        className="p-1 rounded text-slate-400 hover:text-blue-500
                            hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                    >
                        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
                    </button>

                    {open && (
                        <div className="absolute right-0 top-7 z-50 w-52 bg-white dark:bg-slate-800
                            border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl p-3 space-y-3">

                            {/* Language selector */}
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                    Language
                                </label>
                                <select
                                    value={lang}
                                    onChange={e => setLang(e.target.value)}
                                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-600
                                        bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200
                                        px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
                                >
                                    {Object.entries(languages).map(([code, data]) => (
                                        <option key={code} value={code}>
                                            {data.language_name} ({code})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Tone selector */}
                            <div>
                                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                                    Tone
                                </label>
                                <select
                                    value={tone}
                                    onChange={e => setTone(e.target.value)}
                                    className="w-full text-xs rounded-lg border border-slate-200 dark:border-slate-600
                                        bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200
                                        px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
                                >
                                    {availableTones.map(t => (
                                        <option key={t} value={t}>
                                            {t.charAt(0).toUpperCase() + t.slice(1)}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="text-xs text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-700">
                                Powered by Vaani TTS
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default TtsButton;
