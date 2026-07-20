import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { schoolsAPI, adminsAPI } from '../services/api';

const SchoolDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [school, setSchool] = useState(null);
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [schoolData, adminsData] = await Promise.all([
        schoolsAPI.getById(id),
        adminsAPI.getBySchool(parseInt(id))
      ]);
      setSchool(schoolData);
      setAdmins(adminsData);
      setError('');
    } catch (err) {
      setError('Failed to load school details.');
      console.error('Error fetching school:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading school details...</p>
      </div>
    );
  }

  if (error || !school) {
    return (
      <div className="error-box">
        <p>{error || 'School not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* School Info */}
      <div className="card-dark p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="heading-serif text-3xl mb-2">{school.name}</h1>
            <span className="badge badge-green">School ID: {school.id}</span>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => navigate(`/dashboard/schools/${id}/edit`)}
              className="btn-secondary text-sm"
            >
              Edit School
            </button>
            <button
              onClick={() => navigate(`/dashboard/create-admin?schoolId=${id}`)}
              className="btn-primary text-sm"
            >
              Create Admin
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wider">Address</label>
            <p className="text-gray-200">{school.address || 'N/A'}</p>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wider">Phone</label>
            <p className="text-gray-200">{school.phone || 'N/A'}</p>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-400 mb-1 uppercase tracking-wider">Email</label>
            <p className="text-gray-200">{school.email || 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Admins for this School */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-lg font-semibold text-white">
            Admins for this School ({admins.length})
          </h2>
        </div>

        {admins.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No admins found for this school.</p>
            <button
              onClick={() => navigate(`/dashboard/create-admin?schoolId=${id}`)}
              className="mt-4 btn-primary text-sm"
            >
              Create First Admin
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table-dark">
              <thead>
                <tr>
                  <th>Admin ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((admin) => (
                  <tr key={admin.id}>
                    <td><span className="badge badge-blue">ID: {admin.id}</span></td>
                    <td className="font-medium text-white">{admin.name}</td>
                    <td>{admin.email}</td>
                    <td>
                      <button
                        onClick={() => navigate(`/dashboard/admins/${admin.id}/edit`)}
                        className="text-accent-blue hover:text-accent-blue/80 font-medium transition-colors"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SchoolDetails;
