import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const TeachersManagement = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  // Create form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: ''
  });
  const [editingTeacher, setEditingTeacher] = useState(null);

  useEffect(() => {
    fetchTeachers();
  }, [searchTerm]);

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getTeachers(searchTerm || null);
      setTeachers(data);
      setError('');
    } catch (err) {
      setError('Failed to load teachers. Please try again.');
      console.error('Error fetching teachers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createTeacher(formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', subject: '' });
      fetchTeachers();
      alert('Teacher created successfully! Login credentials sent via email.');
    } catch (err) {
      console.error('Error creating teacher:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create teacher. Please check the console for details.';
      alert(`Error: ${errorMessage}`);
    }
  };

  const handleEdit = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({
      name: teacher.name,
      email: teacher.email,
      subject: teacher.subject || ''
    });
    setShowCreateForm(true);
  };

  const handleUpdateTeacher = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateTeacher(editingTeacher.id, {
        name: formData.name,
        email: formData.email,
        subject: formData.subject
      });
      setShowCreateForm(false);
      setEditingTeacher(null);
      setFormData({ name: '', email: '', subject: '' });
      fetchTeachers();
      alert('Teacher updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update teacher');
    }
  };

  const handleDelete = async (teacherId) => {
    if (!window.confirm('Are you sure you want to delete this teacher? This action cannot be undone.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteTeacher(teacherId);
      fetchTeachers();
      alert('Teacher deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete teacher');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading teachers...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-xl md:text-3xl font-bold text-white">Teachers Management</h1>
          <p className="text-sm md:text-base text-gray-400 mt-1 md:mt-2">Manage all teachers in your school</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-3 md:px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm md:text-base whitespace-nowrap"
          >
            ➕ Add Teacher
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="card-dark p-4">
        <input
          type="text"
          placeholder="Search teachers by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-transparent"
        />
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingTeacher ? 'Edit Teacher' : 'Create New Teacher'}
          </h2>
          <form onSubmit={editingTeacher ? handleUpdateTeacher : handleCreateTeacher} className="space-y-4">
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
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Subject</label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingTeacher ? 'Update Teacher' : 'Create Teacher'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingTeacher(null);
                  setFormData({ name: '', email: '', subject: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Teachers List */}
      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">All Teachers ({teachers.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {teachers.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                    No teachers found
                  </td>
                </tr>
              ) : (
                teachers.map((teacher) => (
                  <tr key={teacher.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{teacher.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{teacher.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{teacher.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{teacher.subject || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(teacher)}
                          className="text-accent-green hover:text-accent-green/80 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(teacher.id)}
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

export default TeachersManagement;
