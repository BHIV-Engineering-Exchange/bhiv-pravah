import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import emsApi from '../../services/emsApi';
import { handleApiError } from '../../utils/apiClient';
import Sidebar from '../../components/Sidebar';
import { FaChalkboardTeacher, FaSpinner, FaRedo, FaBookOpen, FaEnvelope } from 'react-icons/fa';
import EMSAuthentication from '../../components/EMSAuthentication';

const MyTeachers = () => {
    const { user } = useAuth();
    const [teachers, setTeachers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [emsToken, setEmsToken] = useState(null);
    const [showAuth, setShowAuth] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('ems_token');
        if (token) {
            setEmsToken(token);
            fetchTeachers(token);
        } else {
            setShowAuth(true);
            setLoading(false);
        }
    }, []);

    const handleAuthSuccess = (token) => {
        setEmsToken(token);
        setShowAuth(false);
        fetchTeachers(token);
    };

    const fetchTeachers = async (token) => {
        try {
            setLoading(true);
            setError('');
            const data = await emsApi.getTeachers(token);
            setTeachers(data || []);
        } catch (err) {
            const errorInfo = handleApiError(err, { context: 'Loading teachers' });
            setError(errorInfo.message || 'Failed to load teachers');
            console.error('Error fetching teachers:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = () => {
        if (emsToken) {
            fetchTeachers(emsToken);
        }
    };

    if (showAuth) {
        return <EMSAuthentication onSuccess={handleAuthSuccess} onCancel={() => setShowAuth(false)} />;
    }

    if (loading) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-center">
                    <div className="text-center">
                        <FaSpinner className="animate-spin text-4xl text-orange-400 mx-auto mb-4" />
                        <p className="text-gray-300 text-lg">Loading your teachers...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !teachers.length) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-start pt-8">
                    <div className="w-full max-w-4xl mx-auto">
                        <div className="glass-panel border border-red-500/30 bg-red-500/10 p-6 rounded-2xl">
                            <p className="text-red-300 text-center mb-4">{error}</p>
                            {emsToken && (
                                <button
                                    onClick={handleRefresh}
                                    className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors font-medium"
                                >
                                    Retry
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
            <Sidebar />
            <div className="flex-grow">
            <div className="w-full max-w-7xl mx-auto">
                <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white flex items-center gap-3">
                            <FaChalkboardTeacher className="text-orange-400" />
                            My Teachers
                        </h2>
                        <p className="text-gray-200 text-xs sm:text-sm font-medium mt-2">
                            View all teachers connected to your enrolled classes
                        </p>
                    </div>
                    {emsToken && (
                        <button
                            onClick={handleRefresh}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white rounded-xl font-medium shadow-lg transition-transform hover:-translate-y-1"
                        >
                            <FaRedo className="text-sm" />
                            <span>Refresh</span>
                        </button>
                    )}
                </div>

                {error && (
                    <div className="mb-6 glass-panel border border-red-500/30 bg-red-500/10 p-4 rounded-xl">
                        <p className="text-red-300 text-sm">{error}</p>
                    </div>
                )}

                {teachers.length === 0 ? (
                    <div className="glass-panel p-8 sm:p-12 text-center border border-white/10 rounded-2xl">
                        <FaChalkboardTeacher className="text-6xl text-gray-400 mx-auto mb-4 opacity-50" />
                        <h3 className="text-xl font-semibold text-white mb-2">No Teachers Found</h3>
                        <p className="text-gray-300">You are not enrolled in any classes yet.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                        {teachers.map((teacher) => (
                            <div
                                key={teacher.id}
                                className="glass-panel p-6 border border-white/10 hover:border-orange-500/50 transition-all rounded-2xl hover:shadow-xl hover:-translate-y-1 bg-black/40"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-bold text-white mb-1">{teacher.name}</h3>
                                        <div className="flex items-center gap-2 text-sm text-gray-300 mt-2">
                                            <FaEnvelope className="text-orange-400 text-xs" />
                                            <span className="break-all">{teacher.email}</span>
                                        </div>
                                    </div>
                                    <div className="text-3xl opacity-60">
                                        <FaChalkboardTeacher className="text-orange-400" />
                                    </div>
                                </div>

                                {teacher.classes && teacher.classes.length > 0 && (
                                    <div className="pt-4 border-t border-white/10">
                                        <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                                            <FaBookOpen className="text-orange-400" />
                                            Classes ({teacher.classes.length})
                                        </h4>
                                        <div className="space-y-2">
                                            {teacher.classes.map((cls) => (
                                                <div
                                                    key={cls.id}
                                                    className="px-3 py-2 bg-white/5 rounded-lg border border-white/10"
                                                >
                                                    <p className="text-sm font-medium text-white">{cls.name}</p>
                                                    <p className="text-xs text-gray-400 mt-1">
                                                        {cls.subject_name || 'No subject'}
                                                        {cls.grade && ` • Grade ${cls.grade}`}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
            </div>
        </div>
    );
};

export default MyTeachers;

