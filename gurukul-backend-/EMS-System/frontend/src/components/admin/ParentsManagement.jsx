import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const ParentsManagement = () => {
  const [parents, setParents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    student_email: ''
  });
  const [editingParent, setEditingParent] = useState(null);

  useEffect(() => {
    fetchParents();
  }, [searchTerm]);

  const fetchParents = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getParents(searchTerm || null);
      setParents(data);
      setError('');
    } catch (err) {
      setError('Failed to load parents. Please try again.');
      console.error('Error fetching parents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateParent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createParent(formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', student_email: '' });
      fetchParents();
      alert('Parent created successfully! Login credentials sent via email.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create parent');
    }
  };

  const handleEdit = (parent) => {
    setEditingParent(parent);
    setFormData({
      name: parent.name,
      email: parent.email,
      student_email: ''
    });
    setShowCreateForm(true);
  };

  const handleUpdateParent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateParent(editingParent.id, {
        name: formData.name,
        email: formData.email
      });
      setShowCreateForm(false);
      setEditingParent(null);
      setFormData({ name: '', email: '', student_email: '' });
      fetchParents();
      alert('Parent updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update parent');
    }
  };

  const handleDelete = async (parentId) => {
    if (!window.confirm('Are you sure you want to delete this parent? This action cannot be undone.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteParent(parentId);
      fetchParents();
      alert('Parent deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete parent');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading parents...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-xl md:text-3xl font-bold text-white">Parents Management</h1>
          <p className="text-sm md:text-base text-gray-400 mt-1 md:mt-2">Manage all parents in your school</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-3 md:px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm md:text-base whitespace-nowrap"
          >
            ➕ Add Parent
          </button>
        </div>
      </div>

      <div className="card-dark p-4">
        <input
          type="text"
          placeholder="Search parents by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
        />
      </div>

      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingParent ? 'Edit Parent' : 'Create New Parent'}
          </h2>
          <form onSubmit={editingParent ? handleUpdateParent : handleCreateParent} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Email *</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            {!editingParent && (
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Student Email</label>
                <input
                  type="email"
                  value={formData.student_email}
                  onChange={(e) => setFormData({ ...formData, student_email: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                  placeholder="Optional: Link to existing student"
                />
              </div>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingParent ? 'Update Parent' : 'Create Parent'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingParent(null);
                  setFormData({ name: '', email: '', student_email: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">All Parents ({parents.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {parents.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                    No parents found
                  </td>
                </tr>
              ) : (
                parents.map((parent) => (
                  <tr key={parent.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{parent.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{parent.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{parent.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(parent)}
                          className="text-accent-green hover:text-accent-green/80 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(parent.id)}
                          className="text-red-400 hover:text-red-300 transition"
                          title="Delete"
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ParentsManagement;
