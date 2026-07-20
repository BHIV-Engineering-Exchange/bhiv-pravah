import React, { createContext, useState, useContext, useEffect } from 'react';
import { DEMO_TENANT_ID } from '../config';

const DemoContext = createContext();

export const useDemo = () => {
    return useContext(DemoContext);
};

export const DemoProvider = ({ children }) => {
    const [isDemoMode, setIsDemoMode] = useState(() => {
        const saved = localStorage.getItem('gurukul_demo_mode');
        return saved === 'true';
    });

    useEffect(() => {
        localStorage.setItem('gurukul_demo_mode', isDemoMode);

        // Auto-set the Demo Tenant ID when demo mode is active
        // This ensures the backend routes requests to the Demo Database
        if (isDemoMode) {
            localStorage.setItem('gurukul_tenant_id', DEMO_TENANT_ID);
        } else {
            // Optional: reset to a default institution if needed, 
            // but usually we just want it removed so main flows work
            localStorage.removeItem('gurukul_tenant_id');
        }
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
