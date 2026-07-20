import React from 'react';
import Sidebar from '../components/Sidebar';
import LearningFlow from '../components/LearningFlow';
import { FaCalculator, FaAtom, FaFlask, FaDna, FaLaptopCode, FaLandmark, FaGlobeAmericas, FaBook, FaChartLine } from 'react-icons/fa';

const Lectures = () => {
    const subjects = [
        { name: 'Mathematics', icon: <FaCalculator />, color: 'from-blue-500 to-cyan-500', search: 'Mathematics full course' },
        { name: 'Physics', icon: <FaAtom />, color: 'from-purple-500 to-pink-500', search: 'Physics lectures full course' },
        { name: 'Chemistry', icon: <FaFlask />, color: 'from-green-500 to-teal-500', search: 'Chemistry full course' },
        { name: 'Biology', icon: <FaDna />, color: 'from-red-500 to-orange-500', search: 'Biology lectures full education' },
        { name: 'Computer Science', icon: <FaLaptopCode />, color: 'from-gray-700 to-gray-900', search: 'Computer Science full course' },
        { name: 'History', icon: <FaLandmark />, color: 'from-amber-600 to-yellow-500', search: 'World History documentary full' },
        { name: 'Geography', icon: <FaGlobeAmericas />, color: 'from-emerald-600 to-green-400', search: 'Geography full course education' },
        { name: 'Literature', icon: <FaBook />, color: 'from-rose-500 to-pink-600', search: 'English Literature full course' },
        { name: 'Economics', icon: <FaChartLine />, color: 'from-indigo-600 to-blue-600', search: 'Economics full course' },
    ];

    const handleSubjectClick = (searchTerm) => {
        window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(searchTerm)}`, '_blank');
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Learning Flow - Guided Journey */}
                <div className="mb-4">
                    <LearningFlow currentStep="learn" />
                </div>

                <div className="flex-grow glass-panel no-hover p-4 sm:p-6 md:p-10 rounded-3xl border border-white/5 relative overflow-hidden flex flex-col items-start justify-start shadow-2xl min-h-[calc(100vh-80px)] sm:min-h-[calc(100vh-100px)]">

                    {/* Header */}
                    <div className="mb-6 sm:mb-10 w-full">
                        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold font-heading text-white mb-2">Video Lectures</h1>
                        <p className="text-base sm:text-lg text-gray-400 font-light">
                            Explore comprehensive video courses on popular subjects.
                        </p>
                    </div>

                    {/* Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 w-full">
                        {subjects.map((sub, idx) => (
                            <div
                                key={idx}
                                onClick={() => handleSubjectClick(sub.search)}
                                className="group relative h-48 rounded-2xl cursor-pointer overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl border border-white/5 bg-black/40"
                            >
                                {/* Gradient Background */}
                                <div className={`absolute inset-0 bg-gradient-to-br ${sub.color} opacity-10 group-hover:opacity-20 transition-opacity duration-300`}></div>

                                {/* Content */}
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-10 p-6">
                                    <div className="text-4xl text-white/80 group-hover:text-white transition-colors drop-shadow-lg">
                                        {sub.icon}
                                    </div>
                                    <h3 className="text-xl font-bold text-white tracking-wide">{sub.name}</h3>
                                </div>

                                {/* Hover Glow Effect */}
                                <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-white/10 rounded-full blur-3xl group-hover:bg-white/20 transition-all duration-500"></div>
                            </div>
                        ))}
                    </div>

                </div>
            </main>
        </div>
    );
};

export default Lectures;
