import React from 'react';
import Hero from '../components/Hero';
import FeatureGrid from '../components/FeatureGrid';

const Home = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] w-full px-2 sm:px-4">
            <Hero />
            <div className="mt-8 sm:mt-12 md:mt-16 w-full animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
                <FeatureGrid />
            </div>
        </div>
    );
};

export default Home;
