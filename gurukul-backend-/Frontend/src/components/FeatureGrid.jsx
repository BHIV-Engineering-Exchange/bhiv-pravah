import React from 'react';
import { Link } from 'react-router-dom';
import { FaThLarge, FaBookOpen, FaFileAlt, FaComments, FaClipboardList, FaVideo } from 'react-icons/fa';

const features = [
    { icon: FaThLarge, label: "Dashboard", path: "/dashboard" },
    { icon: FaBookOpen, label: "Subjects", path: "/subjects" },
    // { icon: FaFileAlt, label: "Summarizer", path: "/summarizer" }, // PDF summarizer commented out
    { icon: FaComments, label: "Chatbot", path: "/chatbot" },
    { icon: FaClipboardList, label: "Test", path: "/test" },
    { icon: FaVideo, label: "Lectures", path: "/lectures" },
];

const FeatureGrid = () => {
    return (
        <div className="max-w-6xl mx-auto px-2 sm:px-4 md:px-6 w-full">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6 lg:gap-8">
                {features.map((feature, index) => (
                    <Link
                        key={index}
                        to={feature.path}
                        className="group relative overflow-hidden rounded-2xl p-4 sm:p-6 md:p-8 transition-all duration-500 hover:-translate-y-2 block text-center w-full"
                    >
                        {/* Glass Background - darker tint */}
                        <div className="absolute inset-0 bg-black/60 backdrop-blur-xl border border-white/5 transition-all duration-500 group-hover:bg-black/70 group-hover:border-accent/20 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)]"></div>

                        {/* Hover Glow */}
                        <div className="absolute -inset-1 bg-gradient-to-r from-accent/0 via-accent/10 to-accent/0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 blur-xl"></div>

                        <div className="relative z-10 flex flex-col items-center justify-center gap-3 sm:gap-4 text-white">
                            <div className="p-3 sm:p-4 rounded-full bg-black/40 border border-white/5 group-hover:scale-110 transition-transform duration-500 group-hover:border-accent/30 group-hover:bg-accent/10">
                                <feature.icon className="text-2xl sm:text-3xl text-gray-100 group-hover:text-accent transition-colors duration-300" />
                            </div>
                            <span className="text-lg sm:text-xl font-medium tracking-wide text-gray-50 group-hover:text-white transition-colors">{feature.label}</span>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
};

export default FeatureGrid;
