import React, { useState } from 'react';
import TeacherSidebar from '../../components/TeacherSidebar';
import { useAuth } from '../../contexts/AuthContext';
import MyStudents from './MyStudents';
import UploadContent from './UploadContent';
import StudentProgress from './StudentProgress';
import ClassManagement from './ClassManagement';
import TeacherAnalytics from './TeacherAnalytics';
import Assignments from './Assignments';
import Communication from './Communication';
import ContentLibrary from './ContentLibrary';
import TeacherSettings from './TeacherSettings';
import GurukulDrishti from '../admin/GurukulDrishti';

const TeacherDashboard = () => {
    const { user } = useAuth();
    const [activeSection, setActiveSection] = useState('drishti'); // default to drishti (Overview)

    // Determine active section from hash or default
    React.useEffect(() => {
        const updateActiveSection = () => {
            const hash = window.location.hash.replace('#', '');
            const validSections = ['drishti', 'students', 'upload', 'progress', 'classes', 'analytics', 'assignments', 'communication', 'library', 'settings'];
            if (hash && validSections.includes(hash)) {
                setActiveSection(hash);
            } else {
                // Default to drishti if no hash or invalid hash
                setActiveSection('drishti');
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
            case 'drishti':
                return <GurukulDrishti />;
            case 'students':
                return <MyStudents />;
            case 'upload':
                return <UploadContent />;
            case 'progress':
                return <StudentProgress />;
            case 'classes':
                return <ClassManagement />;
            case 'analytics':
                return <TeacherAnalytics />;
            case 'assignments':
                return <Assignments />;
            case 'communication':
                return <Communication />;
            case 'library':
                return <ContentLibrary />;
            case 'settings':
                return <TeacherSettings />;
            default:
                return <GurukulDrishti />;
        }
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <TeacherSidebar />
            <main className="flex-grow animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div className="mb-6 sm:mb-8">
                    <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white">Teacher Dashboard</h2>
                    <p className="text-gray-200 text-xs sm:text-sm font-medium">
                        Manage your classes and track student progress
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

export default TeacherDashboard;
