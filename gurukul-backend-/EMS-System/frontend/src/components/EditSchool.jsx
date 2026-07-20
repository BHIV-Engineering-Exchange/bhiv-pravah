import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { schoolsAPI } from '../services/api';

const EditSchool = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
  });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSchool();
  }, [id]);

  const fetchSchool = async () => {
    try {
      setFetching(true);
      const school = await schoolsAPI.getById(id);
      setFormData({
        name: school.name || '',
        address: school.address || '',
        phone: school.phone || '',
        email: school.email || '',
      });
    } catch (err) {
      setError('Failed to load school details.');
      console.error('Error fetching school:', err);
    } finally {
      setFetching(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const updateData = {};
      if (formData.name) updateData.name = formData.name;
      if (formData.address !== undefined) updateData.address = formData.address || null;
      if (formData.phone !== undefined) updateData.phone = formData.phone || null;
      if (formData.email) updateData.email = formData.email || null;

      await schoolsAPI.update(id, updateData);
      setSuccess('School updated successfully!');
      setTimeout(() => {
        navigate('/dashboard/schools');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update school. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading school details...</p>
      </div>
    );
  }

  return (
    <div className="card-dark p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="heading-serif text-2xl">Edit School</h2>
          <p className="text-sm text-accent-green font-medium mt-1">School ID: {id}</p>
        </div>
        <button
          onClick={() => navigate('/dashboard/schools')}
          className="btn-secondary text-sm"
        >
          Cancel
        </button>
      </div>

      {error && (
        <div className="error-box mb-4">
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="success-box mb-4">
          <p>{success}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="name" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            School Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="input-dark"
          />
        </div>

        <div>
          <label htmlFor="address" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={formData.address || ''}
            onChange={handleChange}
            rows="3"
            className="input-dark !rounded-xl"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="phone" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Phone Number
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone || ''}
              onChange={handleChange}
              className="input-dark"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email || ''}
              onChange={handleChange}
              className="input-dark"
            />
          </div>
        </div>

        <div className="flex space-x-4 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 btn-primary"
          >
            {loading ? 'Updating...' : 'Update School'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/dashboard/schools')}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditSchool;
