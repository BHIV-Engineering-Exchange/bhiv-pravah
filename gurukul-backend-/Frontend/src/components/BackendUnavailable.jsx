import React from 'react';
import { FaExclamationTriangle, FaRedo, FaHome } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

/**
 * Backend Unavailable Component
 * Shows when backend returns 5xx errors or is unreachable
 */
const BackendUnavailable = ({ feature = 'this feature', onRetry }) => {
    const navigate = useNavigate();

    return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
            <div className="max-w-md w-full bg-black/40 backdrop-blur-sm border-2 border-yellow-600/30 rounded-2xl p-8 text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-yellow-600/70 to-orange-600/70 flex items-center justify-center">
                    <FaExclamationTriangle className="text-white text-3xl" />
                </div>

                <h3 className="text-2xl font-bold text-white mb-3">
                    Taking a Brief Rest
                </h3>

                <p className="text-gray-300 mb-6">
                    We're having trouble loading {feature}. Our servers are taking a moment to rest.
                    Your progress is safe.
                </p>

                <div className="flex flex-col sm:flex-row gap-3">
                    {onRetry && (
                        <button
                            onClick={onRetry}
                            className="flex-1 px-6 py-3 bg-gradient-to-r from-yellow-600/70 to-orange-600/70 hover:from-yellow-500/70 hover:to-orange-500/70 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                        >
                            <FaRedo />
                            <span>Try Again</span>
                        </button>
                    )}

                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex-1 px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/10 transition-all flex items-center justify-center gap-2"
                    >
                        <FaHome />
                        <span>Go Home</span>
                    </button>
                </div>

                <p className="text-gray-400 text-sm mt-6">
                    Usually resolves in a few moments
                </p>
            </div>
        </div>
    );
};

export default BackendUnavailable;
