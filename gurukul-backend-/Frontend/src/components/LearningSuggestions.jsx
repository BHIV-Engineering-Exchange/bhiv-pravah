import React from 'react';
import { Link } from 'react-router-dom';
import { FaClipboardCheck, FaLightbulb, FaArrowRight } from 'react-icons/fa';

/**
 * Learning Suggestions Component
 * Suggests natural next steps after learning (Practice, Reflect)
 * Makes flashcards and quizzes feel integrated into the learning flow
 */
const LearningSuggestions = ({ subject, topic, onSubjectPage = false }) => {
    if (!subject || !topic) return null;

    return (
        <div className="mt-6 p-4 sm:p-6 bg-gradient-to-br from-orange-900/10 to-black/20 border border-orange-500/20 rounded-2xl">
            <div className="flex items-center gap-2 mb-4">
                <FaLightbulb className="text-orange-400 text-lg" />
                <h3 className="text-sm sm:text-base font-semibold text-gray-200">Continue Your Learning Journey</h3>
            </div>
            
            <p className="text-xs sm:text-sm text-gray-400 mb-4">
                You've explored <span className="text-orange-400 font-medium">{topic}</span> in <span className="text-orange-400 font-medium">{subject}</span>. 
                Here are natural next steps to deepen your understanding:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                {/* Practice Suggestion */}
                <Link
                    to="/test"
                    state={{ subject, topic }}
                    className="group flex items-center justify-between p-3 sm:p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/30 rounded-xl transition-all duration-300"
                >
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-green-500/20 text-green-400">
                            <FaClipboardCheck className="text-sm sm:text-base" />
                        </div>
                        <div>
                            <div className="text-xs sm:text-sm font-semibold text-white group-hover:text-orange-300 transition-colors">
                                Practice with a Quiz
                            </div>
                            <div className="text-xs text-gray-400">
                                Test your understanding
                            </div>
                        </div>
                    </div>
                    <FaArrowRight className="text-gray-400 group-hover:text-orange-400 transition-colors text-xs sm:text-sm" />
                </Link>

                {/* Reflection Suggestion */}
                <Link
                    to="/flashcards"
                    state={{ subject, topic }}
                    className="group flex items-center justify-between p-3 sm:p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-orange-500/30 rounded-xl transition-all duration-300"
                >
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-orange-500/20 text-orange-400">
                            <FaLightbulb className="text-sm sm:text-base" />
                        </div>
                        <div>
                            <div className="text-xs sm:text-sm font-semibold text-white group-hover:text-orange-300 transition-colors">
                                Reflect with Flashcards
                            </div>
                            <div className="text-xs text-gray-400">
                                Review and reinforce
                            </div>
                        </div>
                    </div>
                    <FaArrowRight className="text-gray-400 group-hover:text-orange-400 transition-colors text-xs sm:text-sm" />
                </Link>
            </div>

            {onSubjectPage && (
                <div className="mt-4 pt-4 border-t border-white/10">
                    <p className="text-xs text-gray-500 italic text-center">
                        Remember: Learning is a journey. Take your time, and return to practice whenever you're ready.
                    </p>
                </div>
            )}
        </div>
    );
};

export default LearningSuggestions;

