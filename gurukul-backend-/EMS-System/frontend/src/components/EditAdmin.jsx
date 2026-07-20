import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { adminsAPI, schoolsAPI } from '../services/api';

const EditAdmin = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [schools, setSchools] = useState([]);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', school_id: '' });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => { fetchData(); }, [id]);

  const fetchData = async () => {
    try {
      setFetching(true);
      const admin = await adminsAPI.getById(id);
      const allAdmins = await adminsAPI.getAll();
      const schoolIds = [...new Set(allAdmins.map(a => a.school_id).filter(id => id !== null))];
      const schoolsPromises = schoolIds.map(schoolId => schoolsAPI.getById(schoolId).catch(() => null));
      const schoolsArray = (await Promise.all(schoolsPromises)).filter(school => school !== null);
      setSchools(schoolsArray);
      setFormData({ name: admin.name || '', email: admin.email || '', password: '', school_id: admin.school_id || '' });
    } catch (err) {
      setError('Failed to load admin details.');
      console.error('Error fetching admin:', err);
    } finally { setFetching(false); }
  };

  const handleChange = (e) => { setFormData({ ...formData, [e.target.name]: e.target.value }); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setSuccess(''); setLoading(true);
    try {
      const updateData = {};
      if (formData.name) updateData.name = formData.name;
      if (formData.email) updateData.email = formData.email;
      if (formData.password) updateData.password = formData.password;
      if (formData.school_id) updateData.school_id = parseInt(formData.school_id);
      await adminsAPI.update(id, updateData);
      setSuccess('Admin updated successfully!');
      setTimeout(() => { navigate('/dashboard/admins'); }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update admin. Please try again.');
    } finally { setLoading(false); }
  };

  if (fetching) {
    return (<div className="text-center py-12"><div className="spinner spinner-lg"></div><p className="mt-4 text-gray-400">Loading admin details...</p></div>);
  }

  return (
    <div className="card-dark p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="heading-serif text-2xl">Edit Admin</h2>
          <p className="text-sm text-accent-green font-medium mt-1">Admin ID: {id}</p>
        </div>
        <button onClick={() => navigate('/dashboard/admins')} className="btn-secondary text-sm">Cancel</button>
      </div>

      {error && (<div className="error-box mb-4"><p>{error}</p></div>)}
      {success && (<div className="success-box mb-4"><p>{success}</p></div>)}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="name" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Admin Name <span className="text-red-400">*</span></label>
          <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} required className="input-dark" />
        </div>
        <div>
          <label htmlFor="email" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Email Address <span className="text-red-400">*</span></label>
          <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required className="input-dark" />
        </div>
        <div>
          <label htmlFor="password" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">New Password</label>
          <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} minLength="6" className="input-dark" placeholder="Leave empty to keep current password" />
          <p className="mt-1 text-xs text-gray-500">Leave empty if you don't want to change the password</p>
        </div>
        <div>
          <label htmlFor="school_id" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">School (School ID)</label>
          <select id="school_id" name="school_id" value={formData.school_id} onChange={handleChange} className="input-dark">
            <option value="">-- Select a school --</option>
            {schools.map((school) => (<option key={school.id} value={school.id}>{school.name} (School ID: {school.id})</option>))}
          </select>
          {formData.school_id && (<p className="mt-1 text-xs text-accent-green">Selected: School ID {formData.school_id}</p>)}
        </div>
        <div className="flex space-x-4 pt-2">
          <button type="submit" disabled={loading} className="flex-1 btn-primary">{loading ? 'Updating...' : 'Update Admin'}</button>
          <button type="button" onClick={() => navigate('/dashboard/admins')} className="btn-secondary">Cancel</button>
        </div>
      </form>
    </div>
  );
};

export default EditAdmin;
