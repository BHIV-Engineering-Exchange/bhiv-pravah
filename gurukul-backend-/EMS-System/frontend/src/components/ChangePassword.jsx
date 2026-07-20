import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const ChangePassword = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validation
    if (!currentPassword) {
      setError('Current password is required');
      return;
    }

    if (!newPassword) {
      setError('New password is required');
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters long');
      return;
    }

    if (newPassword === currentPassword) {
      setError('New password must be different from your current password');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.changePassword(currentPassword, newPassword);
      
      if (response.success) {
        setSuccess(true);
        // Clear form
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        // Show success message for 3 seconds, then optionally redirect
        setTimeout(() => {
          setSuccess(false);
        }, 3000);
      } else {
        setError(response.message || 'Failed to change password. Please try again.');
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        err.response?.data?.message || 
        'Failed to change password. Please check your current password and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card-dark p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold text-white mb-6">Reset Password</h2>

      {error && (
        <div className="mb-4 p-4 error-box">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 success-box">
          <p className="text-accent-green text-sm">Password changed successfully! You can now use your new password to log in.</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="currentPassword" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Current Password <span className="text-red-400">*</span>
          </label>
          <input
            id="currentPassword"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full input-dark !py-2"
            placeholder="Enter your current password"
            required
          />
        </div>

        <div>
          <label htmlFor="newPassword" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            New Password <span className="text-red-400">*</span>
          </label>
          <input
            id="newPassword"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full input-dark !py-2"
            placeholder="Enter your new password"
            required
            minLength={6}
          />
          <p className="mt-1 text-xs text-gray-500">Password must be at least 6 characters</p>
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Confirm New Password <span className="text-red-400">*</span>
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full input-dark !py-2"
            placeholder="Confirm your new password"
            required
            minLength={6}
          />
        </div>

        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-accent-green text-[#0D0D0D] py-3 px-4 rounded-capsule font-semibold hover:bg-accent-green/90 focus:outline-none focus:ring-2 focus:ring-accent-green focus:ring-offset-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Changing Password...' : 'Change Password'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Security Tips:</strong>
        </p>
        <ul className="text-sm text-blue-700 mt-2 list-disc list-inside space-y-1">
          <li>Use a strong password with a mix of letters, numbers, and special characters</li>
          <li>Don't share your password with anyone</li>
          <li>Change your password regularly</li>
          <li>Make sure your new password is different from your current one</li>
        </ul>
      </div>
    </div>
  );
};

export default ChangePassword;

