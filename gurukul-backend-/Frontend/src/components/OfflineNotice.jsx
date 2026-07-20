import React from 'react';
import { FaWifi, FaRedo } from 'react-icons/fa';

/**
 * Offline Notice Component
 * Shows when the app detects no internet connection
 */
const OfflineNotice = ({ onRetry }) => {
    return (
        <div className="fixed bottom-4 right-4 z-50 max-w-md animate-slide-in-right">
            <div className="bg-gradient-to-r from-orange-600/90 to-red-600/90 backdrop-blur-sm border border-orange-400/30 rounded-xl p-4 shadow-2xl">
                <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center flex-shrink-0">
                        <FaWifi className="text-white text-lg" />
                    </div>

                    <div className="flex-1">
                        <h4 className="text-white font-bold mb-1">No Internet Connection</h4>
                        <p className="text-white/90 text-sm mb-3">
                            We're having trouble connecting. Your progress is saved.
                        </p>

                        {onRetry && (
                            <button
                                onClick={onRetry}
                                className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white text-sm font-semibold rounded-lg transition-all flex items-center gap-2"
                            >
                                <FaRedo className="text-xs" />
                                <span>Try Again</span>
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OfflineNotice;
