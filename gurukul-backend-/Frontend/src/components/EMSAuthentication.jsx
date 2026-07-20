import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import emsApi from '../services/emsApi';
import { FaLock, FaSpinner, FaTimes } from 'react-icons/fa';

const EMSAuthentication = ({ onSuccess, onCancel }) => {
    const { user } = useAuth();
    const [email, setEmail] = useState(user?.email || '');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Verify email matches current user
            if (email !== user?.email) {
                setError('Email must match your Gurukul account');
                setLoading(false);
                return;
            }

            // Authenticate with EMS
            const token = await emsApi.getEMSToken(email, password);
            
            if (token) {
                setSuccess(true);
                // Show success message briefly before closing
                setTimeout(() => {
                    if (onSuccess) {
                        onSuccess(token);
                    }
                }, 1000);
            }
        } catch (err) {
            console.error('EMS authentication error:', err);
            let errorMessage = err.message || 'Failed to authenticate with EMS.';
            
            // Provide more helpful error messages
            if (errorMessage.includes('Incorrect email or password') || errorMessage.includes('401')) {
                errorMessage = 'Incorrect email or password. Please use your EMS System password (not your Gurukul password). If you don\'t have an EMS account or forgot your password, contact your school administrator.';
            } else if (errorMessage.includes('not found') || errorMessage.includes('404')) {
                errorMessage = 'Student account not found in EMS System. Please contact your school administrator to create your account.';
            } else if (errorMessage.includes('inactive') || errorMessage.includes('inactive')) {
                errorMessage = 'Your EMS account is inactive. Please contact your school administrator.';
            }
            
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 shadow-2xl max-w-md w-full relative animate-fade-in-up">
                {onCancel && (
                    <button
                        onClick={onCancel}
                        className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                    >
                        <FaTimes className="text-xl" />
                    </button>
                )}

                <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 bg-orange-500/20 rounded-xl border border-orange-500/30">
                        <FaLock className="text-orange-400 text-2xl" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Authenticate with EMS</h2>
                        <p className="text-sm text-gray-400">Enter your EMS credentials (one-time setup)</p>
                    </div>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-500/20 text-red-300 rounded-xl text-sm border border-red-500/30">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-4 p-3 bg-green-500/20 text-green-300 rounded-xl text-sm border border-green-500/30">
                        ✓ Authentication successful! Your credentials have been saved.
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Email Address
                        </label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-3 bg-black/60 border border-white/20 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                            placeholder="student@example.com"
                            required
                            disabled={loading}
                        />
                        <p className="mt-1 text-xs text-gray-400">
                            Must match your Gurukul account email ({user?.email})
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            EMS Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-3 bg-black/60 border border-white/20 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                            placeholder="Enter your EMS System password"
                            required
                            disabled={loading}
                        />
                        <p className="mt-1 text-xs text-gray-400">
                            ⚠️ Use your EMS System password (may be different from Gurukul password)
                        </p>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white rounded-xl font-medium shadow-lg transition-transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                        >
                            {loading ? (
                                <>
                                    <FaSpinner className="animate-spin" />
                                    <span>Authenticating...</span>
                                </>
                            ) : (
                                <>
                                    <FaLock />
                                    <span>Authenticate</span>
                                </>
                            )}
                        </button>
                        {onCancel && (
                            <button
                                type="button"
                                onClick={onCancel}
                                disabled={loading}
                                className="px-6 py-3 bg-white/5 hover:bg-white/10 text-gray-300 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                </form>

                <div className="mt-6 pt-6 border-t border-white/10">
                    <p className="text-xs text-gray-400 text-center">
                        💡 You only need to authenticate once. Your credentials will be saved for future sessions.
                    </p>
                    <p className="text-xs text-gray-500 text-center mt-2">
                        💡 <strong>Note:</strong> Your EMS password may be different from your Gurukul password. If you don't have an EMS account or forgot your password, contact your school administrator.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default EMSAuthentication;

