import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowRight, FaBookOpen, FaClipboardCheck, FaLightbulb, FaChartLine } from 'react-icons/fa';

/**
 * Next Step Card Component
 * Shows students what they should do next in their learning journey
 */
const NextStepCard = ({ currentStep = 'enter' }) => {
    const navigate = useNavigate();

    // Define what comes next for each step
    const nextStepMap = {
        'enter': {
            label: 'Start Learning',
            description: 'Begin with your chosen subject',
            path: '/lectures',
            icon: FaBookOpen,
            color: 'from-purple-600/70 to-indigo-600/70', // Calm purple
            actionText: 'Go to Lectures'
        },
        'learn': {
            label: 'Practice What You Learned',
            description: 'Test your knowledge with a quiz',
            path: '/test',
            icon: FaClipboardCheck,
            color: 'from-emerald-600/70 to-teal-600/70', // Calm green
            actionText: 'Take a Quiz'
        },
        'practice': {
            label: 'Review with Flashcards',
            description: 'Reinforce your learning',
            path: '/flashcards',
            icon: FaLightbulb,
            color: 'from-amber-600/70 to-yellow-600/70', // Calm amber
            actionText: 'Review Flashcards'
        },
        'reflect': {
            label: 'Track Your Progress',
            description: 'See how far you\'ve come',
            path: '/dashboard',
            icon: FaChartLine,
            color: 'from-slate-600/70 to-gray-600/70', // Calm gray
            actionText: 'View Progress'
        },
        'improve': {
            label: 'Continue Your Journey',
            description: 'Choose your next topic',
            path: '/subjects',
            icon: FaBookOpen,
            color: 'from-blue-600/70 to-cyan-600/70', // Calm blue
            actionText: 'Explore Subjects'
        }
    };

    const nextStep = nextStepMap[currentStep] || nextStepMap['enter'];
    const Icon = nextStep.icon;

    return (
        <div className="w-full max-w-6xl mx-auto px-4 mb-6">
            <div
                className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-black/80 to-black/60 backdrop-blur-sm border-2 border-accent/20 p-6 sm:p-8 shadow-2xl"
            >
                {/* Background Gradient */}
                <div className={`absolute inset-0 bg-gradient-to-br ${nextStep.color} opacity-5`}></div>

                {/* Content */}
                <div className="relative z-10 flex flex-col sm:flex-row items-center justify-between gap-6">
                    {/* Left Side - Info */}
                    <div className="flex items-center gap-4 sm:gap-6">
                        {/* Icon */}
                        <div className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-br ${nextStep.color} flex items-center justify-center shadow-lg flex-shrink-0`}>
                            <Icon className="text-white text-2xl sm:text-3xl" />
                        </div>

                        {/* Text */}
                        <div>
                            <p className="text-accent text-sm font-semibold mb-1">👉 Next Step</p>
                            <h3 className="text-white text-xl sm:text-2xl font-bold mb-1">
                                {nextStep.label}
                            </h3>
                            <p className="text-gray-300 text-sm sm:text-base">
                                {nextStep.description}
                            </p>
                        </div>
                    </div>

                    {/* Right Side - Action Button */}
                    <button
                        onClick={() => navigate(nextStep.path)}
                        className={`
                            group px-6 py-3 sm:px-8 sm:py-4 
                            bg-gradient-to-r ${nextStep.color}
                            hover:shadow-2xl hover:shadow-accent/30
                            text-white font-bold rounded-xl
                            transition-all duration-300
                            hover:-translate-y-1 hover:scale-105
                            flex items-center gap-3
                            whitespace-nowrap
                        `}
                    >
                        <span>{nextStep.actionText}</span>
                        <FaArrowRight className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NextStepCard;
