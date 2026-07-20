import React from 'react';
import Sidebar from '../components/Sidebar';
import { FaVolumeUp, FaPlus, FaHistory, FaTrashAlt, FaPaperclip, FaArrowUp, FaChevronDown, FaPause, FaPlay } from 'react-icons/fa';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';
import { SkeletonBox } from '../components/LoadingSkeleton';

import { containsProfanity } from '../utils/profanityDetector';
import { apiPost, apiGet, apiDelete, handleApiError } from '../utils/apiClient';
import { sendLifeEvent } from '../utils/karmaTrackerClient';
import vaaniClient from '../utils/vaaniClient';

const Chatbot = () => {
    const { alert, confirm, success, error } = useModal();
    const { user } = useAuth();
    const [message, setMessage] = React.useState('');
    const [selectedModel, setSelectedModel] = React.useState(() => localStorage.getItem('chatbot_selectedModel') || 'Grok');
    const [isModelOpen, setIsModelOpen] = React.useState(false);
    const [chatHistory, setChatHistory] = React.useState(() => {
        const saved = localStorage.getItem('chatbot_chatHistory');
        return saved ? JSON.parse(saved) : [
            {
                role: 'assistant',
                content: "🙏 Namaste! I am Gurukul, your personal AI guide to ancient wisdom and modern learning. What knowledge are you seeking today?"
            }
        ];
    });
    const [loading, setLoading] = React.useState(false);
    const [conversationId, setConversationId] = React.useState(() => localStorage.getItem('chatbot_conversationId') || null);
    const chatEndRef = React.useRef(null);
    const deleteMenuRef = React.useRef(null);

    // State for Features
    const [showHistory, setShowHistory] = React.useState(false);
    const [savedChats, setSavedChats] = React.useState([]);
    const [showDeleteMenu, setShowDeleteMenu] = React.useState(false);
    const [hasReceivedChatKarma, setHasReceivedChatKarma] = React.useState(() => {
        return localStorage.getItem('chatbot_hasReceivedChatKarma') === 'true';
    });



    // Map website language code to TTS code (e.g. zh-CN -> zh)
    const websiteLangToTTS = (code) => {
        if (!code) return 'en';
        if (code === 'zh-CN') return 'zh';
        return code;
    };
    const getWebsiteLanguage = () => websiteLangToTTS(localStorage.getItem('selected_language'));

    // TTS State: sync with website language so TTS matches the language the site is displayed in
    const [isTTSLoading, setIsTTSLoading] = React.useState(false);
    const [ttsLanguage, setTTSLanguage] = React.useState(() =>
        getWebsiteLanguage() || localStorage.getItem('chatbot_tts_language') || 'en'
    );
    const [ttsProvider, setTTSProvider] = React.useState('local');
    const [playingAudioIndex, setPlayingAudioIndex] = React.useState(null);
    const [currentAudio, setCurrentAudio] = React.useState(null);

    // Active Persistence Effects
    React.useEffect(() => {
        localStorage.setItem('chatbot_selectedModel', selectedModel);
    }, [selectedModel]);

    React.useEffect(() => {
        localStorage.setItem('chatbot_chatHistory', JSON.stringify(chatHistory));
    }, [chatHistory]);

    React.useEffect(() => {
        if (conversationId) {
            localStorage.setItem('chatbot_conversationId', conversationId);
        } else {
            localStorage.removeItem('chatbot_conversationId');
        }
    }, [conversationId]);

    React.useEffect(() => {
        localStorage.setItem('chatbot_hasReceivedChatKarma', hasReceivedChatKarma.toString());
    }, [hasReceivedChatKarma]);

    React.useEffect(() => {
        localStorage.setItem('chatbot_tts_language', ttsLanguage);
    }, [ttsLanguage]);

    React.useEffect(() => {
        localStorage.setItem('chatbot_tts_provider', ttsProvider);
    }, [ttsProvider]);

    // Sync TTS language with website language when user changes language in dashboard (same tab or other tab)
    React.useEffect(() => {
        const onLanguageChanged = (e) => {
            try {
                const code = e.detail?.language ?? e.newValue;
                if (code) {
                    const ttsCode = websiteLangToTTS(code);
                    if (ttsCode) {
                        setTTSLanguage(ttsCode);
                    } else {
                        setTTSLanguage('en'); // Fallback to English
                    }
                }
            } catch (err) {
                // Silent fallback on error
                setTTSLanguage('en');
            }
        };
        const onCustom = (e) => {
            try {
                onLanguageChanged({ detail: e.detail });
            } catch (err) {
                setTTSLanguage('en'); // Fallback
            }
        };
        const onStorage = (e) => {
            try {
                if (e.key === 'selected_language' && e.newValue != null) {
                    onLanguageChanged({ newValue: e.newValue });
                }
            } catch (err) {
                setTTSLanguage('en'); // Fallback
            }
        };
        window.addEventListener('gurukul-language-changed', onCustom);
        window.addEventListener('storage', onStorage);
        return () => {
            window.removeEventListener('gurukul-language-changed', onCustom);
            window.removeEventListener('storage', onStorage);
        };
    }, []);

    // When Chatbot page gains focus, refresh TTS language from current website language
    React.useEffect(() => {
        const onFocus = () => {
            const siteLang = getWebsiteLanguage();
            if (siteLang) setTTSLanguage(siteLang);
        };
        window.addEventListener('focus', onFocus);
        return () => window.removeEventListener('focus', onFocus);
    }, []);

    // Initial Load of History
    React.useEffect(() => {
        const loaded = localStorage.getItem('gurukul_saved_chats');
        if (loaded) setSavedChats(JSON.parse(loaded));
    }, []);

    // Auto-scroll to bottom
    React.useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory]);

    // Close delete menu when clicking outside
    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (deleteMenuRef.current && !deleteMenuRef.current.contains(event.target)) {
                setShowDeleteMenu(false);
            }
        };

        if (showDeleteMenu) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => {
                document.removeEventListener('mousedown', handleClickOutside);
            };
        }
    }, [showDeleteMenu]);

    // Cleanup audio on unmount
    React.useEffect(() => {
        return () => {
            if (currentAudio) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }
        };
    }, [currentAudio]);

    // Save History Helper
    const saveToHistory = (id, firstMessage) => {
        setSavedChats(prev => {
            if (prev.find(c => c.id === id)) return prev; // Already saved
            const newChat = {
                id,
                title: firstMessage.substring(0, 30) + (firstMessage.length > 30 ? '...' : ''),
                date: new Date().toLocaleDateString()
            };
            const updated = [newChat, ...prev];
            localStorage.setItem('gurukul_saved_chats', JSON.stringify(updated));
            return updated;
        });
    };

    const handleSendMessage = async () => {
        if (!message.trim()) return;

        // Check for profanity
        if (containsProfanity(message)) {
            // Backend karma: inappropriate language (negative)
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'cheat',
                    note: 'Inappropriate language detected in Chatbot',
                    context: 'source=chatbot'
                });
            }
            alert('Let\'s keep our conversation respectful and focused on learning. Thank you for understanding.', 'Kind Reminder');
            return;
        }

        const userMsg = { role: 'user', content: message };
        setChatHistory(prev => [...prev, userMsg]);
        const currentMsg = message; // Capture for title
        setMessage('');
        setLoading(true);

        // Timeout handling: Show error if loading takes too long (60s max)
        const timeoutId = setTimeout(() => {
            if (loading) {
                setLoading(false);
                setChatHistory(prev => [...prev, {
                    role: 'assistant',
                    content: "I apologize, but the request is taking longer than expected. Please try again."
                }]);
            }
        }, 60000);

        // First chat message in this conversation → solving doubts (positive)
        if (!hasReceivedChatKarma && !conversationId) {
            setHasReceivedChatKarma(true);
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'solving_doubts',
                    note: 'Started learning conversation in Chatbot',
                    context: 'source=chatbot'
                });
            }
        }

        try {
            const data = await apiPost('/api/v1/chat', {
                message: userMsg.content,
                conversation_id: conversationId,
                provider: selectedModel,
                use_rag: true
            });

            // Clear timeout on success
            clearTimeout(timeoutId);

            if (data.conversation_id) {
                setConversationId(data.conversation_id);
                // If this is the start of a clean conversation, save it
                if (!conversationId) {
                    saveToHistory(data.conversation_id, currentMsg);
                }
            }

            const botMsg = { role: 'assistant', content: data.response };
            setChatHistory(prev => [...prev, botMsg]);
        } catch (err) {
            clearTimeout(timeoutId); // Clear timeout on error
            const errorInfo = handleApiError(err, { operation: 'chat' });
            setChatHistory(prev => [...prev, {
                role: 'assistant',
                content: errorInfo.isNetworkError
                    ? "I apologize, but I'm unable to connect to the wisdom source right now. Please check your connection and try again."
                    : "I apologize, but I encountered an error. Please try again."
            }]);
        } finally {
            clearTimeout(timeoutId); // Ensure timeout is cleared
            setLoading(false);
        }
    };

    const handleNewChat = () => {
        // Stop any playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            setCurrentAudio(null);
            setPlayingAudioIndex(null);
        }

        setChatHistory([
            {
                role: 'assistant',
                content: "🙏 Namaste! I am Gurukul, your personal AI guide to ancient wisdom and modern learning. What new topic shall we explore?"
            }
        ]);
        setConversationId(null);
        setHasReceivedChatKarma(false);
        setShowHistory(false);
        // Clear persistence for current active chat
        localStorage.removeItem('chatbot_chatHistory');
        localStorage.removeItem('chatbot_conversationId');
        localStorage.removeItem('chatbot_hasReceivedChatKarma');
    };

    const handleLoadChat = async (id) => {
        setLoading(true);
        setShowHistory(false);
        try {
            const data = await apiGet(`/api/v1/chat/history/${id}`);

            // Transform backend messages to UI format
            // Backend sends: role, content
            if (data.messages && data.messages.length > 0) {
                setChatHistory(data.messages.map(m => ({ role: m.role, content: m.content })));
                setConversationId(id);
            } else {
                // No history found on backend (maybe server restarted)
                // Start a fresh conversation with the same ID
                setChatHistory([
                    {
                        role: 'assistant',
                        content: "🙏 This conversation was not found on the server (it may have been lost after a restart). Starting fresh!"
                    }
                ]);
                setConversationId(id);
            }
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'load chat history' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteCurrent = async (e) => {
        e?.stopPropagation();
        e?.preventDefault();

        if (!conversationId) {
            alert("No active chat to delete. Start a conversation first.", "No Active Chat");
            setShowDeleteMenu(false);
            return;
        }

        const result = await confirm("Delete this conversation permanently?", "Delete Chat");
        if (!result) {
            setShowDeleteMenu(false);
            return;
        }

        try {
            await apiDelete(`/api/v1/chat/history/${conversationId}`);

            // Remove from local list
            const updated = savedChats.filter(c => c.id !== conversationId);
            setSavedChats(updated);
            localStorage.setItem('gurukul_saved_chats', JSON.stringify(updated));

            handleNewChat();
            setShowDeleteMenu(false);
            success("Chat deleted successfully", "Success");
        } catch (err) {
            if (process.env.NODE_ENV === 'development') {
                console.error("Delete error:", err);
            }
            const errorInfo = handleApiError(err, { operation: 'delete chat' });
            error(errorInfo.message, errorInfo.title);
            setShowDeleteMenu(false);
        }
    };

    const handleDeleteAll = async (e) => {
        e?.stopPropagation();
        e?.preventDefault();

        const result = await confirm("Are you sure you want to clear your ENTIRE chat history list? This cannot be undone.", "Clear All History");
        if (!result) {
            setShowDeleteMenu(false);
            return;
        }

        // Clear all saved chats
        setSavedChats([]);
        localStorage.removeItem('gurukul_saved_chats');
        handleNewChat();
        setShowDeleteMenu(false);
    };



    const handleClearChat = () => {
        // Stop any playing audio
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
            setCurrentAudio(null);
            setPlayingAudioIndex(null);
        }

        setChatHistory([
            {
                role: 'assistant',
                content: "🙏 Namaste! I am Gurukul, your personal AI guide. The slate is clean. What shall we discuss?"
            }
        ]);
        setConversationId(null);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Remove markdown formatting from text for TTS
    const cleanTextForTTS = (text) => {
        if (!text) return '';

        return text
            // Remove bold/italic markdown: **text** or *text* or __text__ or _text_
            .replace(/\*\*([^*]+)\*\*/g, '$1')  // **bold**
            .replace(/\*([^*]+)\*/g, '$1')      // *italic* or *bold*
            .replace(/__([^_]+)__/g, '$1')      // __bold__
            .replace(/_([^_]+)_/g, '$1')        // _italic_
            // Remove markdown headers: #, ##, ###
            .replace(/^#{1,6}\s+/gm, '')
            // Remove markdown links: [text](url)
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
            // Remove markdown code blocks: `code` or ```code```
            .replace(/```[\s\S]*?```/g, '')
            .replace(/`([^`]+)`/g, '$1')
            // Remove markdown lists: - item or * item or 1. item
            .replace(/^[-*•]\s+/gm, '')
            .replace(/^\d+\.\s+/gm, '')
            // Remove extra whitespace and clean up
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    };

    const [isPlaying, setIsPlaying] = React.useState(false);
    const [subtitleText, setSubtitleText] = React.useState('');

    const togglePlayback = (messageContent, messageIndex) => {
        if (playingAudioIndex === messageIndex) {
            if (isPlaying) {
                vaaniClient.pause();
                setIsPlaying(false);
            } else {
                vaaniClient.resume();
                setIsPlaying(true);
            }
            return;
        }
        handleTTS(messageContent, messageIndex);
    };

    const handleTTS = async (messageContent, messageIndex) => {
        // Stop any currently playing audio
        vaaniClient.stop();
        setPlayingAudioIndex(null);
        setIsPlaying(false);
        setSubtitleText('');

        if (!messageContent || !messageContent.trim()) {
            error('No message to convert to speech', 'TTS Error');
            return;
        }

        const cleanedText = cleanTextForTTS(messageContent);
        setSubtitleText(cleanedText);

        setIsTTSLoading(true);
        try {
            setPlayingAudioIndex(messageIndex);
            const success = await vaaniClient.speak(cleanedText, ttsLanguage);

            if (success) {
                setIsPlaying(true);
                // Simple sync: clear subtitle when audio ends
                vaaniClient.audioElement.onended = () => {
                    setIsPlaying(false);
                    setPlayingAudioIndex(null);
                    setSubtitleText('');
                };
            } else {
                error('Failed to generate speech. Please try again.', 'TTS Error');
                setPlayingAudioIndex(null);
                setSubtitleText('');
            }
        } catch (err) {
            error(err.message || 'Failed to generate speech. Please try again.', 'TTS Error');
            setPlayingAudioIndex(null);
            setSubtitleText('');
        } finally {
            setIsTTSLoading(false);
        }
    };

    // Simplified Markdown Renderer
    const renderChatContent = (text) => {
        return text.split('\n').map((line, i) => {
            if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
                return <li key={i} className="ml-4 list-disc text-lg">{line.trim().substring(2)}</li>;
            }
            // Headers
            if (line.trim().startsWith('### ')) {
                return <h3 key={i} className="text-xl font-bold mt-2 mb-1 text-accent">{line.trim().replace('### ', '')}</h3>;
            }
            if (line.trim().startsWith('## ')) {
                return <h2 key={i} className="text-2xl font-bold mt-3 mb-2 text-accent">{line.trim().replace('## ', '')}</h2>;
            }
            // Bold
            const parts = line.split(/(\*\*.*?\*\*)/g);
            return (
                <p key={i} className="mb-1 leading-relaxed text-lg">
                    {parts.map((part, j) => {
                        if (part.startsWith('**') && part.endsWith('**')) {
                            return <strong key={j} className="text-accent font-bold">{part.slice(2, -2)}</strong>;
                        }
                        return part;
                    })}
                </p>
            );
        });
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 relative">
            {/* Left Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-grow flex gap-3 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>

                {/* Center Panel - Chat Interface */}
                <div className="flex-grow glass-panel no-hover rounded-3xl border border-white/10 relative overflow-hidden flex flex-col shadow-2xl h-[calc(100vh-80px)] sm:h-[calc(100vh-100px)]">

                    {/* Header */}
                    <div className="flex items-center justify-between p-3 sm:p-4 md:p-6 pb-3 sm:pb-4 shrink-0 border-b border-white/5">
                        <div className="flex items-center gap-2 sm:gap-4">
                            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold font-heading text-white">Chatbot</h1>
                            {/* Language Selector */}
                            <select
                                value={ttsLanguage}
                                onChange={(e) => setTTSLanguage(e.target.value)}
                                className="px-2 py-1 text-xs bg-white/5 border border-white/10 rounded text-gray-300 hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-accent cursor-pointer"
                                title="Select TTS language for audio playback"
                            >
                                <option value="en">🇺🇸 English</option>
                                <option value="es">🇪🇸 Spanish</option>
                                <option value="fr">🇫🇷 French</option>
                                <option value="de">🇩🇪 German</option>
                                <option value="it">🇮🇹 Italian</option>
                                <option value="pt">🇵🇹 Portuguese</option>
                                <option value="ru">🇷🇺 Russian</option>
                                <option value="zh">🇨🇳 Chinese</option>
                                <option value="ja">🇯🇵 Japanese</option>
                                <option value="ko">🇰🇷 Korean</option>
                                <option value="hi">🇮🇳 Hindi</option>
                                <option value="ar">🇸🇦 Arabic</option>
                            </select>
                            <select
                                value={vaaniClient.playbackRate}
                                onChange={(e) => vaaniClient.setRate(parseFloat(e.target.value))}
                                className="px-2 py-1 text-xs bg-white/5 border border-white/10 rounded text-gray-300 hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-accent cursor-pointer"
                                title="Select speech speed"
                            >
                                <option value="0.8">0.8x Slow</option>
                                <option value="1.0">1.0x Normal</option>
                                <option value="1.2">1.2x Fast</option>
                                <option value="1.5">1.5x Rapid</option>
                            </select>
                            <div className="px-3 py-1 text-xs bg-white/5 border border-white/10 rounded text-accent font-medium flex items-center gap-1" title="Sovereign Vaani TTS Engine">
                                🎙️ Vaani Sovereign Voice
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={handleNewChat}
                                className="flex items-center gap-2 px-3 md:px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-gray-300 transition-colors border border-white/5"
                            >
                                <FaPlus className="text-xs" /> <span className="hidden md:inline">New Chat</span>
                            </button>
                            <button
                                onClick={() => setShowHistory(!showHistory)}
                                className={`p-2 transition-colors ${showHistory ? 'text-accent bg-white/10 rounded-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                <FaHistory />
                            </button>

                            <div className="relative" ref={deleteMenuRef}>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setShowDeleteMenu(!showDeleteMenu);
                                    }}
                                    className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                                >
                                    <FaTrashAlt />
                                </button>
                                {/* Delete Dropdown */}
                                {showDeleteMenu && (
                                    <div
                                        className="absolute right-0 top-full mt-2 w-48 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
                                        onClick={(e) => e.stopPropagation()}
                                    >
                                        <button
                                            onClick={handleDeleteCurrent}
                                            disabled={!conversationId}
                                            className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-red-900/20 hover:text-red-400 disabled:opacity-50 disabled:cursor-not-allowed border-b border-white/5"
                                        >
                                            Delete Current Chat
                                        </button>
                                        <button
                                            onClick={handleDeleteAll}
                                            className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-red-900/20 font-medium"
                                        >
                                            Clear All History
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Chat Area - Edge to Edge Scrollbar */}
                    <div className="flex-grow overflow-y-scroll custom-scrollbar flex flex-col px-3 sm:px-4 md:px-6">
                        <div className="mt-auto py-4 sm:py-6 space-y-4 sm:space-y-6">
                            {chatHistory.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                                    <p>Start a conversation...</p>
                                </div>
                            ) : (
                                <div className="flex flex-col space-y-6">
                                    {chatHistory.map((msg, index) => (
                                        <div key={index} className={`flex flex-col gap-1 items-${msg.role === 'user' ? 'end' : 'start'} max-w-full`}>
                                            <div className={`glass-panel p-4 rounded-2xl ${msg.role === 'user' ? 'rounded-tr-none bg-white/20 border border-white/10 text-white font-medium' : 'rounded-tl-none bg-white/5 border border-white/5 text-gray-200'} text-lg leading-relaxed shadow-sm max-w-[85%] relative group`}>
                                                {msg.role === 'user' ? msg.content : renderChatContent(msg.content)}
                                                {/* Audio button for assistant messages */}
                                                {msg.role === 'assistant' && (
                                                    <button
                                                        onClick={() => togglePlayback(msg.content, index)}
                                                        disabled={isTTSLoading && playingAudioIndex !== index}
                                                        className={`absolute top-2 right-2 p-1.5 transition-colors rounded-lg hover:bg-white/10 ${playingAudioIndex === index
                                                            ? 'text-accent'
                                                            : 'text-gray-600 hover:text-gray-400'
                                                            } ${isTTSLoading && playingAudioIndex !== index ? 'opacity-50 cursor-not-allowed' : ''}`}
                                                        title={playingAudioIndex === index ? (isPlaying ? "Pause" : "Resume") : "Convert to speech"}
                                                    >
                                                        {playingAudioIndex === index ? (
                                                            isPlaying ? <FaPause className="text-sm" /> : <FaPlay className="text-sm" />
                                                        ) : (
                                                            <FaVolumeUp className="text-sm" />
                                                        )}
                                                    </button>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 px-1">
                                                <span className="text-xs text-gray-500 font-medium capitalize">{msg.role === 'user' ? 'You' : 'Guru AI'}</span>
                                                {msg.role === 'assistant' && (
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-200 border border-amber-500/20">{selectedModel}</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {loading && (
                                <div className="flex flex-col gap-1 items-start max-w-2xl">
                                    <div className="glass-panel p-4 rounded-2xl rounded-tl-none bg-white/5 border border-white/5 shadow-sm">
                                        <div className="flex gap-2">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                    </div>

                    {/* Subtitle Overlay */}
                    {subtitleText && isPlaying && (
                        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 w-[90%] md:w-[70%] glass-panel bg-black/80 p-3 rounded-xl border border-accent/20 text-center animate-fade-in z-40">
                            <p className="text-accent text-sm md:text-base font-medium leading-tight">
                                {subtitleText.length > 100 ? subtitleText.substring(0, 100) + '...' : subtitleText}
                            </p>
                        </div>
                    )}

                    {/* Input Area */}
                    <div className="p-3 sm:p-4 md:p-6 pt-0 shrink-0">
                        <div className="bg-black/60 backdrop-blur-sm p-3 sm:p-4 rounded-2xl border border-white/5 shadow-inner flex items-center gap-2 sm:gap-4 relative">

                            {/* Model Selector (Custom Dropdown) */}
                            <div className="relative">
                                <button
                                    onClick={() => setIsModelOpen(!isModelOpen)}
                                    onBlur={() => setTimeout(() => setIsModelOpen(false), 200)}
                                    className={`flex items-center gap-2 bg-white/5 border text-gray-300 py-1.5 px-2 md:px-4 rounded-lg hover:bg-white/10 transition-all duration-300 text-xs font-medium ${isModelOpen ? 'border-accent/50 ring-2 ring-accent/20 bg-white/10 text-white' : 'border-white/10'}`}
                                >
                                    <span className="hidden md:inline">{selectedModel}</span>
                                    <span className="md:hidden">{selectedModel.substring(0, 1)}</span>
                                    <FaChevronDown className={`text-[10px] text-gray-400 transition-transform duration-300 ${isModelOpen ? 'rotate-180' : ''}`} />
                                </button>
                                {/* ... dropdown ... */}
                                <div className={`absolute bottom-full mb-2 left-0 w-32 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden transition-all duration-300 origin-bottom ${isModelOpen ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-2 pointer-events-none'}`}>
                                    {['Grok', 'Uniguru'].map((model) => (
                                        <div
                                            key={model}
                                            onClick={() => {
                                                setSelectedModel(model);
                                                setIsModelOpen(false);
                                            }}
                                            className="px-4 py-2 text-xs text-gray-300 hover:bg-white/5 hover:text-accent cursor-pointer transition-colors flex items-center justify-between group"
                                        >
                                            {model}
                                            {selectedModel === model && <div className="w-1 h-1 rounded-full bg-accent shadow-[0_0_5px_rgba(232,185,117,0.8)]"></div>}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Text Input */}
                            <input
                                type="text"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Ask..."
                                className="flex-grow bg-transparent border-none outline-none text-gray-200 placeholder-gray-500 font-light text-sm md:text-base min-w-0"
                                onKeyDown={handleKeyDown}
                            />

                            {/* Send Button */}
                            <button
                                onClick={handleSendMessage}
                                disabled={loading || !message.trim()}
                                className="p-3 bg-accent/20 hover:bg-accent/30 text-accent rounded-xl transition-all shadow-lg border border-accent/10 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <FaArrowUp />
                            </button>
                        </div>
                        <p className="text-center text-[10px] text-gray-600 mt-2 font-mono">Tip: Use Shift+Enter for a new line</p>

                    </div>
                </div>

                {/* History Sidebar Panel (Overlay) */}
                {showHistory && (
                    <div className="fixed sm:absolute right-2 sm:right-4 top-20 sm:top-24 bottom-2 sm:bottom-4 w-[calc(100vw-1rem)] sm:w-80 max-w-sm glass-panel border border-white/10 rounded-3xl z-50 flex flex-col overflow-hidden animate-fade-in-up bg-[#0f110c]/95">
                        <div className="p-6 border-b border-white/10 flex justify-between items-center">
                            <h2 className="text-xl font-heading font-bold text-white">History</h2>
                            <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-white"><FaChevronDown className="rotate-90" /></button>
                        </div>
                        <div className="flex-grow overflow-y-auto custom-scrollbar p-4 space-y-2">
                            {savedChats.length === 0 ? (
                                <p className="text-center text-gray-500 text-sm mt-10">No history yet.</p>
                            ) : (
                                savedChats.map((chat) => (
                                    <div
                                        key={chat.id}
                                        onClick={() => handleLoadChat(chat.id)}
                                        className={`p-3 rounded-xl cursor-pointer transition-all border ${chat.id === conversationId ? 'bg-accent/10 border-accent/30' : 'bg-white/5 border-transparent hover:bg-white/10'}`}
                                    >
                                        <h3 className="text-sm font-medium text-gray-200 truncate">{chat.title}</h3>
                                        <p className="text-[10px] text-gray-500 mt-1">{chat.date}</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}



            </main>
        </div>
    );
};

export default Chatbot;
