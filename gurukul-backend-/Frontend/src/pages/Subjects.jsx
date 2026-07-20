import React from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import LearningFlow from '../components/LearningFlow';
import LearningSuggestions from '../components/LearningSuggestions';
import { FaBook, FaLightbulb, FaBookOpen, FaFlipboard, FaChevronDown, FaPause, FaPlay } from 'react-icons/fa';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';
import { SkeletonBox, SkeletonCard } from '../components/LoadingSkeleton';
import { containsProfanity } from '../utils/profanityDetector';
import { apiPost, handleApiError } from '../utils/apiClient';
import { trackTopicStudied } from '../utils/progressTracker';
import { sendLifeEvent } from '../utils/karmaTrackerClient';
import vaaniClient from '../utils/vaaniClient';
import { FaVolumeUp } from 'react-icons/fa';

const Subjects = () => {
    const { alert, error, success } = useModal();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [subject, setSubject] = React.useState(() => localStorage.getItem('subjects_subject') || '');
    const [topic, setTopic] = React.useState(() => localStorage.getItem('subjects_topic') || '');
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(() => {
        const saved = localStorage.getItem('subjects_result');
        return saved ? JSON.parse(saved) : null;
    });
    const [chatInput, setChatInput] = React.useState('');
    const [chatHistory, setChatHistory] = React.useState(() => {
        const saved = localStorage.getItem('subjects_chatHistory');
        return saved ? JSON.parse(saved) : [];
    });
    const [chatLoading, setChatLoading] = React.useState(false);
    const [hasReceivedChatKarma, setHasReceivedChatKarma] = React.useState(false);
    const [isFlashcardModalOpen, setIsFlashcardModalOpen] = React.useState(false);
    const [flashcardGenerationStep, setFlashcardGenerationStep] = React.useState('select'); // 'select', 'loading', 'success'
    const [flashcardLoading, setFlashcardLoading] = React.useState(false);
    const [isNarrating, setIsNarrating] = React.useState(false);
    const [isPlaying, setIsPlaying] = React.useState(false);
    const [subtitleText, setSubtitleText] = React.useState('');

    // Narrate Lesson
    const toggleNarration = () => {
        if (isNarrating) {
            if (isPlaying) {
                vaaniClient.pause();
                setIsPlaying(false);
            } else {
                vaaniClient.resume();
                setIsPlaying(true);
            }
            return;
        }
        handleNarrate();
    };

    const handleNarrate = async () => {
        if (!result || !result.notes) return;

        // Stop any currently playing audio
        vaaniClient.stop();
        setIsNarrating(false);
        setIsPlaying(false);
        setSubtitleText('');

        setIsNarrating(true);
        try {
            // Clean text for TTS (reuse logic or keep simple)
            const cleanText = result.notes
                .replace(/\*\*([^*]+)\*\*/g, '$1')
                .replace(/^#{1,6}\s+/gm, '')
                .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
                .replace(/```[\s\S]*?```/g, '')
                .replace(/`([^`]+)`/g, '$1')
                .replace(/^[-*•]\s+/gm, '')
                .replace(/^\d+\.\s+/gm, '')
                .trim();

            setSubtitleText(cleanText);

            const lang = localStorage.getItem('selected_language') || 'en';
            const success = await vaaniClient.speak(cleanText, lang);

            if (success) {
                setIsPlaying(true);
                vaaniClient.audioElement.onended = () => {
                    setIsPlaying(false);
                    setIsNarrating(false);
                    setSubtitleText('');
                };
            } else {
                error('Failed to generate narration.', 'Narration Error');
                setIsNarrating(false);
                setSubtitleText('');
            }
        } catch (err) {
            error('Narration failed.', 'Error');
            setIsNarrating(false);
            setSubtitleText('');
        }
    };

    // Persistence Effects
    React.useEffect(() => {
        localStorage.setItem('subjects_subject', subject);
    }, [subject]);

    React.useEffect(() => {
        localStorage.setItem('subjects_topic', topic);
    }, [topic]);

    React.useEffect(() => {
        if (result) {
            localStorage.setItem('subjects_result', JSON.stringify(result));
        } else {
            localStorage.removeItem('subjects_result');
        }
    }, [result]);

    React.useEffect(() => {
        localStorage.setItem('subjects_chatHistory', JSON.stringify(chatHistory));
    }, [chatHistory]);

    const handleGenerate = async () => {
        if (!subject || !topic) {
            alert('To begin learning, please select both a subject and a topic. We\'re here to guide you.', 'Ready to Learn?');
            return;
        }

        setLoading(true);
        setResult(null);
        setChatHistory([]); // Reset chat for new topic

        try {
            const data = await apiPost('/api/v1/learning/explore', {
                subject,
                topic,
                provider: 'groq' // Default provider
            });

            if (data.success) {
                setResult(data);
                setHasReceivedChatKarma(false);
                // Track learning progress
                trackTopicStudied(subject, topic);

                // Backend karma: content generated & viewed
                if (user?.id) {
                    sendLifeEvent({
                        userId: user.id,
                        action: 'completing_lessons',
                        note: `Subject Explorer content generated for ${subject} - ${topic}`,
                        context: `source=subjects;subject=${subject};topic=${topic}`
                    });
                }
            } else {
                error('Failed to generate content: ' + (data.detail || 'Unknown error'), 'Generation Error');
            }
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'generate content' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleChat = async () => {
        if (!chatInput.trim() || !result) return;

        // Check for profanity
        if (containsProfanity(chatInput)) {
            // Backend karma: inappropriate language (negative)
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'cheat',
                    note: 'Inappropriate language detected in Subjects chat',
                    context: 'source=subjects-chat'
                });
            }
            alert('Let\'s keep our conversation respectful and focused on learning. Thank you for understanding.', 'Kind Reminder');
            return;
        }

        const userMessage = chatInput;
        setChatInput('');
        setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
        setChatLoading(true);

        // First chat message for this topic → solving doubts (positive)
        if (!hasReceivedChatKarma) {
            setHasReceivedChatKarma(true);
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'solving_doubts',
                    note: 'Started learning conversation in Subjects',
                    context: `source=subjects-chat;subject=${subject};topic=${topic}`
                });
            }
        }

        try {
            // Construct context-aware prompt
            const contextMessage = `Context from generated lesson on ${result.topic} (${result.subject}):\n${result.notes}\n\nUser Question: ${userMessage}`;

            const data = await apiPost('/api/v1/chat', {
                message: contextMessage,
                provider: 'groq',
                use_rag: false // We are providing context directly
            });

            if (data.response) {
                setChatHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
            } else {
                setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error responding to that.' }]);
            }
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'chat' });
            setChatHistory(prev => [...prev, {
                role: 'assistant',
                content: errorInfo.isNetworkError
                    ? 'Unable to connect. Please check your connection and try again.'
                    : 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setChatLoading(false);
        }
    };

    const handleOpenFlashcardModal = () => {
        setFlashcardGenerationStep('select');
        setIsFlashcardModalOpen(true);
    };

    const handleGenerateFlashcards = async (questionType) => {
        if (!result) return;

        setFlashcardGenerationStep('loading');
        setFlashcardLoading(true);

        try {
            // Prepare payload with Subject Explorer content
            const flashcardPayload = {
                title: `${result.topic} (${result.subject})`,
                content: result.notes, // Use the generated lesson notes
                date: new Date().toISOString(),
                question_type: questionType
            };

            // 1. Save Summary (optional, but good for tracking)
            try {
                await apiPost('/api/v1/learning/summaries/save', {
                    title: flashcardPayload.title,
                    content: flashcardPayload.content,
                    date: flashcardPayload.date
                });

                // Karma: reward generating a structured summary from Subject Explorer
                if (user?.id) {
                    sendLifeEvent({
                        userId: user.id,
                        action: 'completing_lessons',
                        note: `Generated Subject Explorer summary for ${result.subject} - ${result.topic}`,
                        context: `source=subjects-summary;subject=${result.subject};topic=${result.topic}`
                    });
                }
            } catch (err) {
                console.warn('Failed to save summary:', err);
                // Continue anyway
            }

            // 2. Generate Flashcards
            await apiPost('/api/v1/flashcards/generate', flashcardPayload);

            // 3. Karma: summary + flashcards generated from Subject Explorer
            if (user?.id) {
                sendLifeEvent({
                    userId: user.id,
                    action: 'completing_lessons',
                    note: `Generated summary + flashcards in Subject Explorer for ${result.subject} - ${result.topic}`,
                    context: `source=subjects-summary;subject=${result.subject};topic=${result.topic}`
                });
            }

            setFlashcardGenerationStep('success');

            // Auto-close modal after 2 seconds and navigate
            setTimeout(() => {
                setIsFlashcardModalOpen(false);
                navigate('/flashcards');
            }, 2000);

        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'generate flashcards' });
            error(errorInfo.message, errorInfo.title);
            setFlashcardGenerationStep('select');
        } finally {
            setFlashcardLoading(false);
        }
    };

    // Custom Markdown Renderer
    const renderContent = (text) => {
        if (!text) return null;

        // Split by lines to process block by block
        const lines = text.split('\n');
        const elements = [];

        let currentList = [];
        let listType = null; // 'ul' or 'ol'

        const flushList = () => {
            if (currentList.length > 0) {
                const ListTag = listType === 'ul' ? 'ul' : 'ol';
                const listClass = listType === 'ul' ? 'list-disc pl-6 space-y-2 mb-6 text-gray-300' : 'list-decimal pl-6 space-y-2 mb-6 text-gray-300';

                elements.push(
                    <ListTag key={`list-${elements.length}`} className={listClass}>
                        {currentList.map((item, idx) => (
                            <li key={idx}>
                                {parseInlineStyles(item)}
                            </li>
                        ))}
                    </ListTag>
                );
                currentList = [];
                listType = null;
            }
        };

        const parseInlineStyles = (text) => {
            // Split by bold syntax (**text**)
            const parts = text.split(/(\*\*.*?\*\*)/g);
            return parts.map((part, index) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={index} className="text-white font-bold">{part.slice(2, -2)}</strong>;
                }
                return part;
            });
        };

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();
            if (!trimmedLine) {
                flushList();
                return;
            }

            // Headers
            if (trimmedLine.startsWith('## ')) {
                flushList();
                elements.push(
                    <h2 key={`h2-${index}`} className="text-2xl font-bold text-accent mt-8 mb-4 border-l-4 border-accent pl-4">
                        {trimmedLine.replace('## ', '')}
                    </h2>
                );
            }
            else if (trimmedLine.startsWith('### ')) {
                flushList();
                elements.push(
                    <h3 key={`h3-${index}`} className="text-xl font-semibold text-white mt-6 mb-3">
                        {trimmedLine.replace('### ', '')}
                    </h3>
                );
            }
            // Bullet Lists
            else if (trimmedLine.startsWith('* ') || trimmedLine.startsWith('- ')) {
                if (listType === 'ol') flushList();
                listType = 'ul';
                currentList.push(trimmedLine.substring(2));
            }
            // Numbered Lists (Simple detection for 1. 2. etc)
            else if (/^\d+\.\s/.test(trimmedLine)) {
                if (listType === 'ul') flushList();
                listType = 'ol';
                currentList.push(trimmedLine.replace(/^\d+\.\s/, ''));
            }
            // Regular Paragraphs
            else {
                flushList();
                elements.push(
                    <p key={`p-${index}`} className="text-gray-300 leading-relaxed mb-4 text-lg">
                        {parseInlineStyles(trimmedLine)}
                    </p>
                );
            }
        });

        flushList(); // Flush any remaining list items
        return elements;
    };

    // Simplified Markdown Renderer for Chat
    const renderChatContent = (text) => {
        if (!text) return null;

        const lines = text.split('\n');
        const elements = [];

        let currentList = [];
        let listType = null;

        const flushList = () => {
            if (currentList.length > 0) {
                const ListTag = listType === 'ul' ? 'ul' : 'ol';
                const listClass = listType === 'ul' ? 'list-disc pl-4 space-y-1 mb-2' : 'list-decimal pl-4 space-y-1 mb-2';

                elements.push(
                    <ListTag key={`chat-list-${elements.length}`} className={listClass}>
                        {currentList.map((item, idx) => (
                            <li key={idx}>
                                {parseInlineStyles(item)}
                            </li>
                        ))}
                    </ListTag>
                );
                currentList = [];
                listType = null;
            }
        };

        const parseInlineStyles = (text) => {
            const parts = text.split(/(\*\*.*?\*\*)/g);
            return parts.map((part, index) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={index} className="font-bold">{part.slice(2, -2)}</strong>;
                }
                return part;
            });
        };

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();
            if (!trimmedLine) {
                flushList();
                return;
            }

            if (trimmedLine.startsWith('## ') || trimmedLine.startsWith('### ')) {
                flushList();
                elements.push(
                    <strong key={`h-${index}`} className="block mt-3 mb-1 font-bold text-accent">
                        {trimmedLine.replace(/^#+ /, '')}
                    </strong>
                );
            }
            else if (trimmedLine.startsWith('* ') || trimmedLine.startsWith('- ')) {
                if (listType === 'ol') flushList();
                listType = 'ul';
                currentList.push(trimmedLine.substring(2));
            }
            else if (/^\d+\.\s/.test(trimmedLine)) {
                if (listType === 'ul') flushList();
                listType = 'ol';
                currentList.push(trimmedLine.replace(/^\d+\.\s/, ''));
            }
            else {
                flushList();
                elements.push(
                    <p key={`p-${index}`} className="mb-2 leading-relaxed">
                        {parseInlineStyles(trimmedLine)}
                    </p>
                );
            }
        });

        flushList();
        return elements;
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-8 sm:pb-12">
            {/* Left Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="flex-grow flex flex-col gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Learning Flow - Guided Journey */}
                <div className="mb-4">
                    <LearningFlow currentStep="enter" />
                </div>

                {/* Center Panel - Subject Explorer Form */}
                {!loading && !result && (
                    <div className="flex-grow glass-panel no-hover p-4 sm:p-6 md:p-10 rounded-3xl border border-white/10 relative overflow-hidden flex flex-col items-center justify-center text-center shadow-2xl">

                        {/* Header */}
                        <div className="mb-6 sm:mb-8">
                            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold font-heading text-transparent bg-clip-text bg-gradient-to-r from-orange-100 to-orange-50 mb-3 sm:mb-4 drop-shadow-sm">
                                Subject Explorer
                            </h1>
                            <p className="text-gray-300 max-w-lg mx-auto font-light text-sm sm:text-base px-4">
                                Select a subject and enter a topic to begin your learning journey
                            </p>
                        </div>

                        {/* Form Container */}
                        <div className="w-full max-w-xl bg-black/60 backdrop-blur-sm p-4 sm:p-6 rounded-2xl border border-white/5 shadow-inner">

                            {/* Subject Input */}
                            <div className="mb-3 sm:mb-4 text-left">
                                <label className="block text-gray-300 text-xs sm:text-sm font-semibold mb-2 ml-1">Subject:</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                        <FaBook className="text-gray-500 group-focus-within:text-accent transition-colors" />
                                    </div>
                                    <input
                                        type="text"
                                        value={subject}
                                        onChange={(e) => setSubject(e.target.value)}
                                        placeholder="Type any subject (e.g. Mathematics)"
                                        className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent/50 transition-all font-medium"
                                    />
                                </div>
                            </div>

                            {/* Topic Input */}
                            <div className="mb-4 sm:mb-6 text-left">
                                <label className="block text-gray-300 text-xs sm:text-sm font-semibold mb-2 ml-1">Topic:</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                        <FaLightbulb className="text-gray-500 group-focus-within:text-accent transition-colors" />
                                    </div>
                                    <input
                                        type="text"
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        placeholder="Enter a topic needed"
                                        className="w-full pl-11 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent/50 transition-all font-medium"
                                    />
                                </div>
                            </div>

                            {/* Action Button */}
                            <button
                                onClick={handleGenerate}
                                className="w-full py-3 sm:py-4 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-bold text-base sm:text-lg rounded-xl shadow-lg transition-all transform hover:-translate-y-1 flex items-center justify-center gap-2"
                            >
                                <FaBookOpen />
                                Generate Lesson
                            </button>
                        </div>
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="flex-grow glass-panel no-hover p-4 sm:p-6 md:p-10 rounded-3xl border border-white/5 relative overflow-hidden flex flex-col gap-6 shadow-2xl">
                        <div className="text-center mb-4">
                            <SkeletonBox height="h-8" width="w-64" className="mx-auto mb-2" />
                            <SkeletonBox height="h-4" width="w-96" className="mx-auto" />
                        </div>
                        <div className="space-y-4">
                            <SkeletonCard />
                            <SkeletonCard />
                            <SkeletonCard />
                        </div>
                        <div className="text-center mt-4">
                            <p className="text-gray-400 text-sm">Generating your lesson...</p>
                        </div>
                    </div>
                )}

                {/* RESULTS SECTION */}
                {result && (
                    <div className="animate-fade-in-up">

                        {/* Notes & Chat Container */}
                        <div className="glass-panel p-3 sm:p-4 md:p-8 rounded-3xl border border-white/10 mb-4 sm:mb-6 bg-black/40">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0 mb-6 sm:mb-8 border-b border-white/10 pb-4 sm:pb-6">
                                <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-300 to-amber-200 flex items-center gap-2 sm:gap-3">
                                    <FaBookOpen className="text-orange-400 text-lg sm:text-xl" />
                                    {result.topic}
                                </h2>
                                <div className="flex items-center gap-2">
                                    <select
                                        value={vaaniClient.playbackRate}
                                        onChange={(e) => vaaniClient.setRate(parseFloat(e.target.value))}
                                        className="px-2 py-1 text-xs bg-white/5 border border-white/10 rounded text-gray-300 hover:bg-white/10 focus:outline-none focus:ring-1 focus:ring-accent cursor-pointer"
                                        title="Select speech speed"
                                    >
                                        <option value="0.8">0.8x</option>
                                        <option value="1.0">1.0x</option>
                                        <option value="1.2">1.2x</option>
                                        <option value="1.5">1.5x</option>
                                    </select>
                                    <button
                                        onClick={toggleNarration}
                                        className={`px-4 py-2 rounded-lg transition-all border flex items-center gap-2 shadow-lg ${isNarrating ? 'bg-accent/20 border-accent/50 text-accent' : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'}`}
                                    >
                                        {isNarrating ? (
                                            isPlaying ? <FaPause className="text-sm" /> : <FaPlay className="text-sm" />
                                        ) : (
                                            <FaVolumeUp className="text-sm" />
                                        )}
                                        {isNarrating ? (isPlaying ? 'Pause' : 'Resume') : 'Narrate Lesson'}
                                    </button>
                                    <button
                                        onClick={handleOpenFlashcardModal}
                                        className="px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white text-sm font-semibold rounded-lg transition-all border border-orange-500/50 flex items-center gap-2 shadow-lg shadow-orange-500/20 hover:-translate-y-0.5"
                                    >
                                        <FaFlipboard className="text-sm" />
                                        Generate Flashcards
                                    </button>
                                    <button
                                        onClick={() => setResult(null)}
                                        className="px-4 py-2 bg-white/5 hover:bg-white/10 text-sm text-gray-400 hover:text-white rounded-lg transition-colors border border-white/5 flex items-center gap-2"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                                        Explore New Topic
                                    </button>
                                </div>
                            </div>

                            {/* Notes Content */}
                            <div className="prose prose-invert max-w-none text-gray-200 leading-relaxed mb-6 sm:mb-8 p-4 sm:p-6 md:p-8 bg-black/20 rounded-2xl border border-white/5 shadow-inner text-sm sm:text-base">
                                {renderContent(result.notes)}
                            </div>

                            {/* Learning Suggestions - Natural Next Steps */}
                            <LearningSuggestions subject={result.subject} topic={result.topic} onSubjectPage={true} />

                            {/* Divider */}
                            <div className="h-px bg-white/10 my-8"></div>

                            {/* Contextual Chat Interface */}
                            <div className="bg-black/40 rounded-xl p-4 sm:p-6 border border-white/5">
                                <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4 flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                    Ask doubts about this topic
                                </h3>

                                {/* Chat History */}
                                {chatHistory.length > 0 && (
                                    <div className="mb-3 sm:mb-4 max-h-48 sm:max-h-60 overflow-y-auto space-y-2 sm:space-y-3 custom-scrollbar pr-2">
                                        {chatHistory.map((msg, idx) => (
                                            <div key={idx} className={`p-4 rounded-xl text-base ${msg.role === 'user' ? 'bg-orange-900/30 ml-auto border border-orange-500/20 max-w-[80%]' : 'bg-white/5 border border-white/10 max-w-[90%]'}`}>
                                                <span className={`font-bold block text-xs mb-1 ${msg.role === 'user' ? 'text-orange-400' : 'text-purple-400'}`}>
                                                    {msg.role === 'user' ? 'You' : 'AI Tutor'}
                                                </span>
                                                {renderChatContent(msg.content)}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Chat Input */}
                                <div className="relative flex gap-2">
                                    <input
                                        type="text"
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                                        placeholder="Ask a follow-up question..."
                                        className="flex-grow px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent/50"
                                    />
                                    <button
                                        onClick={handleChat}
                                        disabled={chatLoading}
                                        className="px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base bg-accent text-black font-bold rounded-xl hover:bg-accent/90 transition-colors disabled:opacity-50"
                                    >
                                        {chatLoading ? '...' : 'Send'}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* YouTube Recommendations */}
                        <div className="glass-panel p-4 sm:p-6 md:p-8 rounded-3xl border border-white/10 bg-black/40">
                            <h2 className="text-xl sm:text-2xl font-bold text-red-500 mb-4 sm:mb-6 flex items-center gap-2 sm:gap-3">
                                {/* Using text for icon if FaYoutube not imported, but assuming it works or fallback */}
                                Video Recommendations
                            </h2>

                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                                {result.youtube_recommendations.map((video, idx) => (
                                    <a
                                        key={idx}
                                        href={video.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="block group bg-black/60 rounded-xl overflow-hidden border border-white/5 hover:border-red-500/50 transition-all hover:transform hover:-translate-y-1"
                                    >
                                        <div className="relative aspect-video">
                                            <img src={video.thumbnail} alt={video.title} className="w-full h-full object-cover" />
                                            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                <div className="w-12 h-12 bg-red-600 rounded-full flex items-center justify-center">
                                                    <div className="w-0 h-0 border-t-8 border-t-transparent border-l-12 border-l-white border-b-8 border-b-transparent ml-1"></div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="p-4">
                                            <h3 className="text-white font-medium line-clamp-2 mb-2 group-hover:text-red-400 transition-colors">{video.title}</h3>
                                            <p className="text-gray-400 text-sm">{video.channel_title}</p>
                                        </div>
                                    </a>
                                ))}
                            </div>
                        </div>

                    </div>
                )}

                {/* Subtitle Overlay for Lesson Narration */}
                {subtitleText && isPlaying && (
                    <div className="fixed bottom-10 left-1/2 -translate-x-1/2 w-[90%] md:w-[60%] glass-panel bg-black/90 p-4 rounded-xl border border-accent/20 text-center animate-fade-in z-50">
                        <p className="text-accent text-sm md:text-lg font-medium leading-tight">
                            {subtitleText.length > 150 ? subtitleText.substring(0, 150) + '...' : subtitleText}
                        </p>
                    </div>
                )}
            </main>

            {/* Flashcard Generation Modal */}
            {isFlashcardModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
                    <div className="bg-[#1a1c16] border border-white/10 rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl relative">
                        <button
                            onClick={() => setIsFlashcardModalOpen(false)}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>

                        <h3 className="text-2xl font-bold text-white mb-2 text-center">
                            {flashcardGenerationStep === 'select' && "Generate Flashcards"}
                            {flashcardGenerationStep === 'loading' && "Creating Flashcards..."}
                            {flashcardGenerationStep === 'success' && "Flashcards Ready! 🎴"}
                        </h3>
                        <p className="text-gray-400 text-center mb-6 text-sm">
                            {flashcardGenerationStep === 'select' && `Create flashcards from "${result.topic}" to practice and review.`}
                            {flashcardGenerationStep === 'loading' && "Please wait while our AI creates your flashcards..."}
                            {flashcardGenerationStep === 'success' && "Your flashcards have been generated successfully!"}
                        </p>

                        {flashcardGenerationStep === 'select' && (
                            <div className="space-y-3">
                                <button
                                    onClick={() => handleGenerateFlashcards('conceptual')}
                                    disabled={flashcardLoading}
                                    className="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/50 rounded-xl flex items-center gap-4 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="w-10 h-10 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">?</div>
                                    <div className="text-left flex-1">
                                        <h4 className="font-bold text-white">General Questions</h4>
                                        <p className="text-xs text-gray-400">Conceptual Q&A based on the lesson</p>
                                    </div>
                                </button>

                                <button
                                    onClick={() => handleGenerateFlashcards('fill_in_blanks')}
                                    disabled={flashcardLoading}
                                    className="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/50 rounded-xl flex items-center gap-4 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="w-10 h-10 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">_</div>
                                    <div className="text-left flex-1">
                                        <h4 className="font-bold text-white">Fill in the Blanks</h4>
                                        <p className="text-xs text-gray-400">Complete the missing key terms</p>
                                    </div>
                                </button>

                                <button
                                    onClick={() => handleGenerateFlashcards('short_answer')}
                                    disabled={flashcardLoading}
                                    className="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/50 rounded-xl flex items-center gap-4 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="w-10 h-10 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">✎</div>
                                    <div className="text-left flex-1">
                                        <h4 className="font-bold text-white">One Line Answers</h4>
                                        <p className="text-xs text-gray-400">Short, precise recall questions</p>
                                    </div>
                                </button>

                                <button
                                    onClick={() => handleGenerateFlashcards('mcq')}
                                    disabled={flashcardLoading}
                                    className="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/50 rounded-xl flex items-center gap-4 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="w-10 h-10 rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">☑</div>
                                    <div className="text-left flex-1">
                                        <h4 className="font-bold text-white">Multiple Choice</h4>
                                        <p className="text-xs text-gray-400">Test with 4 options per question</p>
                                    </div>
                                </button>
                            </div>
                        )}

                        {flashcardGenerationStep === 'loading' && (
                            <div className="flex flex-col items-center justify-center py-8">
                                <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                                <p className="text-gray-400 text-sm">Generating your flashcards...</p>
                            </div>
                        )}

                        {flashcardGenerationStep === 'success' && (
                            <div className="space-y-4 text-center">
                                <div className="text-6xl mb-4">🎴</div>
                                <p className="text-white font-semibold">Redirecting to Flashcards page...</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

        </div>
    );
};

export default Subjects;
