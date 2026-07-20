import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { schoolsAPI } from '../services/api';

const CreateSchool = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    address: '',
    phone: '',
    email: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
      await schoolsAPI.create(formData);
      setSuccess('School created successfully!');
      setFormData({ name: '', address: '', phone: '', email: '' });
      
      setTimeout(() => {
        navigate('/dashboard/schools');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create school. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-dark p-6 max-w-2xl mx-auto animate-fade-in">
      <h2 className="heading-serif text-2xl mb-6">Create New School</h2>

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
            placeholder="Enter school name"
          />
        </div>

        <div>
          <label htmlFor="address" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={formData.address}
            onChange={handleChange}
            rows="3"
            className="input-dark !rounded-xl"
            placeholder="Enter school address"
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
              value={formData.phone}
              onChange={handleChange}
              className="input-dark"
              placeholder="123-456-7890"
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
              value={formData.email}
              onChange={handleChange}
              className="input-dark"
              placeholder="school@example.com"
            />
          </div>
        </div>

        <div className="flex space-x-4 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 btn-primary"
          >
            {loading ? 'Creating...' : 'Create School'}
          </button>
          <button
            type="button"
            onClick={() => setFormData({ name: '', address: '', phone: '', email: '' })}
            className="btn-secondary"
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateSchool;
