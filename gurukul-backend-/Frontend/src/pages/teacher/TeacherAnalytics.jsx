import React, { useState, useEffect } from 'react';
import { FaChartLine, FaUsers, FaBookOpen, FaClipboardCheck } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const TeacherAnalytics = () => {
    const { alert } = useModal();
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/analytics').catch(() => null);
            setAnalytics(data);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch analytics' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading analytics...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaChartLine className="text-orange-400" />
                    Analytics & Reports
                </h3>
                <p className="text-gray-400 text-sm mt-1">View comprehensive class performance and learning metrics</p>
            </div>

            {analytics ? (
                <>
                    {/* Statistics Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="glass-panel p-6 rounded-2xl border border-white/10">
                            <div className="flex items-center justify-between mb-2">
                                <FaUsers className="text-blue-400 text-2xl" />
                            </div>
                            <div className="text-3xl font-bold text-white mb-1">{analytics.totalStudents || 0}</div>
                            <div className="text-sm text-gray-400">Total Students</div>
                        </div>
                        <div className="glass-panel p-6 rounded-2xl border border-white/10">
                            <div className="flex items-center justify-between mb-2">
                                <FaBookOpen className="text-green-400 text-2xl" />
                            </div>
                            <div className="text-3xl font-bold text-white mb-1">{analytics.totalTopics || 0}</div>
                            <div className="text-sm text-gray-400">Topics Covered</div>
                        </div>
                        <div className="glass-panel p-6 rounded-2xl border border-white/10">
                            <div className="flex items-center justify-between mb-2">
                                <FaClipboardCheck className="text-orange-400 text-2xl" />
                            </div>
                            <div className="text-3xl font-bold text-white mb-1">{analytics.completedAssignments || 0}</div>
                            <div className="text-sm text-gray-400">Completed Tasks</div>
                        </div>
                        <div className="glass-panel p-6 rounded-2xl border border-white/10">
                            <div className="flex items-center justify-between mb-2">
                                <FaChartLine className="text-purple-400 text-2xl" />
                            </div>
                            <div className="text-3xl font-bold text-white mb-1">{analytics.averageScore || 0}%</div>
                            <div className="text-sm text-gray-400">Average Score</div>
                        </div>
                    </div>

                    {/* Additional Analytics */}
                    <div className="glass-panel p-6 rounded-2xl border border-white/10">
                        <h4 className="text-lg font-semibold text-white mb-4">Performance Overview</h4>
                        <p className="text-gray-400 text-sm">Detailed charts and trends coming soon...</p>
                    </div>
                </>
            ) : (
                <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center text-gray-400">
                    No analytics data available yet
                </div>
            )}
        </div>
    );
};

export default TeacherAnalytics;

