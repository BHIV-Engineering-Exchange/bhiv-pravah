import React, { useState, useEffect } from 'react';
import { parentAPI } from '../../services/api';

const MyAnnouncements = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const fetchAnnouncements = async () => {
    try {
      setLoading(true);
      const data = await parentAPI.getMyAnnouncements();
      setAnnouncements(data || []);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load announcements. Please try again.';
      setError(`Failed to load announcements: ${errorMessage}`);
      console.error('Error fetching announcements:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAudienceBadgeColor = (audience) => {
    switch (audience) {
      case 'PARENTS':
        return 'bg-accent-blue/15 text-accent-blue';
      case 'EVERYONE':
        return 'bg-accent-pink/15 text-accent-pink';
      default:
        return 'bg-[#16162A] text-white';
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading announcements...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
        <button
          onClick={fetchAnnouncements}
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
        <div>
          <h1 className="text-3xl font-bold text-white">Announcements</h1>
          <p className="text-gray-400 mt-2">View school announcements for parents</p>
        </div>
        <button
          onClick={fetchAnnouncements}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {announcements.length === 0 ? (
        <div className="card-dark p-8 text-center">
          <div className="text-6xl mb-4">📢</div>
          <h2 className="text-2xl font-semibold text-white mb-2">No Announcements</h2>
          <p className="text-gray-400">There are no announcements at this time.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map((announcement) => (
            <div key={announcement.id} className="card-dark p-6 border border-[#2A2A3E] hover:shadow-lg transition">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-white">{announcement.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAudienceBadgeColor(announcement.target_audience)}`}>
                      {announcement.target_audience}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    Published: {formatDate(announcement.published_at)}
                    {announcement.created_by_name && ` • By ${announcement.created_by_name}`}
                  </p>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-[#2A2A3E]">
                <p className="text-gray-300 whitespace-pre-wrap">{announcement.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyAnnouncements;

