import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FaArrowRight, FaBookOpen, FaClipboardCheck, FaLightbulb, FaChartLine } from 'react-icons/fa';

/**
 * Learning Flow Component
 * Guides students through: Enter → Learn → Practice → Reflect → Improve
 * This replaces the fragmented menu approach with a structured learning journey
 */
const LearningFlow = ({ currentStep = null }) => {
    const navigate = useNavigate();

    const steps = [
        {
            id: 'enter',
            label: 'Subject Explorer',
            description: 'Choose your subject and topic',
            icon: FaBookOpen,
            path: '/subjects',
            color: 'from-blue-600/70 to-cyan-600/70' // Softer blue
        },
        {
            id: 'learn',
            label: 'Learn',
            description: 'Study lessons and watch videos',
            icon: FaBookOpen,
            path: '/lectures',
            color: 'from-purple-600/70 to-indigo-600/70' // Softer purple
        },
        {
            id: 'practice',
            label: 'Practice',
            description: 'Test your knowledge with quizzes',
            icon: FaClipboardCheck,
            path: '/test',
            color: 'from-emerald-600/70 to-teal-600/70' // Softer green
        },
        {
            id: 'reflect',
            label: 'Reflect',
            description: 'Review with flashcards',
            icon: FaLightbulb,
            path: '/flashcards',
            color: 'from-amber-600/70 to-yellow-600/70' // Softer amber
        },
        {
            id: 'improve',
            label: 'Improve',
            description: 'Track progress and continue',
            icon: FaChartLine,
            path: '/dashboard',
            color: 'from-slate-600/70 to-gray-600/70' // Calm gray
        }
    ];

    const handleStepClick = (step) => {
        navigate(step.path);
    };

    return (
        <div className="w-full max-w-6xl mx-auto px-4 py-6">
            <div className="mb-6 text-center">
                <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">
                    Your Learning Journey
                </h2>
                <p className="text-gray-300 text-sm sm:text-base">
                    Follow the path to structured learning
                </p>
            </div>

            <div className="relative">
                {/* Connection Line (Desktop) */}
                <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-blue-600/30 via-purple-600/30 via-emerald-600/30 via-amber-600/30 to-slate-600/30 opacity-20 -translate-y-1/2"></div>

                {/* Steps */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 relative z-10">
                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        const isActive = currentStep === step.id;
                        const isCompleted = currentStep && steps.findIndex(s => s.id === currentStep) > index;

                        return (
                            <button
                                key={step.id}
                                onClick={() => handleStepClick(step)}
                                className={`
                                    group relative p-4 sm:p-6 rounded-2xl 
                                    bg-black/40 backdrop-blur-sm border-2 
                                    transition-all duration-300
                                    ${isActive
                                        ? 'border-accent shadow-lg shadow-accent/30 scale-105'
                                        : 'border-white/10 hover:border-white/30 hover:scale-102'
                                    }
                                    ${isCompleted ? 'opacity-60' : 'opacity-100'}
                                `}
                            >
                                {/* Background Gradient */}
                                <div className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity`}></div>

                                {/* Content */}
                                <div className="relative z-10 flex flex-col items-center text-center gap-3">
                                    <div className={`
                                        w-12 h-12 sm:w-14 sm:h-14 rounded-full 
                                        flex items-center justify-center
                                        bg-gradient-to-br ${step.color}
                                        ${isActive ? 'ring-4 ring-accent/50' : ''}
                                        transition-all group-hover:scale-110
                                    `}>
                                        <Icon className="text-white text-lg sm:text-xl" />
                                    </div>

                                    <div>
                                        <h3 className="text-white font-bold text-sm sm:text-base mb-1">
                                            {step.label}
                                        </h3>
                                        <p className="text-gray-400 text-xs sm:text-sm">
                                            {step.description}
                                        </p>
                                    </div>

                                    {/* Step Number */}
                                    <div className={`
                                        absolute -top-2 -right-2 w-6 h-6 rounded-full
                                        flex items-center justify-center text-xs font-bold
                                        ${isActive || isCompleted
                                            ? 'bg-accent text-black'
                                            : 'bg-white/20 text-gray-400'
                                        }
                                    `}>
                                        {index + 1}
                                    </div>

                                    {/* Active Indicator */}
                                    {isActive && (
                                        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-12 h-1 bg-accent rounded-full"></div>
                                    )}
                                </div>

                                {/* Arrow (Mobile/Tablet) */}
                                {index < steps.length - 1 && (
                                    <div className="hidden sm:block lg:hidden absolute -right-2 top-1/2 -translate-y-1/2 z-20">
                                        <FaArrowRight className="text-gray-500 text-sm" />
                                    </div>
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Progress Indicator */}
            {currentStep && (
                <div className="mt-6 text-center">
                    <p className="text-gray-400 text-sm">
                        You are at: <span className="text-accent font-semibold">
                            {steps.find(s => s.id === currentStep)?.label || 'Getting Started'}
                        </span>
                    </p>
                </div>
            )}
        </div>
    );
};

export default LearningFlow;

