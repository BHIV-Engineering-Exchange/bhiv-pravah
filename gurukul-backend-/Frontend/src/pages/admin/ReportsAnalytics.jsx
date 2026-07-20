import React, { useState, useEffect } from 'react';
import { FaChartLine, FaUsers, FaBook, FaGraduationCap, FaFileAlt, FaLightbulb, FaCalendar, FaArrowUp, FaUserFriends } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const ReportsAnalytics = () => {
    const { alert } = useModal();
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('30d'); // 7d, 30d, all

    useEffect(() => {
        fetchAnalytics();
        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchAnalytics, 60000);
        return () => clearInterval(interval);
    }, [timeRange]);

    const fetchAnalytics = async () => {
        setLoading(true);
        try {
            // Check if user is authenticated
            const token = localStorage.getItem('auth_token');
            if (!token) {
                await alert('Please sign in to view analytics.', 'Authentication Required');
                setLoading(false);
                return;
            }
            
            console.log('Fetching analytics with token:', token ? 'Token exists' : 'No token');
            console.log('API Base URL:', import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:3000' : 'https://gurukul-up9j.onrender.com'));
            console.log('Full URL will be:', `${import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:3000' : 'https://gurukul-up9j.onrender.com')}/api/v1/ems/admin/analytics`);
            const data = await apiGet('/api/v1/ems/admin/analytics');
            setAnalytics(data);
        } catch (error) {
            console.error('Analytics fetch error:', error);
            console.error('Error status:', error.status);
            console.error('Error message:', error.message);
            const errorInfo = handleApiError(error, { operation: 'fetch analytics' });
            await alert(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const getRoleIcon = (role) => {
        switch (role) {
            case 'STUDENT': return <FaGraduationCap className="text-green-400" />;
            case 'TEACHER': return <FaUserFriends className="text-purple-400" />;
            case 'PARENT': return <FaUsers className="text-orange-400" />;
            case 'ADMIN': return <FaUsers className="text-red-400" />;
            default: return <FaUsers className="text-gray-400" />;
        }
    };

    const getMaxValue = (data, key) => {
        if (!data || data.length === 0) return 1;
        return Math.max(...data.map(item => item[key] || 0), 1);
    };

    const renderBarChart = (data, key, label, color) => {
        if (!data || data.length === 0) return <div className="text-gray-400 text-sm">No data available</div>;
        
        const maxValue = getMaxValue(data, key);
        
        return (
            <div className="space-y-2">
                {data.map((item, index) => {
                    const value = item[key] || 0;
                    const percentage = (value / maxValue) * 100;
                    return (
                        <div key={index} className="flex items-center gap-3">
                            <div className="text-xs text-gray-400 w-20 text-right">
                                {new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </div>
                            <div className="flex-1">
                                <div className="relative h-6 bg-black/40 rounded overflow-hidden">
                                    <div
                                        className={`h-full ${color} transition-all duration-500 flex items-center justify-end pr-2`}
                                        style={{ width: `${percentage}%` }}
                                    >
                                        {value > 0 && (
                                            <span className="text-xs font-semibold text-white">{value}</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    if (loading && !analytics) {
        return (
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <div className="flex flex-col items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mb-4"></div>
                    <p className="text-gray-400">Loading analytics data...</p>
                </div>
            </div>
        );
    }

    if (!analytics) {
        return (
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <p className="text-gray-400">No analytics data available.</p>
            </div>
        );
    }

    const { userStats, learningStats, dailyUserGrowth, dailyActivity, mostActiveUsers, roleDistribution } = analytics;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <div>
                        <h3 className="text-2xl font-bold text-white flex items-center gap-2 mb-2">
                            <FaChartLine className="text-orange-500" />
                            Reports & Analytics
                        </h3>
                        <p className="text-gray-400 text-sm">
                            Comprehensive insights into platform usage and user activity
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
                        >
                            <option value="7d">Last 7 Days</option>
                            <option value="30d">Last 30 Days</option>
                            <option value="all">All Time</option>
                        </select>
                        <button
                            onClick={fetchAnalytics}
                            className="px-4 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-white text-sm font-medium transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {/* User Statistics Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaUsers className="text-blue-400 text-xl" />
                            <FaArrowUp className="text-green-400 text-sm" />
                        </div>
                        <div className="text-2xl font-bold text-white">{userStats?.total || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Total Users</div>
                        <div className="text-xs text-green-400 mt-1">
                            +{userStats?.newUsers30d || 0} this month
                        </div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaUsers className="text-green-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{userStats?.active || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Active Users</div>
                        <div className="text-xs text-gray-500 mt-1">
                            {userStats?.total ? Math.round((userStats.active / userStats.total) * 100) : 0}% of total
                        </div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaGraduationCap className="text-purple-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{userStats?.students || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Students</div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaUserFriends className="text-orange-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{userStats?.teachers || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Teachers</div>
                    </div>
                </div>

                {/* Learning Statistics Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaFileAlt className="text-blue-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{learningStats?.totalSummaries || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Total Summaries</div>
                        <div className="text-xs text-green-400 mt-1">
                            +{learningStats?.summaries30d || 0} this month
                        </div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaLightbulb className="text-yellow-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{learningStats?.totalFlashcards || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Flashcards</div>
                        <div className="text-xs text-green-400 mt-1">
                            +{learningStats?.flashcards30d || 0} this month
                        </div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaBook className="text-pink-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{learningStats?.totalReflections || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Reflections</div>
                        <div className="text-xs text-green-400 mt-1">
                            +{learningStats?.reflections30d || 0} this month
                        </div>
                    </div>
                    <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <FaGraduationCap className="text-green-400 text-xl" />
                        </div>
                        <div className="text-2xl font-bold text-white">{learningStats?.completedMilestones || 0}</div>
                        <div className="text-xs text-gray-400 uppercase">Milestones</div>
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* User Growth Chart */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10">
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FaArrowUp className="text-orange-500" />
                        User Growth (Last 7 Days)
                    </h4>
                    {dailyUserGrowth && dailyUserGrowth.length > 0 ? (
                        renderBarChart(dailyUserGrowth, 'count', 'New Users', 'bg-gradient-to-r from-blue-500 to-blue-600')
                    ) : (
                        <div className="text-gray-400 text-sm py-8 text-center">No user growth data available</div>
                    )}
                </div>

                {/* Activity Chart */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10">
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FaCalendar className="text-orange-500" />
                        Daily Activity (Last 7 Days)
                    </h4>
                    {dailyActivity && dailyActivity.length > 0 ? (
                        <div className="space-y-4">
                            <div>
                                <div className="text-xs text-gray-400 mb-2">Summaries</div>
                                {renderBarChart(dailyActivity, 'summaries', 'Summaries', 'bg-gradient-to-r from-blue-500 to-blue-600')}
                            </div>
                            <div>
                                <div className="text-xs text-gray-400 mb-2">Flashcards</div>
                                {renderBarChart(dailyActivity, 'flashcards', 'Flashcards', 'bg-gradient-to-r from-yellow-500 to-yellow-600')}
                            </div>
                            <div>
                                <div className="text-xs text-gray-400 mb-2">Reflections</div>
                                {renderBarChart(dailyActivity, 'reflections', 'Reflections', 'bg-gradient-to-r from-pink-500 to-pink-600')}
                            </div>
                        </div>
                    ) : (
                        <div className="text-gray-400 text-sm py-8 text-center">No activity data available</div>
                    )}
                </div>
            </div>

            {/* Role Distribution & Most Active Users */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Role Distribution */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10">
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FaUsers className="text-orange-500" />
                        Role Distribution
                    </h4>
                    {roleDistribution && (
                        <div className="space-y-3">
                            {Object.entries(roleDistribution).map(([role, count]) => {
                                const total = Object.values(roleDistribution).reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
                                return (
                                    <div key={role} className="flex items-center gap-3">
                                        <div className="flex items-center gap-2 w-24">
                                            {getRoleIcon(role)}
                                            <span className="text-sm text-gray-300 capitalize">{role.toLowerCase()}</span>
                                        </div>
                                        <div className="flex-1">
                                            <div className="relative h-6 bg-black/40 rounded overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-orange-500 to-amber-600 transition-all duration-500 flex items-center justify-end pr-2"
                                                    style={{ width: `${percentage}%` }}
                                                >
                                                    {count > 0 && (
                                                        <span className="text-xs font-semibold text-white">{count}</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-sm text-gray-400 w-12 text-right">{percentage}%</div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Most Active Users */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10">
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <FaArrowUp className="text-orange-500" />
                        Most Active Users
                    </h4>
                    {mostActiveUsers && mostActiveUsers.length > 0 ? (
                        <div className="space-y-3">
                            {mostActiveUsers.map((user, index) => (
                                <div key={user.id} className="flex items-center justify-between p-3 bg-black/40 rounded-lg border border-white/10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-400 font-bold text-sm">
                                            {index + 1}
                                        </div>
                                        <div>
                                            <div className="text-white font-medium">{user.name}</div>
                                            <div className="text-xs text-gray-400">{user.email}</div>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            {getRoleIcon(user.role)}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-white font-bold">{user.totalActivity}</div>
                                        <div className="text-xs text-gray-400">
                                            {user.summaryCount} summaries, {user.flashcardCount} flashcards
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-gray-400 text-sm py-8 text-center">No active users data available</div>
                    )}
                </div>
            </div>

            {/* Last Updated */}
            {analytics.generatedAt && (
                <div className="text-center text-xs text-gray-500">
                    Last updated: {new Date(analytics.generatedAt).toLocaleString()}
                </div>
            )}
        </div>
    );
};

export default ReportsAnalytics;

