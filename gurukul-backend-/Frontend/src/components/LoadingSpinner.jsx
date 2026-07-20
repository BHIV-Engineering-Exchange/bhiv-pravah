import React from 'react';

/**
 * Loading Spinner Component
 * Reusable loading indicator for async operations
 */
const LoadingSpinner = ({ size = 'md', message = 'Loading...' }) => {
    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
        xl: 'w-16 h-16'
    };

    return (
        <div className="flex flex-col items-center justify-center gap-3">
            <div className={`${sizeClasses[size]} border-4 border-accent/30 border-t-accent rounded-full animate-spin`}></div>
            {message && (
                <p className="text-gray-400 text-sm animate-pulse">{message}</p>
            )}
        </div>
    );
};

export default LoadingSpinner;
