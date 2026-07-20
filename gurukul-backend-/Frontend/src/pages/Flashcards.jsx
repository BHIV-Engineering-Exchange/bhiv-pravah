import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import LearningFlow from '../components/LearningFlow';
import { FaFlipboard, FaCheckCircle, FaTimesCircle, FaChartBar, FaBook, FaSpinner, FaArrowRight, FaArrowLeft, FaRedo } from 'react-icons/fa';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';
import { apiGet, apiPost, handleApiError } from '../utils/apiClient';
import { trackReflectionSession } from '../utils/progressTracker';
import { sendLifeEvent } from '../utils/karmaTrackerClient';

const Flashcards = () => {
    const { success, error } = useModal();
    const { user } = useAuth();
    const [cards, setCards] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [stats, setStats] = useState(null);
    const [reviewedCount, setReviewedCount] = useState(0);

    // Load pending reviews
    const loadPendingReviews = async () => {
        setLoading(true);
        try {
            const data = await apiGet('/api/v1/flashcards/reviews/pending');
            setCards(data);
            setCurrentIndex(0);
            setIsFlipped(false);
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'load flashcards' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    // Load stats
    const loadStats = async () => {
        try {
            const data = await apiGet('/api/v1/flashcards/reviews/stats');
            setStats(data);
        } catch (err) {
            // Silently fail for stats - not critical
            console.error('Error loading stats:', err);
        }
    };

    useEffect(() => {
        loadPendingReviews();
        loadStats();
    }, []);

    const currentCard = cards[currentIndex];

    const handleFlip = () => {
        setIsFlipped(!isFlipped);
    };

    const handleAnswer = async (difficulty) => {
        if (!currentCard || submitting) return;

        setSubmitting(true);
        try {
            // Simplified SRS mapping for frontend buttons
            // Green (Easy) -> easy
            // Yellow (Good) -> medium
            // Red (Hard) -> hard

            const result = await apiPost('/api/v1/flashcards/reviews', {
                card_id: currentCard.question_id || currentCard.id,  // Support both question_id and id
                difficulty: difficulty
            });

            // Remove current card from list
            const newCards = cards.filter((_, index) => index !== currentIndex);
            setCards(newCards);
            const newReviewedCount = reviewedCount + 1;
            setReviewedCount(newReviewedCount);

            // Track reflection session when all cards are reviewed
            if (newCards.length === 0) {
                trackReflectionSession();

                // Backend karma: completed a flashcard review session
                if (user?.id) {
                    sendLifeEvent({
                        userId: user.id,
                        action: 'completing_lessons',
                        note: `Completed flashcard review session (${newReviewedCount} cards)`,
                        context: 'source=flashcards'
                    });
                }
            }

            // Update stats
            loadStats();

            // Move to next card or reset
            if (newCards.length > 0) {
                if (currentIndex >= newCards.length) {
                    setCurrentIndex(newCards.length - 1);
                }
                setIsFlipped(false);
            } else {
                // No more cards
                setIsFlipped(false);
                setCurrentIndex(0);
            }
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'submit review' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setSubmitting(false);
        }
    };

    const handleNext = () => {
        if (currentIndex < cards.length - 1) {
            setCurrentIndex(currentIndex + 1);
            setIsFlipped(false);
        }
    };

    const handlePrevious = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
            setIsFlipped(false);
        }
    };

    const handleReset = () => {
        setIsFlipped(false);
        setCurrentIndex(0);
        loadPendingReviews();
        setReviewedCount(0);
    };

    if (loading) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
                <Sidebar />
                <main className="flex-grow flex items-center justify-center">
                    <div className="text-center">
                        <FaSpinner className="animate-spin text-4xl text-orange-500 mx-auto mb-4" />
                        <p className="text-gray-400">Loading flashcards...</p>
                    </div>
                </main>
            </div>
        );
    }

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Learning Flow - Guided Journey */}
                <div className="mb-4">
                    <LearningFlow currentStep="reflect" />
                </div>
                <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
                    {/* Main Flashcard Area */}
                    <div className="flex-grow flex flex-col items-center justify-center glass-panel no-hover p-6 sm:p-8 rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden min-h-[500px]">
                        {/* Background Glow */}
                        <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2"></div>

                        {cards.length === 0 ? (
                            <div className="text-center z-10">
                                <FaFlipboard className="text-6xl text-gray-600 mx-auto mb-6" />
                                <h2 className="text-2xl font-bold text-white mb-2">No Cards to Review!</h2>
                                <p className="text-gray-400 mb-6">You're all caught up. Great job! 🎉</p>
                                <button
                                    onClick={handleReset}
                                    className="px-6 py-3 bg-orange-600 hover:bg-orange-500 text-white rounded-xl transition-all font-medium flex items-center gap-2 mx-auto"
                                >
                                    <FaRedo /> Refresh
                                </button>
                            </div>
                        ) : (
                            <>
                                {/* Card Counter */}
                                <div className="absolute top-6 left-6 z-10">
                                    <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded-xl border border-white/10">
                                        <span className="text-sm text-gray-300">
                                            Card <span className="font-bold text-white">{currentIndex + 1}</span> of <span className="font-bold text-white">{cards.length}</span>
                                        </span>
                                    </div>
                                </div>

                                {/* Flashcard */}
                                <div className="relative w-full max-w-2xl z-10" style={{ perspective: '1000px' }}>
                                    <div
                                        className="relative w-full aspect-[4/3] cursor-pointer"
                                        onClick={handleFlip}
                                        style={{
                                            transformStyle: 'preserve-3d',
                                            transition: 'transform 0.6s',
                                            transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'
                                        }}
                                    >
                                        {/* Front of Card */}
                                        <div
                                            className="absolute inset-0 w-full h-full rounded-3xl p-8 sm:p-12 flex flex-col items-center justify-center glass-panel border-2 border-white/20 shadow-2xl"
                                            style={{
                                                backfaceVisibility: 'hidden',
                                                WebkitBackfaceVisibility: 'hidden',
                                                transform: 'rotateY(0deg)'
                                            }}
                                        >
                                            <div className="text-center">
                                                <FaBook className="text-4xl text-orange-400 mx-auto mb-4" />
                                                <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-4 font-bold">
                                                    {currentCard?.question_type?.toUpperCase() || 'QUESTION'}
                                                </h3>
                                                <p className="text-2xl sm:text-3xl font-bold text-white leading-relaxed">
                                                    {currentCard?.question || 'No question available'}
                                                </p>
                                                <p className="text-sm text-gray-400 mt-6">Click to flip</p>
                                            </div>
                                        </div>

                                        {/* Back of Card */}
                                        <div
                                            className="absolute inset-0 w-full h-full rounded-3xl p-8 sm:p-12 flex flex-col items-center justify-center glass-panel border-2 border-orange-500/50 shadow-2xl"
                                            style={{
                                                backfaceVisibility: 'hidden',
                                                WebkitBackfaceVisibility: 'hidden',
                                                transform: 'rotateY(180deg)'
                                            }}
                                        >
                                            <div className="text-center">
                                                <FaCheckCircle className="text-4xl text-green-400 mx-auto mb-4" />
                                                <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-4 font-bold">ANSWER</h3>
                                                <div className="text-xl sm:text-2xl text-gray-200 leading-relaxed whitespace-pre-wrap">
                                                    {currentCard?.answer || 'No answer available'}
                                                </div>
                                                {currentCard?.days_until_review !== undefined && (
                                                    <p className="text-sm text-gray-400 mt-4">
                                                        {currentCard.days_until_review > 0
                                                            ? `${currentCard.days_until_review} days overdue`
                                                            : 'Due for review'
                                                        }
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Navigation and Actions */}
                                    <div className="mt-8 flex flex-col items-center gap-4">
                                        {/* Card Navigation */}
                                        {cards.length > 1 && (
                                            <div className="flex items-center gap-4">
                                                <button
                                                    onClick={handlePrevious}
                                                    disabled={currentIndex === 0}
                                                    className="p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                                >
                                                    <FaArrowLeft className="text-white" />
                                                </button>
                                                <span className="text-gray-400 text-sm">
                                                    {currentIndex + 1} / {cards.length}
                                                </span>
                                                <button
                                                    onClick={handleNext}
                                                    disabled={currentIndex === cards.length - 1}
                                                    className="p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                                >
                                                    <FaArrowRight className="text-white" />
                                                </button>
                                            </div>
                                        )}

                                        {/* Answer Buttons (only show when flipped) */}
                                        {isFlipped && (
                                            <div className="flex gap-2 sm:gap-4 flex-wrap justify-center">
                                                <button
                                                    onClick={() => handleAnswer('hard')}
                                                    disabled={submitting}
                                                    className="px-4 py-3 sm:px-6 sm:py-4 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-xl border-2 border-red-500/50 transition-all font-bold flex items-center gap-2 disabled:opacity-50"
                                                >
                                                    <FaTimesCircle /> Hard (1d)
                                                </button>
                                                <button
                                                    onClick={() => handleAnswer('medium')}
                                                    disabled={submitting}
                                                    className="px-4 py-3 sm:px-6 sm:py-4 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 rounded-xl border-2 border-yellow-500/50 transition-all font-bold flex items-center gap-2 disabled:opacity-50"
                                                >
                                                    <FaCheckCircle /> Good (3d)
                                                </button>
                                                <button
                                                    onClick={() => handleAnswer('easy')}
                                                    disabled={submitting}
                                                    className="px-4 py-3 sm:px-6 sm:py-4 bg-green-600/20 hover:bg-green-600/30 text-green-400 rounded-xl border-2 border-green-500/50 transition-all font-bold flex items-center gap-2 disabled:opacity-50"
                                                >
                                                    <FaCheckCircle /> Easy (7d)
                                                </button>
                                            </div>
                                        )}

                                        {/* Flip Hint */}
                                        {!isFlipped && (
                                            <p className="text-sm text-gray-500">Click the card to see the answer</p>
                                        )}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Stats Sidebar */}
                    <div className="w-full lg:w-80 glass-panel no-hover p-4 sm:p-6 rounded-3xl border border-white/10 flex flex-col shadow-2xl h-fit">
                        <div className="flex items-center gap-3 mb-6">
                            <FaChartBar className="text-orange-500 text-xl" />
                            <h2 className="text-xl font-bold text-white">Progress Stats</h2>
                        </div>

                        {stats ? (
                            <div className="space-y-4">
                                {/* Total Questions */}
                                <div className="bg-black/60 p-4 rounded-xl border border-white/10">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-400 text-sm">Total Questions</span>
                                        <span className="text-2xl font-bold text-white">{stats.total_questions || 0}</span>
                                    </div>
                                </div>

                                {/* Pending Reviews */}
                                <div
                                    onClick={() => {
                                        loadPendingReviews();
                                        loadStats();
                                        setReviewedCount(0);
                                    }}
                                    className="bg-orange-500/10 p-4 rounded-xl border border-orange-500/30 cursor-pointer hover:bg-orange-500/20 transition-all group"
                                >
                                    <div className="flex justify-between items-center">
                                        <div className="flex flex-col">
                                            <span className="text-orange-300 text-sm">Pending Reviews</span>
                                            <span className="text-[10px] text-orange-400/60 group-hover:text-orange-400/80">Click to refresh</span>
                                        </div>
                                        <span className="text-2xl font-bold text-orange-400">{stats.pending_reviews || 0}</span>
                                    </div>
                                </div>

                                {/* Mastery Levels */}
                                <div className="space-y-3">
                                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Mastery Levels</h3>

                                    <div className="bg-blue-500/10 p-3 rounded-lg border border-blue-500/30">
                                        <div className="flex justify-between items-center">
                                            <span className="text-blue-300 text-sm">Learning</span>
                                            <span className="text-lg font-bold text-blue-400">{stats.learning || 0}</span>
                                        </div>
                                    </div>

                                    <div className="bg-yellow-500/10 p-3 rounded-lg border border-yellow-500/30">
                                        <div className="flex justify-between items-center">
                                            <span className="text-yellow-300 text-sm">Reviewing</span>
                                            <span className="text-lg font-bold text-yellow-400">{stats.reviewing || 0}</span>
                                        </div>
                                    </div>

                                    <div className="bg-green-500/10 p-3 rounded-lg border border-green-500/30">
                                        <div className="flex justify-between items-center">
                                            <span className="text-green-300 text-sm">Mastered</span>
                                            <span className="text-lg font-bold text-green-400">{stats.mastered || 0}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Session Stats */}
                                {reviewedCount > 0 && (
                                    <div className="bg-purple-500/10 p-4 rounded-xl border border-purple-500/30 mt-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-purple-300 text-sm">Reviewed This Session</span>
                                            <span className="text-2xl font-bold text-purple-400">{reviewedCount}</span>
                                        </div>
                                    </div>
                                )}

                                {/* Refresh Button */}
                                <button
                                    onClick={() => {
                                        loadPendingReviews();
                                        loadStats();
                                        setReviewedCount(0);
                                    }}
                                    className="w-full mt-4 px-4 py-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 transition-all font-medium flex items-center justify-center gap-2"
                                >
                                    <FaRedo /> Refresh Stats
                                </button>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <FaSpinner className="animate-spin text-2xl text-gray-500 mx-auto mb-2" />
                                <p className="text-gray-500 text-sm">Loading stats...</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Flashcards;

