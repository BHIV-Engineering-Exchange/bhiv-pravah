import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { schoolAdminAPI } from '../../services/api';

const SchoolAdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getDashboardStats();
      setStats(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard statistics. Please try again.';
      setError(`Failed to load dashboard statistics: ${errorMessage}`);
      console.error('Error fetching stats:', err);
      console.error('Error response:', err.response);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <div className="stat-card" style={{ '--stat-color': color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</p>
          <p className="text-2xl md:text-3xl font-bold text-white mt-1 md:mt-2">{value}</p>
        </div>
        <div className="text-3xl md:text-4xl opacity-30" style={{ color }}>
          {icon}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="heading-serif text-3xl">School Admin Dashboard</h1>
        <p className="text-gray-400 mt-2">Overview of your school management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard title="Total Teachers" value={stats?.total_teachers || 0} icon="👨‍🏫" color="#6C63FF" />
        <StatCard title="Total Students" value={stats?.total_students || 0} icon="👨‍🎓" color="#06D6A0" />
        <StatCard title="Total Parents" value={stats?.total_parents || 0} icon="👨‍👩‍👧" color="#FFD93D" />
        <StatCard title="Total Classes" value={stats?.total_classes || 0} icon="📚" color="#A7F305" />
        <StatCard title="Total Lessons" value={stats?.total_lessons || 0} icon="📖" color="#FF6B9D" />
        <StatCard title="Today's Classes" value={stats?.todays_classes || 0} icon="📅" color="#06D6A0" />
        <StatCard title="Upcoming Holidays" value={stats?.upcoming_holidays || 0} icon="🎉" color="#FFD93D" />
        <StatCard title="Upcoming Events" value={stats?.upcoming_events || 0} icon="📢" color="#6C63FF" />
      </div>

      {/* Quick Actions */}
      <div className="card-dark p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/dashboard/teachers"
            className="p-4 border border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 block group"
          >
            <div className="text-2xl mb-2">👨‍🏫</div>
            <div className="font-semibold text-white group-hover:text-accent-green transition-colors">Manage Teachers</div>
            <div className="text-sm text-gray-500">Add or upload teachers</div>
          </Link>
          <Link
            to="/dashboard/students"
            className="p-4 border border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 block group"
          >
            <div className="text-2xl mb-2">👨‍🎓</div>
            <div className="font-semibold text-white group-hover:text-accent-green transition-colors">Manage Students</div>
            <div className="text-sm text-gray-500">Add or upload students</div>
          </Link>
          <Link
            to="/dashboard/parents"
            className="p-4 border border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 block group"
          >
            <div className="text-2xl mb-2">👨‍👩‍👧</div>
            <div className="font-semibold text-white group-hover:text-accent-green transition-colors">Manage Parents</div>
            <div className="text-sm text-gray-500">Add or upload parents</div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SchoolAdminDashboard;
