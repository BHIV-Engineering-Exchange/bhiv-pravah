import React from 'react';
import { FaBookOpen, FaClipboardCheck, FaLightbulb, FaChartLine, FaCheckCircle } from 'react-icons/fa';

/**
 * Learning Progress Component
 * Shows visible learning progress through the journey
 * Calm, supportive, non-competitive
 */
const LearningProgress = () => {
    // Get progress from localStorage (would come from backend in production)
    const [progress, setProgress] = React.useState(() => {
        const saved = localStorage.getItem('gurukul_learning_progress');
        return saved ? JSON.parse(saved) : {
            topicsStudied: 0,
            practiceSessions: 0,
            reflectionSessions: 0,
            learningStreak: 0,
            lastActivity: null
        };
    });

    // Calculate overall progress (simple metric)
    const overallProgress = Math.min(
        ((progress.topicsStudied * 0.4) + 
         (progress.practiceSessions * 0.3) + 
         (progress.reflectionSessions * 0.3)) * 10,
        100
    );

    const milestones = [
        { id: 'enter', label: 'Topics Explored', count: progress.topicsStudied, icon: FaBookOpen, color: 'from-blue-500 to-cyan-500' },
        { id: 'practice', label: 'Practice Sessions', count: progress.practiceSessions, icon: FaClipboardCheck, color: 'from-green-500 to-teal-500' },
        { id: 'reflect', label: 'Reflection Sessions', count: progress.reflectionSessions, icon: FaLightbulb, color: 'from-orange-500 to-amber-500' },
    ];

    return (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 relative overflow-hidden">
            <div className="flex items-center justify-between mb-4 sm:mb-6">
                <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-400">
                        <FaChartLine className="text-sm sm:text-base" />
                    </div>
                    <h3 className="text-sm sm:text-base font-semibold text-gray-200">Learning Progress</h3>
                </div>
                {progress.learningStreak > 0 && (
                    <div className="text-xs text-gray-400">
                        {progress.learningStreak} day streak
                    </div>
                )}
            </div>

            {/* Overall Progress Circle */}
            <div className="flex items-center justify-center mb-6">
                <div className="relative w-24 h-24 sm:w-28 sm:h-28">
                    <svg className="transform -rotate-90 w-full h-full">
                        <circle
                            cx="50%"
                            cy="50%"
                            r="40%"
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="8"
                        />
                        <circle
                            cx="50%"
                            cy="50%"
                            r="40%"
                            fill="none"
                            stroke="url(#progressGradient)"
                            strokeWidth="8"
                            strokeDasharray={`${2 * Math.PI * 40}`}
                            strokeDashoffset={`${2 * Math.PI * 40 * (1 - overallProgress / 100)}`}
                            strokeLinecap="round"
                            className="transition-all duration-1000 ease-out"
                        />
                        <defs>
                            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="#667eea" />
                                <stop offset="100%" stopColor="#764ba2" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                            <div className="text-xl sm:text-2xl font-bold text-white tabular-nums">
                                {Math.round(overallProgress)}%
                            </div>
                            <div className="text-xs text-gray-400">Overall</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Milestones */}
            <div className="space-y-3">
                {milestones.map((milestone) => {
                    const Icon = milestone.icon;
                    return (
                        <div key={milestone.id} className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-gradient-to-br ${milestone.color} opacity-20`}>
                                <Icon className={`text-sm text-transparent bg-clip-text bg-gradient-to-br ${milestone.color}`} />
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs sm:text-sm text-gray-300">{milestone.label}</span>
                                    <span className="text-xs sm:text-sm font-semibold text-white tabular-nums">
                                        {milestone.count}
                                    </span>
                                </div>
                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full bg-gradient-to-r ${milestone.color} transition-all duration-1000 ease-out`}
                                        style={{ width: `${Math.min((milestone.count / 10) * 100, 100)}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Encouragement Message */}
            {overallProgress > 0 && (
                <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-white/10">
                    <p className="text-xs sm:text-sm text-gray-400 text-center italic">
                        {overallProgress < 30 && "You're beginning your learning journey. Keep going!"}
                        {overallProgress >= 30 && overallProgress < 60 && "You're making steady progress. Well done!"}
                        {overallProgress >= 60 && overallProgress < 90 && "You're doing great! Keep up the momentum."}
                        {overallProgress >= 90 && "Excellent progress! You're on a wonderful learning path."}
                    </p>
                </div>
            )}
        </div>
    );
};

export default LearningProgress;

