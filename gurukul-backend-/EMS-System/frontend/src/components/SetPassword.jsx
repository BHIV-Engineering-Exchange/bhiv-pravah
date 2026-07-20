import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../services/api';

const SetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing token. Please check your email link.');
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    // Validation
    if (!password) {
      setError('Password is required');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!token) {
      setError('Invalid token. Please check your email link.');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.setPassword(token, password);
      
      if (response.success) {
        setSuccess(true);
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setError(response.message || 'Failed to set password. Please try again.');
      }
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        err.response?.data?.message || 
        'Failed to set password. The token may be expired or invalid. Please request a new invitation.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2A2A3E] rounded-3xl p-8">
          <div className="text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Invalid Link</h2>
            <p className="text-gray-400 mb-6">
              The password setup link is invalid or missing a token.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-accent-green text-white py-2 px-4 rounded-lg hover:bg-accent-green/90 transition"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2A2A3E] rounded-3xl p-8">
          <div className="text-center">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Password Set Successfully!</h2>
            <p className="text-gray-400 mb-6">
              Your password has been set. You will be redirected to the login page shortly.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-accent-green text-white py-2 px-4 rounded-lg hover:bg-accent-green/90 transition"
            >
              Go to Login Now
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2A2A3E] rounded-3xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Set Your Password
          </h1>
          <p className="text-gray-400">
            Please set a password for your admin account
          </p>
        </div>

        {error && (
          <div className="mb-4 p-4 error-box">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              New Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-transparent"
              placeholder="Enter your password"
              required
              minLength={6}
            />
            <p className="mt-1 text-xs text-gray-500">Password must be at least 6 characters</p>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-transparent"
              placeholder="Confirm your password"
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent-green text-white py-3 px-4 rounded-lg hover:bg-accent-green/90 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Setting Password...' : 'Set Password'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => navigate('/login')}
            className="text-sm text-accent-green hover:text-indigo-800"
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default SetPassword;
