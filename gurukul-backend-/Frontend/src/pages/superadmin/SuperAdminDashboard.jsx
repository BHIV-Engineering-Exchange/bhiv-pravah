
import React, { useState, useEffect } from 'react';
import SuperAdminSidebar from '../../components/SuperAdminSidebar';
import { FaGlobe, FaUniversity, FaUsers, FaServer, FaShieldAlt } from 'react-icons/fa';
import SchoolManagement from './SchoolManagement';
import InfrastructureOverview from './InfrastructureOverview';
import PlatformAnalytics from './PlatformAnalytics'; // We can reuse logic from ReportsAnalytics
import UserManagement from '../admin/UserManagement'; // Reuse standard user management for now

const SuperAdminDashboard = () => {
    const [activeSection, setActiveSection] = useState('overview');

    useEffect(() => {
        const updateActiveSection = () => {
            const hash = window.location.hash.replace('#', '');
            if (hash && ['overview', 'schools', 'users', 'health'].includes(hash)) {
                setActiveSection(hash);
            } else {
                setActiveSection('overview');
            }
        };
        updateActiveSection();
        window.addEventListener('hashchange', updateActiveSection);
        return () => window.removeEventListener('hashchange', updateActiveSection);
    }, []);

    const renderContent = () => {
        switch (activeSection) {
            case 'schools':
                return <SchoolManagement />;
            case 'users':
                return (
                    <div className="space-y-6">
                        <div className="bg-orange-500/10 border border-orange-500/30 p-4 rounded-xl mb-4">
                            <h4 className="text-orange-400 font-bold flex items-center gap-2">
                                <FaShieldAlt /> Global User Control
                            </h4>
                            <p className="text-gray-400 text-xs">You are viewing users across all schools. Be careful with administrative changes.</p>
                        </div>
                        <UserManagement />
                    </div>
                );
            case 'health':
                return <InfrastructureOverview />;
            case 'overview':
            default:
                return <PlatformAnalytics />;
        }
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <SuperAdminSidebar />
            <main className="flex-grow animate-fade-in-up">
                <div className="mb-6 sm:mb-8 bg-gradient-to-r from-orange-600/20 to-transparent p-6 rounded-2xl border-l-4 border-orange-500">
                    <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white tracking-tight flex items-center gap-3">
                        <FaGlobe className="text-orange-500 animate-pulse" />
                        Platform Control Center
                    </h2>
                    <p className="text-gray-300 text-xs sm:text-sm font-medium mt-1">
                        Global oversight of Gurukul Schools and Infrastructure
                    </p>
                </div>

                <div className="mb-6">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
};

export default SuperAdminDashboard;
