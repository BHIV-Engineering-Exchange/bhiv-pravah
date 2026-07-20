import React, { useState, useEffect } from 'react';
import { FaServer, FaDatabase, FaCheckCircle, FaExclamationTriangle, FaClock, FaChartBar } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const SystemOverview = () => {
    const { error: showError } = useModal();
    const [stats, setStats] = useState({
        totalUsers: 0,
        activeUsers: 0,
        totalTeachers: 0,
        totalStudents: 0,
        totalParents: 0,
        systemHealth: 'Checking...',
        apiStatus: 'Checking...'
    });
    const [loading, setLoading] = useState(true);
    const [activities, setActivities] = useState([]);
    const [lastChecked, setLastChecked] = useState(new Date());

    useEffect(() => {
        fetchSystemStats();
        const interval = setInterval(() => {
            fetchSystemStats();
            setLastChecked(new Date());
        }, 30000); // Refresh every 30 seconds

        return () => clearInterval(interval);
    }, []);

    const fetchSystemStats = async () => {
        try {
            const data = await apiGet('/api/v1/ems/admin/stats');
            setStats(data);
            setLoading(false);
        } catch (err) {
            const errorInfo = handleApiError(err, { operation: 'fetch system stats' });
            showError(errorInfo.message, errorInfo.title);
            setLoading(false);
        }
    };

    const getHealthColor = (status) => {
        if (status === 'Healthy' || status === 'Operational') return 'text-green-400 bg-green-500/20';
        if (status === 'Degraded' || status === 'Error') return 'text-red-400 bg-red-500/20';
        return 'text-yellow-400 bg-yellow-500/20';
    };

    const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 relative overflow-hidden group hover:border-orange-500/30 transition-all">
            <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg ${color} opacity-20 group-hover:opacity-30 transition-opacity`}>
                    <Icon className={`text-lg ${color.replace('bg-', 'text-')}`} />
                </div>
                <span className="text-xs text-gray-400 font-semibold uppercase tracking-wider">{title}</span>
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-white mb-1 tabular-nums">
                {loading ? '...' : value}
            </div>
            {subtitle && <div className="text-xs text-gray-400">{subtitle}</div>}
        </div>
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaServer className="text-orange-500" />
                    System Overview
                </h3>
                <div className="text-xs text-gray-400 flex items-center gap-2">
                    <FaClock className="text-xs" />
                    Last checked: {lastChecked.toLocaleTimeString()}
                </div>
            </div>

            {/* System Status */}
            <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10">
                <div className="flex items-center gap-3 mb-4">
                    <FaServer className="text-green-400 text-xl" />
                    <h4 className="text-lg font-semibold text-white">System Status</h4>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                        <div className="flex items-center gap-3">
                            <FaDatabase className="text-blue-400" />
                            <span className="text-sm text-gray-300">Backend API</span>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getHealthColor(stats.apiStatus)}`}>
                            {stats.apiStatus}
                        </span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                        <div className="flex items-center gap-3">
                            <FaCheckCircle className="text-green-400" />
                            <span className="text-sm text-gray-300">System Health</span>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getHealthColor(stats.systemHealth)}`}>
                            {stats.systemHealth}
                        </span>
                    </div>
                </div>
            </div>

            {/* User Statistics */}
            <div>
                    <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FaChartBar className="text-orange-400" />
                    User Statistics
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard
                        icon={FaChartBar}
                        title="Total Users"
                        value={stats.totalUsers}
                        subtitle={`${stats.activeUsers} active`}
                        color="bg-blue-500/20"
                    />
                    <StatCard
                        icon={FaChartBar}
                        title="Students"
                        value={stats.totalStudents}
                        subtitle="Active learners"
                        color="bg-green-500/20"
                    />
                    <StatCard
                        icon={FaChartBar}
                        title="Teachers"
                        value={stats.totalTeachers}
                        subtitle="Educators"
                        color="bg-purple-500/20"
                    />
                    <StatCard
                        icon={FaChartBar}
                        title="Parents"
                        value={stats.totalParents}
                        subtitle="Guardians"
                        color="bg-orange-500/20"
                    />
                </div>
            </div>

            {/* Recent Activities (Placeholder for now) */}
            <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FaChartBar className="text-orange-400" />
                    Recent Activities
                </h4>
                <div className="text-center py-8 text-gray-400 text-sm">
                    Activity feed coming soon...
                </div>
            </div>
        </div>
    );
};

export default SystemOverview;

