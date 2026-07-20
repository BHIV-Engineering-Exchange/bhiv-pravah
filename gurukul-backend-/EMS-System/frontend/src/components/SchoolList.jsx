import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { schoolsAPI } from '../services/api';

const SchoolList = () => {
  const navigate = useNavigate();
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchSchools();
  }, [search]);

  const fetchSchools = async () => {
    try {
      setLoading(true);
      const { adminsAPI } = await import('../services/api');
      const admins = await adminsAPI.getAll();
      const schoolIds = [...new Set(admins.map(admin => admin.school_id).filter(id => id !== null))];
      const schoolsPromises = schoolIds.map(schoolId => 
        schoolsAPI.getById(schoolId).catch(() => null)
      );
      const schoolsArray = (await Promise.all(schoolsPromises)).filter(school => school !== null);
      setSchools(schoolsArray);
      setError('');
    } catch (err) {
      setError('Failed to load schools. The list schools endpoint has been removed. Access schools through admins or use specific school IDs.');
      console.error('Error fetching schools:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (schoolId) => {
    try {
      setDeleting(true);
      await schoolsAPI.delete(schoolId);
      setDeleteConfirm(null);
      fetchSchools();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete school. Please try again.');
      setDeleteConfirm(null);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="card-dark p-6">
        <div className="text-center py-8">
          <div className="spinner"></div>
          <p className="mt-4 text-gray-400">Loading schools...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card-dark overflow-hidden animate-fade-in">
      <div className="px-6 py-4 border-b border-[#2A2A3E] flex justify-between items-center">
        <h2 className="text-lg font-semibold text-white">All Schools</h2>
        <div className="flex items-center space-x-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search schools..."
            className="input-dark text-sm w-64 !py-2 !rounded-capsule"
          />
          <button onClick={fetchSchools} className="btn-secondary text-sm">
            ↻ Refresh
          </button>
        </div>
      </div>
      
      {error && (
        <div className="error-box m-6">
          <p>{error}</p>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-lg font-semibold text-white mb-4">Confirm Delete</h3>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete this school? This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => handleDelete(deleteConfirm.id)}
                disabled={deleting}
                className="flex-1 btn-danger py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 btn-secondary py-2.5"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {schools.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          <p>No schools found. Create your first school!</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table-dark">
            <thead>
              <tr>
                <th>School ID</th>
                <th>Name</th>
                <th>Address</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {schools.map((school) => (
                <tr key={school.id}>
                  <td>
                    <span className="badge badge-green">ID: {school.id}</span>
                  </td>
                  <td>
                    <button
                      onClick={() => navigate(`/dashboard/schools/${school.id}`)}
                      className="text-accent-green hover:text-accent-green/80 font-medium hover:underline transition-colors"
                    >
                      {school.name}
                    </button>
                  </td>
                  <td>{school.address || '-'}</td>
                  <td>{school.phone || '-'}</td>
                  <td>{school.email || '-'}</td>
                  <td className="space-x-2">
                    <button
                      onClick={() => navigate(`/dashboard/schools/${school.id}/edit`)}
                      className="text-accent-blue hover:text-accent-blue/80 font-medium transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => navigate(`/dashboard/create-admin?schoolId=${school.id}`)}
                      className="text-accent-green hover:text-accent-green/80 font-medium transition-colors"
                      title="Create admin for this school"
                    >
                      Create Admin
                    </button>
                    <button
                      onClick={() => setDeleteConfirm({ id: school.id, name: school.name })}
                      className="text-red-400 hover:text-red-300 font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="px-6 py-4 border-t border-[#2A2A3E] bg-[#16162A]">
        <p className="text-sm text-gray-500">
          Showing {schools.length} school{schools.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
};

export default SchoolList;
