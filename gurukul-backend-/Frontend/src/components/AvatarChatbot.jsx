import React, { useState, useRef, useEffect } from 'react';
import { FaTimes, FaPaperPlane, FaRobot } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { apiPost, handleApiError } from '../utils/apiClient';

const AvatarChatbot = ({ position, onClose }) => {
    const [messages, setMessages] = useState([{
        role: 'assistant',
        content: '👋 Hi! I\'m your website assistant. Ask me anything about navigating or using Gurukul!'
    }]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef(null);

    // Smart positioning near avatar
    const getChatPosition = () => {
        const isMobile = window.innerWidth < 640;
        const chatWidth = isMobile ? window.innerWidth - 32 : 350;
        const chatHeight = isMobile ? 400 : 500;
        const padding = 20;

        // Try to position to the left of avatar
        let left = position.x - chatWidth - 20;
        let top = position.y;

        // If too far left, position to the right
        if (left < padding) {
            left = position.x + 150;
        }

        // If too far right, adjust
        if (left + chatWidth > window.innerWidth - padding) {
            left = window.innerWidth - chatWidth - padding;
        }

        // Adjust vertical position
        if (top + chatHeight > window.innerHeight - padding) {
            top = window.innerHeight - chatHeight - padding;
        }

        if (top < padding) {
            top = padding;
        }

        return { left: `${left}px`, top: `${top}px` };
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const data = await apiPost('/api/v1/chat', {
                message: `Context: You are a helpful website assistant for Gurukul, an educational platform. Help users navigate the website, understand features, and answer questions about how to use the platform. Be concise and friendly. User question: ${input}`,
                provider: 'auto',
                use_rag: false
            });

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.response
            }]);
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'website assistant chat' });
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: errorInfo.isNetworkError 
                    ? 'Unable to connect right now. Please check your connection.' 
                    : 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div
            style={getChatPosition()}
            className="fixed w-[calc(100vw-2rem)] sm:w-[350px] h-[400px] sm:h-[500px] max-h-[80vh] bg-black/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-orange-500/30 flex flex-col z-[10000] animate-fade-in-up"
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10 bg-gradient-to-r from-orange-600/20 to-amber-600/20">
                <h3 className="font-bold text-white flex items-center gap-2 text-sm">
                    <FaRobot className="text-orange-400" />
                    Website Assistant
                </h3>
                <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                >
                    <FaTimes />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.role === 'user'
                            ? 'bg-orange-600 text-white rounded-br-none'
                            : 'bg-white/10 text-gray-200 rounded-bl-none'
                            }`}>
                            {msg.role === 'assistant' ? (
                                <ReactMarkdown>
                                    {msg.content}
                                </ReactMarkdown>
                            ) : (
                                <p>{msg.content}</p>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white/10 text-gray-200 p-3 rounded-lg text-sm rounded-bl-none">
                            <div className="flex gap-1">
                                <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                <div className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/10 bg-black/50">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about the website..."
                        className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm outline-none focus:border-orange-500 transition-colors"
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="bg-orange-600 hover:bg-orange-500 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <FaPaperPlane className="text-sm" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AvatarChatbot;
