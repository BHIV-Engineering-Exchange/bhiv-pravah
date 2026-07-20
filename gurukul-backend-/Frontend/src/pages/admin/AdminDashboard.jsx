import React, { useState } from 'react';
import AdminSidebar from '../../components/AdminSidebar';
import { FaUsers, FaChartLine, FaCog, FaServer } from 'react-icons/fa';
import { useAuth } from '../../contexts/AuthContext';
import UserManagement from './UserManagement';
import SystemOverview from './SystemOverview';
import ReportsAnalytics from './ReportsAnalytics';
import AdminSettings from './AdminSettings';
import MduRegistry from './MduRegistry';
import GurukulDrishti from './GurukulDrishti';

const AdminDashboard = () => {
    const { user } = useAuth();
    const [activeSection, setActiveSection] = useState('overview'); // overview, users, reports, settings

    // Determine active section from hash or default
    React.useEffect(() => {
        const updateActiveSection = () => {
            const hash = window.location.hash.replace('#', '');
            if (hash && ['overview', 'users', 'reports', 'settings', 'mdu_registry', 'drishti'].includes(hash)) {
                setActiveSection(hash);
            } else {
                // Default to overview if no hash or invalid hash
                setActiveSection('overview');
            }
        };
        
        // Set initial section
        updateActiveSection();
        
        // Listen for hash changes
        const handleHashChange = () => {
            updateActiveSection();
        };
        
        window.addEventListener('hashchange', handleHashChange);
        // Also listen for popstate (browser back/forward)
        window.addEventListener('popstate', handleHashChange);
        
        return () => {
            window.removeEventListener('hashchange', handleHashChange);
            window.removeEventListener('popstate', handleHashChange);
        };
    }, []);

    const renderContent = () => {
        switch (activeSection) {
            case 'users':
                return <UserManagement />;
            case 'overview':
            default:
                return <SystemOverview />;
            case 'reports':
                return <ReportsAnalytics />;
            case 'settings':
                return <AdminSettings />;
            case 'mdu_registry':
                return <MduRegistry />;
            case 'drishti':
                return <GurukulDrishti />;
        }
    };

    // Debug: Log active section
    React.useEffect(() => {
        console.log('AdminDashboard activeSection:', activeSection);
    }, [activeSection]);

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <AdminSidebar />
            <main className="flex-grow animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div className="mb-6 sm:mb-8">
                    <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white">Administrator Dashboard</h2>
                    <p className="text-gray-200 text-xs sm:text-sm font-medium">
                        Platform oversight and management
                    </p>
                </div>

                {/* Content Section */}
                <div className="mb-6">
                    {renderContent()}
                </div>
            </main>
        </div>
    );
};

export default AdminDashboard;

