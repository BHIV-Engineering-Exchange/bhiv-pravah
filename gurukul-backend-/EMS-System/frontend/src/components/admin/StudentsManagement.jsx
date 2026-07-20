import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { schoolAdminAPI } from '../../services/api';

const StudentsManagement = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    grade: '',
    parent_email: '',
    parent_name: ''
  });
  const [editingStudent, setEditingStudent] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  useEffect(() => {
    fetchStudents();
  }, [searchTerm]);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getStudents(searchTerm || null);
      setStudents(data);
      setError('');
    } catch (err) {
      setError('Failed to load students. Please try again.');
      console.error('Error fetching students:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createStudent(formData);
      setShowCreateForm(false);
      setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
      fetchStudents();
      alert('Student created successfully! Login credentials sent via email.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create student');
    }
  };

  const handleEdit = (student) => {
    setEditingStudent(student);
      setFormData({
        name: student.name,
        email: student.email,
        grade: student.grade || '',
        parent_email: '',
        parent_name: ''
      });
    setShowCreateForm(true);
  };

  const handleUpdateStudent = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateStudent(editingStudent.id, {
        name: formData.name,
        email: formData.email,
        grade: formData.grade
      });
      setShowCreateForm(false);
      setEditingStudent(null);
      setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
      fetchStudents();
      alert('Student updated successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update student');
    }
  };

  const handleDelete = async (studentId) => {
    if (!window.confirm('Are you sure you want to delete this student? This action cannot be undone.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteStudent(studentId);
      fetchStudents();
      alert('Student deleted successfully!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete student');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading students...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-xl md:text-3xl font-bold text-white">Students Management</h1>
          <p className="text-sm md:text-base text-gray-400 mt-1 md:mt-2">Manage all students in your school</p>
        </div>
        <div className="flex gap-3">
          <button
            data-ems-task="true"
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-3 md:px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm md:text-base whitespace-nowrap"
          >
            ➕ Add Student
          </button>
        </div>
      </div>

      <div className="card-dark p-4">
        <input
          type="text"
          placeholder="Search students by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
        />
      </div>

      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingStudent ? 'Edit Student' : 'Create New Student'}
          </h2>
          <form onSubmit={editingStudent ? handleUpdateStudent : handleCreateStudent} className="space-y-4">
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
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Grade</label>
              <select
                value={formData.grade}
                onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
              >
                <option value="">Select a grade</option>
                <option value="3">3rd Grade</option>
                <option value="4">4th Grade</option>
                <option value="5">5th Grade</option>
                <option value="6">6th Grade</option>
                <option value="7">7th Grade</option>
                <option value="8">8th Grade</option>
                <option value="9">9th Grade</option>
                <option value="10">10th Grade</option>
                <option value="11">11th Grade</option>
                <option value="12">12th Grade</option>
              </select>
            </div>
            {!editingStudent && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Parent Name</label>
                  <input
                    type="text"
                    value={formData.parent_name}
                    onChange={(e) => setFormData({ ...formData, parent_name: e.target.value })}
                    className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                    placeholder="Optional: Parent's name (if creating new parent)"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Parent Email</label>
                  <input
                    type="email"
                    value={formData.parent_email}
                    onChange={(e) => setFormData({ ...formData, parent_email: e.target.value })}
                    className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                    placeholder="Optional: Link to existing parent or create new"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    If parent email exists, it will link to existing parent. If not, a new parent will be created.
                  </p>
                </div>
              </>
            )}
            <div className="flex gap-3">
              <button
                type="submit"
                data-ems-task="true"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingStudent ? 'Update Student' : 'Create Student'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingStudent(null);
                  setFormData({ name: '', email: '', grade: '', parent_email: '', parent_name: '' });
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
          <h2 className="text-xl font-bold text-white">All Students ({students.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Grade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Parent Email(s)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {students.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No students found
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{student.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{student.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{student.grade || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {student.parent_emails && Array.isArray(student.parent_emails) && student.parent_emails.length > 0 ? (
                        <div className="flex flex-col gap-1">
                          {student.parent_emails.map((email, idx) => {
                            const parentName = student.parent_names && student.parent_names[idx] ? student.parent_names[idx] : '';
                            return (
                              <span key={idx} className="inline-flex items-center px-2 py-1 rounded-md bg-green-100 text-accent-green text-xs font-medium">
                                <span className="mr-1">✓</span> 
                                {parentName && <span className="font-semibold mr-1">{parentName}</span>}
                                <span className="text-gray-400">({email})</span>
                              </span>
                            );
                          })}
                        </div>
                      ) : (
                        <span className="text-gray-400 italic">No parent linked</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2 flex-wrap">
                        <Link
                          to={`/dashboard/students/${student.id}/content`}
                          data-ems-interaction="true"
                          className="text-accent-green hover:text-accent-green/80 transition"
                          title="View Generated Content"
                        >
                          📚 View Content
                        </Link>
                        <button
                          onClick={() => handleEdit(student)}
                          className="text-accent-green hover:text-accent-green/80 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDelete(student.id)}
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

export default StudentsManagement;
