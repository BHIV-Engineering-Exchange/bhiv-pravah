import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminsAPI, schoolsAPI } from '../services/api';

const AdminList = () => {
  const navigate = useNavigate();
  const [admins, setAdmins] = useState([]);
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterSchoolId, setFilterSchoolId] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchData();
  }, [filterSchoolId, search]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      const { schoolsAPI } = await import('../services/api');
      const adminsForSchools = await adminsAPI.getAll();
      const schoolIds = [...new Set(adminsForSchools.map(admin => admin.school_id).filter(id => id !== null))];
      const schoolsPromises = schoolIds.map(schoolId => 
        schoolsAPI.getById(schoolId).catch(() => null)
      );
      const schoolsArray = (await Promise.all(schoolsPromises)).filter(school => school !== null);
      setSchools(schoolsArray);
      const adminsData = await adminsAPI.getAll(search || null, filterSchoolId ? parseInt(filterSchoolId) : null);
      setAdmins(adminsData);
    } catch (err) {
      setError('Failed to load admins. Please try again.');
      console.error('Error fetching admins:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (adminId) => {
    try {
      setDeleting(true);
      await adminsAPI.delete(adminId);
      setDeleteConfirm(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete admin. Please try again.');
      setDeleteConfirm(null);
    } finally {
      setDeleting(false);
    }
  };

  const getSchoolName = (schoolId) => {
    if (!schoolId) return 'N/A';
    const school = schools.find((s) => s.id === schoolId);
    return school ? school.name : `Unknown (ID: ${schoolId})`;
  };

  if (loading) {
    return (
      <div className="card-dark p-6">
        <div className="text-center py-8">
          <div className="spinner"></div>
          <p className="mt-4 text-gray-400">Loading admins...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card-dark overflow-hidden animate-fade-in">
      <div className="px-6 py-4 border-b border-[#2A2A3E]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-white">All School Admins</h2>
          <button onClick={fetchData} className="btn-secondary text-sm">
            ↻ Refresh
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="search" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Search
            </label>
            <input
              type="text"
              id="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name or email..."
              className="input-dark text-sm !py-2"
            />
          </div>
          <div>
            <label htmlFor="school-filter" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Filter by School:
            </label>
            <select
              id="school-filter"
              value={filterSchoolId}
              onChange={(e) => setFilterSchoolId(e.target.value)}
              className="input-dark text-sm !py-2"
            >
              <option value="">All Schools</option>
              {schools.map((school) => (
                <option key={school.id} value={school.id}>
                  {school.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="text-lg font-semibold text-white mb-4">Confirm Delete</h3>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete admin "{deleteConfirm.name}"? This action cannot be undone.
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

      {error && (
        <div className="error-box m-6">
          <p>{error}</p>
        </div>
      )}

      {admins.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          {filterSchoolId ? (
            <p>No admins found for this school. Create an admin to get started!</p>
          ) : (
            <p>No admins found. Create your first school admin!</p>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table-dark">
            <thead>
              <tr>
                <th>Admin ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>School (School ID)</th>
                <th>Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {admins.map((admin) => (
                <tr key={admin.id}>
                  <td>
                    <span className="badge badge-blue">ID: {admin.id}</span>
                  </td>
                  <td className="font-medium text-white">{admin.name}</td>
                  <td>{admin.email}</td>
                  <td>
                    {admin.school_id ? (
                      <span>
                        <span className="font-medium text-gray-200">{getSchoolName(admin.school_id)}</span>
                        <span className="badge badge-green ml-2">ID: {admin.school_id}</span>
                      </span>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td>
                    <span className="badge badge-blue">{admin.role}</span>
                  </td>
                  <td className="space-x-2">
                    <button
                      onClick={() => navigate(`/dashboard/admins/${admin.id}/edit`)}
                      className="text-accent-blue hover:text-accent-blue/80 font-medium transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteConfirm({ id: admin.id, name: admin.name })}
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
          Showing {admins.length} admin{admins.length !== 1 ? 's' : ''}
          {filterSchoolId && ` for selected school`}
        </p>
      </div>
    </div>
  );
};

export default AdminList;
