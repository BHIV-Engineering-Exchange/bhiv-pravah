import React from 'react';
import Sidebar from '../../components/Sidebar';
import { FaUserGraduate, FaClock, FaChartLine, FaBookOpen, FaTrophy } from 'react-icons/fa';

const ParentDashboard = () => {
    // Mock data - would come from backend
    const childStats = {
        name: 'Arjun',
        studyTime: '12h 30m',
        topicsStudied: 8,
        quizzesCompleted: 15,
        averageScore: 82,
        learningStreak: 5
    };

    const recentActivity = [
        { action: 'Completed quiz on Algebra', score: '85%', time: '3 hours ago' },
        { action: 'Studied topic: Photosynthesis', subject: 'Biology', time: '1 day ago' },
        { action: 'Reviewed flashcards', count: 20, time: '2 days ago' }
    ];

    const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
        <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 relative overflow-hidden">
            <div className="flex items-center justify-between mb-4">
                <div className={`p-2 rounded-lg ${color} opacity-20`}>
                    <Icon className={`text-lg ${color.replace('bg-', 'text-')}`} />
                </div>
                <span className="text-xs text-gray-400">{title}</span>
            </div>
            <div className="text-2xl sm:text-3xl font-bold text-white mb-1 tabular-nums">{value}</div>
            {subtitle && <div className="text-xs text-gray-400">{subtitle}</div>}
        </div>
    );

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />
            <main className="flex-grow animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div className="mb-6 sm:mb-8">
                    <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white">Parent Dashboard</h2>
                    <p className="text-gray-200 text-xs sm:text-sm font-medium">
                        Monitor your child's learning journey
                    </p>
                </div>

                {/* Child Overview */}
                <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 mb-6">
                    <div className="flex items-center gap-3 mb-4">
                        <FaUserGraduate className="text-orange-400 text-xl" />
                        <h3 className="text-lg font-semibold text-white">{childStats.name}'s Progress</h3>
                    </div>
                    <p className="text-sm text-gray-400 mb-4">
                        Safe, read-only view of your child's learning activities and achievements.
                    </p>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <StatCard
                        icon={FaClock}
                        title="Study Time"
                        value={childStats.studyTime}
                        subtitle="This week"
                        color="bg-blue-500/20"
                    />
                    <StatCard
                        icon={FaBookOpen}
                        title="Topics Studied"
                        value={childStats.topicsStudied}
                        subtitle="This month"
                        color="bg-green-500/20"
                    />
                    <StatCard
                        icon={FaChartLine}
                        title="Average Score"
                        value={`${childStats.averageScore}%`}
                        subtitle="Overall performance"
                        color="bg-purple-500/20"
                    />
                    <StatCard
                        icon={FaTrophy}
                        title="Learning Streak"
                        value={`${childStats.learningStreak} days`}
                        subtitle="Keep it up!"
                        color="bg-orange-500/20"
                    />
                </div>

                {/* Recent Activity */}
                <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-white/10 mb-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <FaBookOpen className="text-orange-400" />
                        Recent Learning Activity
                    </h3>
                    <div className="space-y-3">
                        {recentActivity.map((activity, idx) => (
                            <div key={idx} className="p-3 bg-white/5 rounded-lg border border-white/5">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <span className="text-white text-sm">{activity.action}</span>
                                        {activity.score && (
                                            <span className="text-green-400 text-xs ml-2">({activity.score})</span>
                                        )}
                                    </div>
                                    <div className="text-xs text-gray-500">{activity.time}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Information */}
                <div className="glass-panel p-4 sm:p-6 rounded-2xl border border-orange-500/20 bg-orange-900/10">
                    <div className="flex items-start gap-3">
                        <FaBookOpen className="text-orange-400 mt-1" />
                        <div>
                            <h4 className="text-sm font-semibold text-white mb-2">About Parent View</h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                This dashboard provides a safe, read-only view of your child's learning progress. 
                                You can see their study time, completed activities, and achievements. 
                                For detailed reports or to communicate with teachers, please use the contact options.
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ParentDashboard;

