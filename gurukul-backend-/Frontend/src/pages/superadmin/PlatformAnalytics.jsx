
import React, { useState, useEffect } from 'react';
import { FaChartLine, FaUsers, FaUniversity, FaUserGraduate, FaChalkboardTeacher, FaArrowUp, FaCalendarAlt } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';

const PlatformAnalytics = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const data = await apiGet('/api/v1/ems/admin/stats');
                setStats(data);
            } catch (error) {
                console.error('Failed to fetch platform stats:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    const StatBox = ({ title, value, icon: Icon, color, trend }) => (
        <div className="bg-black/40 border border-white/10 rounded-2xl p-6 hover:border-white/20 transition-all">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${color} bg-opacity-20`}>
                    <Icon className={color} size={24} />
                </div>
                {trend && (
                    <div className="flex items-center gap-1 text-green-400 text-xs font-bold">
                        <FaArrowUp /> {trend}
                    </div>
                )}
            </div>
            <div className="text-3xl font-bold text-white mb-1">{value}</div>
            <div className="text-gray-500 text-xs uppercase tracking-widest font-semibold">{title}</div>
        </div>
    );

    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-pulse text-white">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white/5 h-32 rounded-2xl border border-white/10"></div>
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Global Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatBox 
                    title="Total Enrollment" 
                    value={stats?.totalUsers || 0} 
                    icon={FaUsers} 
                    color="text-blue-400" 
                    trend="12%"
                />
                <StatBox 
                    title="Active Students" 
                    value={stats?.totalStudents || 0} 
                    icon={FaUserGraduate} 
                    color="text-green-400" 
                    trend="5%"
                />
                <StatBox 
                    title="Verified Teachers" 
                    value={stats?.totalTeachers || 0} 
                    icon={FaChalkboardTeacher} 
                    color="text-purple-400" 
                />
                <StatBox 
                    title="System Health" 
                    value="99.9%" 
                    icon={FaChartLine} 
                    color="text-orange-400" 
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Activity Graph Placeholder */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/60 min-h-[300px] flex flex-col justify-between">
                    <div>
                        <h4 className="text-white font-bold mb-1 flex items-center gap-2">
                            <FaCalendarAlt className="text-orange-500" />
                            Global Enrollment Trend
                        </h4>
                        <p className="text-gray-500 text-[10px] mb-6">User growth across all school shards in the last 30 days.</p>
                    </div>
                    <div className="flex-grow flex items-end justify-between gap-2 px-2 pb-2">
                        {[40, 65, 45, 80, 55, 90, 70, 85, 60, 100].map((h, i) => (
                            <div key={i} className="w-full bg-gradient-to-t from-orange-600 to-amber-500 rounded-t-sm transition-all hover:brightness-125 cursor-help" style={{height: `${h}%`}}></div>
                        ))}
                    </div>
                </div>

                {/* Role Distribution */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/60 min-h-[300px]">
                    <h4 className="text-white font-bold mb-6 flex items-center gap-2">
                        <FaUsers className="text-orange-500" />
                        Role Distribution
                    </h4>
                    <div className="space-y-5">
                        {[
                            { label: 'Students', count: stats?.totalStudents || 0, color: 'bg-green-500' },
                            { label: 'Teachers', count: stats?.totalTeachers || 0, color: 'bg-purple-500' },
                            { label: 'Parents', count: stats?.totalParents || 0, color: 'bg-orange-500' },
                            { label: 'Admins', count: (stats?.totalUsers || 0) - (stats?.totalStudents || 0) - (stats?.totalTeachers || 0) - (stats?.totalParents || 0), color: 'bg-red-500' },
                        ].map((role, idx) => {
                            const total = stats?.totalUsers || 1;
                            const pct = Math.round((role.count / total) * 100);
                            return (
                                <div key={idx} className="space-y-1">
                                    <div className="flex justify-between items-center text-xs">
                                        <span className="text-gray-400 font-bold">{role.label}</span>
                                        <span className="text-white font-mono">{role.count} ({pct}%)</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full ${role.color} transition-all duration-1000`} style={{width: `${pct}%`}}></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PlatformAnalytics;
