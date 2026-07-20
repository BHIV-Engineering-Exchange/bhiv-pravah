import React, { useState, useEffect } from 'react';
import { dashboardAPI } from '../services/api';

const DashboardOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await dashboardAPI.getStats();
      setStats(data);
      setError('');
    } catch (err) {
      setError('Failed to load statistics. Please try again.');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color }) => (
    <div className="stat-card" style={{ '--stat-color': color }}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
        </div>
        <div className="text-4xl opacity-30" style={{ color }}>
          {icon}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading statistics...</p>
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
      <div className="flex justify-between items-center">
        <h1 className="heading-serif text-3xl">Dashboard Overview</h1>
        <button
          onClick={fetchStats}
          className="btn-secondary text-sm"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <StatCard
          title="Total Schools"
          value={stats?.total_schools || 0}
          icon="🏫"
          color="#A7F305"
        />
        <StatCard
          title="Total Admins"
          value={stats?.total_admins || 0}
          icon="👥"
          color="#06D6A0"
        />
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon="👤"
          color="#FFD93D"
        />
        <StatCard
          title="Teachers"
          value={stats?.total_teachers || 0}
          icon="👨‍🏫"
          color="#6C63FF"
        />
        <StatCard
          title="Students"
          value={stats?.total_students || 0}
          icon="🎓"
          color="#FF6B9D"
        />
        <StatCard
          title="Parents"
          value={stats?.total_parents || 0}
          icon="👨‍👩‍👧"
          color="#06D6A0"
        />
      </div>

      {/* Quick Actions */}
      <div className="card-dark p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.hash = '#/dashboard/create-school'}
            className="p-4 border border-dashed border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 text-left group"
          >
            <div className="text-2xl mb-2">➕</div>
            <div className="font-medium text-white group-hover:text-accent-green transition-colors">Create School</div>
            <div className="text-sm text-gray-500">Add a new school</div>
          </button>
          <button
            onClick={() => window.location.hash = '#/dashboard/create-admin'}
            className="p-4 border border-dashed border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 text-left group"
          >
            <div className="text-2xl mb-2">👥</div>
            <div className="font-medium text-white group-hover:text-accent-green transition-colors">Create Admin</div>
            <div className="text-sm text-gray-500">Add a new admin</div>
          </button>
          <button
            onClick={() => window.location.hash = '#/dashboard/schools'}
            className="p-4 border border-dashed border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 text-left group"
          >
            <div className="text-2xl mb-2">🏫</div>
            <div className="font-medium text-white group-hover:text-accent-green transition-colors">View Schools</div>
            <div className="text-sm text-gray-500">Manage all schools</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
