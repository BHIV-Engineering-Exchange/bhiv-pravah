import React, { useState, useEffect } from 'react';
import { parentAPI } from '../../services/api';

const ParentDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await parentAPI.getDashboardStats();
      setStats(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard statistics. Please try again.';
      setError(`Failed to load dashboard statistics: ${errorMessage}`);
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <div className="stat-card" style={{ borderLeftColor: color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs md:text-sm font-medium text-gray-400">{title}</p>
          <p className="text-2xl md:text-3xl font-bold text-white mt-1 md:mt-2">{value}</p>
        </div>
        <div className="text-3xl md:text-4xl opacity-20" style={{ color }}>
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
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
        <button
          onClick={fetchStats}
          className="mt-4 px-4 py-2 bg-red-600/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-600/30 transition text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Parent Dashboard</h1>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="My Children"
          value={stats?.total_children || 0}
          icon="👨‍👩‍👧"
          color="#4F46E5"
        />
        <StatCard
          title="Total Classes"
          value={stats?.total_classes || 0}
          icon="📚"
          color="#10B981"
        />
        <StatCard
          title="Total Lessons"
          value={stats?.total_lessons || 0}
          icon="📖"
          color="#F59E0B"
        />
        <StatCard
          title="Recent Announcements"
          value={stats?.recent_announcements || 0}
          icon="📢"
          color="#EF4444"
        />
      </div>

      {/* Quick Actions */}
      <div className="card-dark p-4 md:p-6">
        <h2 className="text-lg md:text-xl font-semibold text-white mb-3 md:mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
          <button
            onClick={() => window.location.hash = '#/dashboard/children'}
            className="p-3 md:p-4 border-2 border-gray-200 rounded-lg hover:border-accent-green hover:bg-indigo-50 transition text-left"
          >
            <div className="text-xl md:text-2xl mb-1 md:mb-2">👨‍👩‍👧</div>
            <div className="font-medium text-white text-sm md:text-base">My Children</div>
            <div className="text-xs md:text-sm text-gray-400 mt-1 hidden sm:block">View your children's information</div>
          </button>
          <button
            onClick={() => window.location.hash = '#/dashboard/attendance'}
            className="p-3 md:p-4 border-2 border-gray-200 rounded-lg hover:border-accent-green hover:bg-indigo-50 transition text-left"
          >
            <div className="text-xl md:text-2xl mb-1 md:mb-2">✅</div>
            <div className="font-medium text-white text-sm md:text-base">View Attendance</div>
            <div className="text-xs md:text-sm text-gray-400 mt-1 hidden sm:block">Check attendance records</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ParentDashboard;

