import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { adminsAPI, schoolsAPI } from '../services/api';

const CreateAdmin = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedSchoolId = searchParams.get('schoolId');
  
  const [schools, setSchools] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    school_id: selectedSchoolId || '',
  });
  const [loading, setLoading] = useState(false);
  const [fetchingSchools, setFetchingSchools] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSchools();
    if (selectedSchoolId) {
      setFormData(prev => ({ ...prev, school_id: selectedSchoolId }));
    }
  }, [selectedSchoolId]);

  const fetchSchools = async () => {
    try {
      setFetchingSchools(true);
      const admins = await adminsAPI.getAll();
      const schoolIds = [...new Set(admins.map(admin => admin.school_id).filter(id => id !== null))];
      const schoolsPromises = schoolIds.map(schoolId => 
        schoolsAPI.getById(schoolId).catch(() => null)
      );
      const schoolsArray = (await Promise.all(schoolsPromises)).filter(school => school !== null);
      setSchools(schoolsArray);
    } catch (err) {
      setError('Failed to load schools. Please create a school first, then admins will be available.');
      console.error('Error fetching schools:', err);
    } finally {
      setFetchingSchools(false);
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

    if (!formData.school_id) {
      setError('Please select a school');
      setLoading(false);
      return;
    }

    try {
      await adminsAPI.invite(formData);
      setSuccess(`Admin invitation sent to ${formData.email}! The admin will receive an email to set their password.`);
      setFormData({ name: '', email: '', school_id: selectedSchoolId || '' });
      
      setTimeout(() => {
        navigate('/dashboard/admins');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to invite admin. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-dark p-6 max-w-2xl mx-auto animate-fade-in">
      <h2 className="heading-serif text-2xl mb-2">Invite School Admin</h2>
      <p className="text-sm text-gray-400 mb-6">
        Invite an admin by email. They will receive a secure link to set their own password.
      </p>

      {error && (<div className="error-box mb-4"><p>{error}</p></div>)}
      {success && (<div className="success-box mb-4"><p>{success}</p></div>)}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="school_id" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Select School (School ID) <span className="text-red-400">*</span>
          </label>
          <select
            id="school_id"
            name="school_id"
            value={formData.school_id}
            onChange={handleChange}
            required
            disabled={fetchingSchools || !!selectedSchoolId}
            className="input-dark disabled:opacity-50"
          >
            <option value="">-- Select a school --</option>
            {schools.map((school) => (
              <option key={school.id} value={school.id}>
                {school.name} (School ID: {school.id})
              </option>
            ))}
          </select>
          {selectedSchoolId && (
            <p className="mt-1 text-sm text-accent-green font-medium">
              ✓ School pre-selected: School ID {selectedSchoolId} from Schools list
            </p>
          )}
          {formData.school_id && !selectedSchoolId && (
            <p className="mt-1 text-xs text-accent-green">
              Selected: School ID {formData.school_id}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="name" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Admin Name <span className="text-red-400">*</span>
          </label>
          <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} required className="input-dark" placeholder="Enter admin name" />
        </div>

        <div>
          <label htmlFor="email" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Email Address <span className="text-red-400">*</span>
          </label>
          <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required className="input-dark" placeholder="admin@example.com" />
        </div>

        <div className="flex space-x-4 pt-2">
          <button type="submit" disabled={loading || !formData.school_id} className="flex-1 btn-primary">
            {loading ? 'Sending Invitation...' : 'Send Invitation'}
          </button>
          <button type="button" onClick={() => setFormData({ name: '', email: '', school_id: selectedSchoolId || '' })} className="btn-secondary">
            Clear
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateAdmin;
