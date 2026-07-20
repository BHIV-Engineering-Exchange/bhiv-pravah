import React, { createContext, useState, useContext, useEffect } from 'react';

const DemoContext = createContext();

export const useDemo = () => {
    const context = useContext(DemoContext);
    if (!context) {
        throw new Error('useDemo must be used within a DemoProvider');
    }
    return context;
};

export const DemoProvider = ({ children }) => {
    const [isDemoMode, setIsDemoMode] = useState(() => {
        const saved = localStorage.getItem('ems_demo_mode');
        return saved === 'true';
    });

    useEffect(() => {
        localStorage.setItem('ems_demo_mode', isDemoMode);
    }, [isDemoMode]);

    const toggleDemoMode = () => {
        setIsDemoMode(prev => !prev);
    };

    return (
        <DemoContext.Provider value={{ isDemoMode, toggleDemoMode }}>
            {children}
        </DemoContext.Provider>
    );
};
