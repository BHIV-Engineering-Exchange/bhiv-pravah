import React, { useState } from 'react';
import { FaHeart, FaTimes, FaSmile, FaMeh, FaFrown, FaGrinStars, FaSadTear } from 'react-icons/fa';
import { apiPost, handleApiError } from '../utils/apiClient';

const ReflectionModal = ({ isOpen, onClose, onSuccess }) => {
    const [content, setContent] = useState('');
    const [mood, setMood] = useState(3); // 1-5
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    if (!isOpen) return null;

    const moods = [
        { score: 1, icon: FaSadTear, label: 'Struggling', color: 'text-red-400' },
        { score: 2, icon: FaFrown, label: 'Difficult', color: 'text-orange-400' },
        { score: 3, icon: FaMeh, label: 'Okay', color: 'text-yellow-400' },
        { score: 4, icon: FaSmile, label: 'Good', color: 'text-blue-400' },
        { score: 5, icon: FaGrinStars, label: 'Great', color: 'text-green-400' },
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!content.trim()) return;

        setLoading(true);
        setError(null);

        try {
            await apiPost('/api/v1/soul/reflections', {
                content,
                mood_score: mood
            });
            if (onSuccess) onSuccess();
            onClose();
            setContent('');
            setMood(3);
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'save reflection' });
            setError(errorInfo.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className="bg-[#0a0c08] border border-white/5 rounded-3xl w-full max-w-lg relative shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/40">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                        <FaHeart className="text-red-500" />
                        Daily Reflection
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <FaTimes />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {/* Mood Selector */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-3">How are you feeling today?</label>
                        <div className="flex justify-between gap-2 px-2">
                            {moods.map((m) => {
                                const Icon = m.icon;
                                const isSelected = mood === m.score;
                                return (
                                    <button
                                        key={m.score}
                                        type="button"
                                        onClick={() => setMood(m.score)}
                                        className={`flex flex-col items-center gap-2 p-2 rounded-xl transition-all ${isSelected ? 'scale-110' : 'opacity-50 hover:opacity-80'}`}
                                    >
                                        <div className={`text-2xl sm:text-3xl ${m.color}`}>
                                            <Icon />
                                        </div>
                                        <span className={`text-[10px] sm:text-xs font-medium ${isSelected ? 'text-white' : 'text-gray-500'}`}>
                                            {m.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Content Input */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">What did you learn about yourself?</label>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="I felt really focused when I..."
                            className="w-full h-32 bg-black/60 border border-white/5 rounded-xl p-4 text-white placeholder-gray-600 focus:outline-none focus:border-accent resize-none"
                            required
                        />
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                            {error}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-3 rounded-xl bg-black/40 hover:bg-black/60 text-gray-400 font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`flex-1 py-3 rounded-xl font-bold text-white transition-all shadow-lg ${loading ? 'bg-gray-700 cursor-not-allowed' : 'bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-400 hover:to-pink-500'}`}
                        >
                            {loading ? 'Saving...' : 'Log Reflection'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ReflectionModal;
