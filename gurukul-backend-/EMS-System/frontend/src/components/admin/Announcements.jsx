import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const Announcements = () => {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [targetAudience, setTargetAudience] = useState('');
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    target_audience: 'EVERYONE',
  });

  const audienceOptions = [
    { value: 'TEACHERS', label: 'Teachers' },
    { value: 'STUDENTS', label: 'Students' },
    { value: 'PARENTS', label: 'Parents' },
    { value: 'EVERYONE', label: 'Everyone' },
  ];

  useEffect(() => {
    fetchAnnouncements();
  }, [targetAudience]);

  const fetchAnnouncements = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getAnnouncements(targetAudience || null);
      setAnnouncements(data);
      setError('');
    } catch (err) {
      console.error('Error fetching announcements:', err);
      setError('Failed to load announcements. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAnnouncement = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createAnnouncement(formData);
      setShowCreateForm(false);
      setEditingAnnouncement(null);
      setFormData({
        title: '',
        content: '',
        target_audience: 'EVERYONE',
      });
      fetchAnnouncements();
      alert('Announcement created successfully!');
    } catch (err) {
      console.error('Error creating announcement:', err);
      alert(err.response?.data?.detail || 'Failed to create announcement');
    }
  };

  const handleEditAnnouncement = (announcement) => {
    setEditingAnnouncement(announcement);
    setFormData({
      title: announcement.title,
      content: announcement.content,
      target_audience: announcement.target_audience,
    });
    setShowCreateForm(true);
  };

  const handleUpdateAnnouncement = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateAnnouncement(editingAnnouncement.id, formData);
      setShowCreateForm(false);
      setEditingAnnouncement(null);
      setFormData({
        title: '',
        content: '',
        target_audience: 'EVERYONE',
      });
      fetchAnnouncements();
      alert('Announcement updated successfully!');
    } catch (err) {
      console.error('Error updating announcement:', err);
      alert(err.response?.data?.detail || 'Failed to update announcement');
    }
  };

  const handleDeleteAnnouncement = async (id) => {
    if (!window.confirm('Are you sure you want to delete this announcement?')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteAnnouncement(id);
      fetchAnnouncements();
      alert('Announcement deleted successfully!');
    } catch (err) {
      console.error('Error deleting announcement:', err);
      alert(err.response?.data?.detail || 'Failed to delete announcement');
    }
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingAnnouncement(null);
    setFormData({
      title: '',
      content: '',
      target_audience: 'EVERYONE',
    });
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
          <h1 className="text-3xl font-bold text-white">Announcements & Notices</h1>
          <p className="text-gray-400 mt-2">
            Create announcements targeted to teachers, students, parents, or everyone
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
        >
          ➕ New Announcement
        </button>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Filter */}
      <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Filter by Audience
          </label>
          <select
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
          >
            <option value="">All</option>
            {audienceOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingAnnouncement ? 'Edit Announcement' : 'Create Announcement'}
          </h2>
          <form onSubmit={editingAnnouncement ? handleUpdateAnnouncement : handleCreateAnnouncement} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Title *</label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                Target Audience *
              </label>
              <select
                value={formData.target_audience}
                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              >
                {audienceOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Content *</label>
              <textarea
                required
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                rows={4}
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingAnnouncement ? 'Update' : 'Publish'}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Announcements List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">
            Announcements ({announcements.length})
          </h2>
        </div>
        <div className="divide-y divide-[#2A2A3E]">
          {announcements.length === 0 ? (
            <div className="px-6 py-4 text-center text-gray-500">No announcements yet</div>
          ) : (
            announcements.map((a) => (
              <div key={a.id} className="px-6 py-4 hover:bg-[#16162A]">
                <div className="flex justify-between items-start mb-1">
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <h3 className="text-lg font-semibold text-white">{a.title}</h3>
                      <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 text-indigo-700">
                        {a.target_audience}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-2">{a.content}</p>
                    <p className="text-xs text-gray-400">
                      Published: {formatDateTime(a.published_at)} | By User ID: {a.created_by}
                    </p>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleEditAnnouncement(a)}
                      className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                      title="Edit"
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDeleteAnnouncement(a.id)}
                      className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition"
                      title="Delete"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Announcements;

