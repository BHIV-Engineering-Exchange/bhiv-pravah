import React from 'react';

const Hero = () => {
    return (
        <div className="flex flex-col items-center justify-center text-center mb-12 md:mb-16 pt-24 md:pt-32 px-4 animate-fade-in-up">
            <h1 className="text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold font-heading mb-4 md:mb-6 drop-shadow-2xl tracking-tighter text-white">
                Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-yellow-200">Gurukul</span>
            </h1>
            <p className="text-lg md:text-2xl text-gray-100 font-light max-w-3xl mx-auto leading-relaxed drop-shadow-lg opacity-90 tracking-wide">
                Your intelligent learning companion for <span className="italic font-heading">lifelong growth</span> and discovery.
            </p>
        </div>
    );
};

export default Hero;
