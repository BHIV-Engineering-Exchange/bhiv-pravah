import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import emsApi from '../../services/emsApi';
import { handleApiError } from '../../utils/apiClient';
import Sidebar from '../../components/Sidebar';
import { FaBullhorn, FaRedo, FaSpinner, FaCalendarAlt } from 'react-icons/fa';
import EMSAuthentication from '../../components/EMSAuthentication';

const MyAnnouncements = () => {
    const { user } = useAuth();
    const [announcements, setAnnouncements] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [emsToken, setEmsToken] = useState(null);
    const [showAuth, setShowAuth] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('ems_token');
        if (token) {
            setEmsToken(token);
            fetchAnnouncements(token);
        } else {
            setShowAuth(true);
            setLoading(false);
        }
    }, []);

    const handleAuthSuccess = (token) => {
        setEmsToken(token);
        setShowAuth(false);
        fetchAnnouncements(token);
    };

    const fetchAnnouncements = async (token) => {
        try {
            setLoading(true);
            setError('');
            const data = await emsApi.getAnnouncements(token);
            setAnnouncements(data || []);
        } catch (err) {
            const errorInfo = handleApiError(err, { context: 'Loading announcements' });
            setError(errorInfo.message || 'Failed to load announcements');
            console.error('Error fetching announcements:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = () => {
        if (emsToken) {
            fetchAnnouncements(emsToken);
        }
    };

    const formatDateTime = (dt) => {
        if (!dt) return '-';
        try {
            const d = new Date(dt);
            return `${d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })} ${d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
        } catch {
            return dt;
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
                        <p className="text-gray-300 text-lg">Loading announcements...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !announcements.length) {
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
            <div className="w-full max-w-5xl mx-auto">
                <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white flex items-center gap-3">
                            <FaBullhorn className="text-orange-400" />
                            Announcements
                        </h2>
                        <p className="text-gray-200 text-xs sm:text-sm font-medium mt-2">
                            View announcements from school administration
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

                {announcements.length === 0 ? (
                    <div className="glass-panel p-8 sm:p-12 text-center border border-white/10 rounded-2xl">
                        <FaBullhorn className="text-6xl text-gray-400 mx-auto mb-4 opacity-50" />
                        <h3 className="text-xl font-semibold text-white mb-2">No Announcements</h3>
                        <p className="text-gray-300">No announcements available at this time.</p>
                    </div>
                ) : (
                    <div className="space-y-4 sm:space-y-6">
                        {announcements.map((announcement) => (
                            <div
                                key={announcement.id}
                                className="glass-panel p-6 border border-white/10 hover:border-orange-500/50 transition-all rounded-2xl hover:shadow-xl hover:-translate-y-1 bg-black/40"
                            >
                                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 gap-3">
                                    <h3 className="text-xl font-bold text-white">{announcement.title}</h3>
                                    <span className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full text-xs font-medium border border-orange-500/30">
                                        {announcement.target_audience || 'EVERYONE'}
                                    </span>
                                </div>
                                <p className="text-gray-300 mb-4 whitespace-pre-wrap leading-relaxed">
                                    {announcement.content}
                                </p>
                                <div className="flex items-center gap-2 text-xs text-gray-400 pt-3 border-t border-white/10">
                                    <FaCalendarAlt className="text-orange-400" />
                                    <span>Published: {formatDateTime(announcement.published_at)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
            </div>
        </div>
    );
};

export default MyAnnouncements;

