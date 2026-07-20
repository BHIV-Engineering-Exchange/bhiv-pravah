import React, { useState, useEffect } from 'react';
import { teacherAPI } from '../../services/api';

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
      const data = await teacherAPI.getMyAnnouncements();
      setAnnouncements(data);
      setError('');
    } catch (err) {
      setError('Failed to load announcements. Please try again.');
      console.error('Error fetching announcements:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dt) => {
    if (!dt) return '-';
    try {
      const d = new Date(dt);
      return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
    } catch {
      return dt;
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Announcements</h1>
          <p className="text-gray-400 mt-2">View announcements from school administration</p>
        </div>
        <button
          onClick={fetchAnnouncements}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {announcements.length === 0 ? (
        <div className="card-dark p-8 text-center">
          <p className="text-gray-400">No announcements available.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map((announcement) => (
            <div key={announcement.id} className="card-dark p-6 hover:shadow-lg transition">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-xl font-semibold text-white">{announcement.title}</h3>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-medium">
                  {announcement.target_audience}
                </span>
              </div>
              <p className="text-gray-400 mb-3 whitespace-pre-wrap">{announcement.content}</p>
              <p className="text-xs text-gray-400">
                Published: {formatDateTime(announcement.published_at)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyAnnouncements;

