import React from 'react';

const LoadingState = ({ message = 'Loading...' }) => {
    return (
        <div className="flex items-center justify-center py-12">
            <div className="text-center">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-600 dark:text-slate-400">{message}</p>
            </div>
        </div>
    );
};

export default LoadingState;