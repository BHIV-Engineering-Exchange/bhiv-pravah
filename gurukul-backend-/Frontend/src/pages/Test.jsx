import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import LearningFlow from '../components/LearningFlow';
import { FaBrain, FaClock, FaQuestionCircle, FaBolt, FaPlay, FaChevronDown, FaCheckCircle, FaTimesCircle, FaArrowRight, FaArrowLeft, FaRedo } from 'react-icons/fa';
import { useModal } from '../contexts/ModalContext';
import { useAuth } from '../contexts/AuthContext';
import { apiPost, handleApiError } from '../utils/apiClient';
import { trackPracticeSession } from '../utils/progressTracker';
import { sendLifeEvent } from '../utils/karmaTrackerClient';

const Test = () => {
    const { alert, confirm, error } = useModal();
    const { user } = useAuth();
    // Mode: 'setup', 'taking', 'results'
    const [mode, setMode] = useState('setup');
    const [loading, setLoading] = useState(false);

    // Setup State
    const [subject, setSubject] = useState('');
    const [topic, setTopic] = useState('');
    const [difficulty, setDifficulty] = useState('medium');
    const [isSubjectOpen, setIsSubjectOpen] = useState(false);
    const [isDifficultyOpen, setIsDifficultyOpen] = useState(false);

    // Quiz Data State
    const [quizData, setQuizData] = useState(null); // Full response from generate
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({}); // { question_id: "A" | "B"... }

    // Results State
    
    // Cleanup timeouts on unmount
    useEffect(() => {
        return () => {
            // Cleanup any pending translation timeouts when component unmounts
            translationTimeoutsRef.current.forEach(id => clearTimeout(id));
            translationTimeoutsRef.current = [];
        };
    }, []);
    const [quizResult, setQuizResult] = useState(null); // Full result from submit

    const difficulties = ['easy', 'medium', 'hard'];
    const subjects = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science', 'History', 'Geography', 'Literature', 'Economics'];

    // Store timeout IDs for cleanup
    const translationTimeoutsRef = React.useRef([]);
    
    // Function to force Google Translate to re-translate dynamically added content
    const forceRetranslation = () => {
        try {
            const select = document.querySelector('.goog-te-combo');
            if (!select || !select.value || select.value === 'en') return;

            const currentLang = select.value;

            // Method 1: Trigger multiple change events to force re-processing
            for (let i = 0; i < 5; i++) {
                const timeoutId = setTimeout(() => {
                    try {
                        const event = new Event('change', { bubbles: true, cancelable: true });
                        select.dispatchEvent(event);
                    } catch (e) {
                        // Ignore
                    }
                }, i * 200);
                translationTimeoutsRef.current.push(timeoutId);
            }

            // Method 2: Temporarily toggle language to force full re-translation
            const timeout1 = setTimeout(() => {
                try {
                    const originalValue = select.value;
                    // Switch to English
                    select.value = 'en';
                    const event1 = new Event('change', { bubbles: true });
                    select.dispatchEvent(event1);

                    // Switch back to target language
                    const timeout2 = setTimeout(() => {
                        select.value = originalValue;
                        const event2 = new Event('change', { bubbles: true });
                        select.dispatchEvent(event2);

                        // Additional trigger after switching back
                        const timeout3 = setTimeout(() => {
                            const event3 = new Event('change', { bubbles: true });
                            select.dispatchEvent(event3);
                        }, 300);
                        translationTimeoutsRef.current.push(timeout3);
                    }, 500);
                    translationTimeoutsRef.current.push(timeout2);
                } catch (e) {
                    // Ignore
                }
            }, 1000);
            translationTimeoutsRef.current.push(timeout1);

        } catch (e) {
            if (process.env.NODE_ENV === 'development') {
                console.warn('Translation retry failed:', e);
            }
        }
    };

    // --- Handlers ---

    const handleGenerate = async () => {
        if (!subject || !topic) {
            alert("To create a practice quiz, please select both a subject and topic. This helps us tailor the questions for you.", "Ready to Practice?");
            return;
        }

        setLoading(true);
        try {
            const data = await apiPost('/api/v1/quiz/generate', {
                subject,
                topic,
                difficulty,
                provider: 'auto'
            });

            // Validate data structure
            if (!data || !data.questions || !Array.isArray(data.questions)) {
                throw new Error("Invalid quiz data received");
            }

            setQuizData(data);
            setAnswers({});
            setCurrentQuestionIndex(0);
            setMode('taking');

            // Force Google Translate to re-translate dynamically added content
            const retranslateTimeout = setTimeout(() => {
                forceRetranslation();
            }, 1000);
            
            // Store timeout ID for cleanup if component unmounts
            // Note: This timeout will be cleaned up when component unmounts or when quizData changes
            // For proper cleanup, we'd need useEffect, but since this is in an async handler,
            // we'll rely on component unmount cleanup. The timeout is short (1s) so low risk.
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'generate quiz' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerSelect = (questionId, optionKey) => {
        setAnswers(prev => ({
            ...prev,
            [questionId]: optionKey
        }));
    };

    const handleSubmit = async () => {
        const result = await confirm("Ready to see how you did? You can always practice again if you'd like.", "Submit Your Answers");
        if (!result) return;

        setLoading(true);
        try {
            const result = await apiPost('/api/v1/quiz/submit', {
                quiz_id: quizData.quiz_id,
                answers: answers // { q_id: "A", ... }
            });

            setQuizResult(result);

            // Track learning progress
            trackPracticeSession();

            // Backend karma: quiz performance-based rewards/penalties
            if (user?.id && result?.score != null && result?.total_questions) {
                const percentage = (result.score / result.total_questions) * 100;
                const rounded = Math.round(percentage);

                // 1) Below 40% → -10 (cheat / poor effort)
                if (rounded < 40) {
                    sendLifeEvent({
                        userId: user.id,
                        action: 'cheat',
                        note: `Quiz completed below 40% (${rounded}%)`,
                        context: `source=test;subject=${subject};topic=${topic};difficulty=${difficulty}`
                    });
                }
                // 2) Perfect score (100%) → +50 (5 × +10)
                else if (rounded === 100) {
                    for (let i = 0; i < 5; i++) {
                        sendLifeEvent({
                            userId: user.id,
                            action: 'completing_lessons',
                            note: `Quiz completed with a perfect score (100%)`,
                            context: `source=test;subject=${subject};topic=${topic};difficulty=${difficulty}`
                        });
                    }
                }
                // 3) Between 40% and 99% → +10
                else if (rounded >= 40) {
                    sendLifeEvent({
                        userId: user.id,
                        action: 'completing_lessons',
                        note: `Quiz completed with score ${rounded}%`,
                        context: `source=test;subject=${subject};topic=${topic};difficulty=${difficulty}`
                    });
                }
            }

            setMode('results');
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'submit quiz' });
            error(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    // --- Renderers ---

    const renderSetup = () => (
        <div className="w-full bg-gradient-to-br from-orange-900/10 to-black/20 border border-orange-500/20 rounded-2xl p-4 sm:p-6 md:p-8 relative group animate-fade-in-up">
            <div className="absolute inset-0 overflow-hidden rounded-2xl">
                <div className="absolute -top-20 -right-20 w-64 h-64 bg-orange-500/10 rounded-full blur-3xl group-hover:bg-orange-500/20 transition-all duration-700"></div>
            </div>

            <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                    <FaBrain className="text-2xl text-orange-400" />
                    <h2 className="text-2xl font-bold text-white">New Quiz Session</h2>
                </div>
                <p className="text-gray-400 mb-8 max-w-2xl text-sm">
                    Configure your AI-powered assessment.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
                    {/* Subject */}
                    <div className="relative z-50">
                        <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider pl-1 mb-2 block">Subject</label>
                        <div className="relative">
                            <button
                                onClick={() => setIsSubjectOpen(!isSubjectOpen)}
                                onBlur={() => setTimeout(() => setIsSubjectOpen(false), 200)}
                                className={`w-full p-4 rounded-xl bg-white/5 border text-left flex items-center justify-between transition-all duration-300 ${isSubjectOpen ? 'border-orange-500/50 ring-2 ring-orange-500/20 bg-white/10' : 'border-white/10 hover:bg-white/10'}`}
                            >
                                <span className={subject ? "text-white" : "text-gray-500"}>{subject || "Select Subject"}</span>
                                <FaChevronDown className={`text-xs text-gray-400 transition-transform duration-300 ${isSubjectOpen ? 'rotate-180' : ''}`} />
                            </button>
                            {isSubjectOpen && (
                                <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50 max-h-60 overflow-y-auto custom-scrollbar">
                                    {subjects.map(item => (
                                        <div key={item} onClick={() => { setSubject(item); setIsSubjectOpen(false); }} className="px-5 py-3 text-gray-300 hover:bg-white/5 hover:text-orange-400 cursor-pointer flex justify-between">
                                            {item}
                                            {subject === item && <div className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]"></div>}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Topic */}
                    <div>
                        <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider pl-1 mb-2 block">Topic</label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="e.g. Thermodynamics, Algebra..."
                            className="w-full p-4 rounded-xl bg-white/5 border border-white/10 text-gray-300 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-colors"
                        />
                    </div>

                    {/* Difficulty */}
                    <div className="relative z-40">
                        <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider pl-1 mb-2 block">Difficulty</label>
                        <div className="relative">
                            <button
                                onClick={() => setIsDifficultyOpen(!isDifficultyOpen)}
                                onBlur={() => setTimeout(() => setIsDifficultyOpen(false), 200)}
                                className={`w-full p-4 rounded-xl bg-white/5 border text-left flex items-center justify-between transition-all duration-300 ${isDifficultyOpen ? 'border-orange-500/50 ring-2 ring-orange-500/20 bg-white/10' : 'border-white/10 hover:bg-white/10'}`}
                            >
                                <span className="text-white capitalize">{difficulty}</span>
                                <FaChevronDown className={`text-xs text-gray-400 transition-transform duration-300 ${isDifficultyOpen ? 'rotate-180' : ''}`} />
                            </button>
                            {isDifficultyOpen && (
                                <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a1c16] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                                    {difficulties.map(item => (
                                        <div key={item} onClick={() => { setDifficulty(item); setIsDifficultyOpen(false); }} className="px-5 py-3 text-gray-300 hover:bg-white/5 hover:text-orange-400 cursor-pointer capitalize flex justify-between">
                                            {item}
                                            {difficulty === item && <div className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.8)]"></div>}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex justify-end notranslate">
                    <button
                        onClick={handleGenerate}
                        disabled={loading || !subject || !topic}
                        className="px-8 py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-bold rounded-lg shadow-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? <FaBolt className="animate-spin" /> : <FaPlay className="text-xs" />}
                        {loading ? "Generating Quiz..." : "Start Quiz"}
                    </button>
                </div>
            </div>
        </div>
    );

    // Trigger Google Translate when quiz data or question changes
    useEffect(() => {
        if (mode === 'taking' && quizData && quizData.questions) {
            // Delay to ensure DOM is fully updated
            setTimeout(() => {
                forceRetranslation();
            }, 800);
        }
    }, [mode, quizData, currentQuestionIndex]);

    const renderTaking = () => {
        if (!quizData || !quizData.questions || !Array.isArray(quizData.questions)) {
            return (
                <div className="w-full flex-grow flex items-center justify-center">
                    <div className="text-center">
                        <p className="text-red-400 mb-4">Error: Invalid quiz data</p>
                        <button
                            onClick={() => setMode('setup')}
                            className="px-6 py-3 bg-orange-600 hover:bg-orange-500 text-white rounded-lg"
                        >
                            Return to Setup
                        </button>
                    </div>
                </div>
            );
        }

        if (currentQuestionIndex >= quizData.questions.length) {
            setCurrentQuestionIndex(0);
            return null;
        }

        const currentQ = quizData.questions[currentQuestionIndex];
        if (!currentQ) {
            return null;
        }

        const progress = ((currentQuestionIndex + 1) / quizData.total_questions) * 100;
        const isLast = currentQuestionIndex === quizData.total_questions - 1;

        return (
            <div className="w-full flex-grow flex flex-col gap-6 animate-fade-in-up">
                {/* Header / Progress */}
                <div className="flex items-center justify-between text-gray-400 text-sm">
                    <span className="notranslate">Question {currentQuestionIndex + 1} of {quizData.total_questions}</span>
                    <span>{quizData.topic} • {quizData.difficulty}</span>
                </div>
                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-orange-500 transition-all duration-500" style={{ width: `${progress}%` }}></div>
                </div>

                {/* Question Card */}
                <div className="flex-grow glass-panel p-4 sm:p-6 md:p-8 rounded-3xl border border-white/10 flex flex-col justify-center">
                    <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-6 sm:mb-8 leading-snug" data-translate="yes">
                        {currentQ.question}
                    </h3>

                    <div className="grid grid-cols-1 gap-3 sm:gap-4">
                        {currentQ.options && Object.entries(currentQ.options).map(([key, text]) => (
                            <div
                                key={key}
                                onClick={() => handleAnswerSelect(currentQ.question_id, key)}
                                className={`p-4 rounded-xl border cursor-pointer flex items-center gap-4 transition-all duration-200 ${answers[currentQ.question_id] === key ? 'bg-orange-500/20 border-orange-500 text-white' : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'}`}
                                data-translate="yes"
                            >
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center border text-sm font-bold notranslate ${answers[currentQ.question_id] === key ? 'bg-orange-500 border-orange-500 text-white' : 'border-white/20 text-gray-500'}`}>
                                    {key}
                                </div>
                                <span className="text-lg" data-translate="yes">{text}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Navigation */}
                <div className="flex justify-between items-center mt-auto notranslate">
                    <button
                        onClick={() => setCurrentQuestionIndex(prev => Math.max(0, prev - 1))}
                        disabled={currentQuestionIndex === 0}
                        className="px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        <FaArrowLeft /> Previous
                    </button>
                    {isLast ? (
                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="px-8 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl shadow-lg transition-all flex items-center gap-2"
                        >
                            {loading ? "Submitting..." : "Submit Quiz"} <FaCheckCircle />
                        </button>
                    ) : (
                        <button
                            onClick={() => setCurrentQuestionIndex(prev => Math.min(quizData.total_questions - 1, prev + 1))}
                            className="px-6 py-3 rounded-xl bg-white/10 border border-white/10 text-white hover:bg-white/20 flex items-center gap-2"
                        >
                            Next <FaArrowRight />
                        </button>
                    )}
                </div>
            </div>
        );
    };

    const renderResults = () => {
        if (!quizResult) return null;

        return (
            <div className="w-full flex-grow flex flex-col gap-8 animate-fade-in-up">
                {/* Score Card */}
                <div className="w-full bg-gradient-to-r from-gray-900 to-black border border-white/10 rounded-3xl p-4 sm:p-6 md:p-8 flex flex-col md:flex-row items-center justify-between shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-l from-orange-500/10 to-transparent"></div>

                    <div className="z-10">
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">Quiz Complete!</h2>
                        <p className="text-sm sm:text-base text-gray-400">You scored {quizResult.correct_answers} out of {quizResult.total_questions}</p>
                    </div>

                    <div className="flex items-center gap-4 sm:gap-6 z-10 mt-6 md:mt-0">
                        <div className="text-center">
                            <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-orange-500">{quizResult.score_percentage}%</div>
                            <div className="text-xs text-orange-400 uppercase tracking-wide mt-1">Score</div>
                        </div>
                        <div className="h-12 w-px bg-white/10"></div>
                        <div className="text-center">
                            <div className="text-xl sm:text-2xl font-bold text-green-400">{quizResult.correct_answers}</div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide">Correct</div>
                        </div>
                        <div className="text-center">
                            <div className="text-xl sm:text-2xl font-bold text-red-400">{quizResult.wrong_answers}</div>
                            <div className="text-xs text-gray-500 uppercase tracking-wide">Wrong</div>
                        </div>
                    </div>
                </div>

                {/* Question Breakdown */}
                <div className="space-y-6">
                    <h3 className="text-xl font-bold text-white px-2">Detailed Analysis</h3>
                    {quizResult.results.map((q, idx) => (
                        <div key={idx} className={`glass-panel p-6 rounded-2xl border ${q.is_correct ? 'border-green-500/20 bg-green-900/5' : 'border-red-500/20 bg-red-900/5'}`}>
                            <div className="flex justify-between items-start mb-4">
                                <h4 className="text-lg font-medium text-gray-200">Q{q.question_number}. {q.question}</h4>
                                {q.is_correct ? <FaCheckCircle className="text-green-500 text-xl shrink-0" /> : <FaTimesCircle className="text-red-500 text-xl shrink-0" />}
                            </div>

                            <div className="flex flex-col gap-2 text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-500 w-24">Your Answer:</span>
                                    <span className={q.is_correct ? "text-green-400 font-medium" : "text-red-400 font-medium line-through"}>
                                        {q.user_answer || "Skipped"}
                                    </span>
                                </div>
                                {!q.is_correct && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-500 w-24">Correct Answer:</span>
                                        <span className="text-green-400 font-medium">{q.correct_answer}</span>
                                    </div>
                                )}
                            </div>

                            <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/5 text-sm text-gray-400 italic">
                                💡 {q.explanation}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="flex justify-center pb-12">
                    <button
                        onClick={() => { setMode('setup'); setSubject(''); setTopic(''); }}
                        className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl border border-white/10 transition-all flex items-center gap-2"
                    >
                        <FaRedo /> Take Another Quiz
                    </button>
                </div>
            </div>
        );
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Learning Flow - Guided Journey */}
                <div className="mb-4">
                    <LearningFlow currentStep="practice" />
                </div>
                <div className="flex-grow glass-panel no-hover p-4 sm:p-6 md:p-10 rounded-3xl border border-white/10 relative flex flex-col items-start justify-start shadow-2xl min-h-[calc(100vh-80px)] sm:min-h-[calc(100vh-100px)]">

                    {/* Header only in setup mode or sticky mini header? Let's just keep the title simple */}
                    <div className="mb-4 sm:mb-8 w-full flex justify-between items-center notranslate">
                        <div>
                            <h1 className="text-2xl sm:text-3xl font-bold font-heading text-white">Test Center</h1>
                            {mode === 'taking' && <p className="text-gray-500 text-xs sm:text-sm">Focus Mode Active</p>}
                        </div>
                        {mode !== 'setup' && (
                            <button onClick={async () => { const result = await confirm("Quit quiz?", "Quit Session"); if (result) setMode('setup'); }} className="text-xs text-red-400 hover:text-red-300 notranslate">Quit Session</button>
                        )}
                    </div>

                    {mode === 'setup' && renderSetup()}
                    {mode === 'taking' && renderTaking()}
                    {mode === 'results' && renderResults()}

                </div>
            </main>
        </div>
    );
};

export default Test;
