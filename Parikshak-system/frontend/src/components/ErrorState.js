import React from 'react';
import { AlertCircle, RefreshCcw } from 'lucide-react';

const ErrorState = ({ message = 'Something went wrong', onRetry }) => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-6 p-8 card bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-900">
            <div className="p-4 bg-red-100 dark:bg-red-900/30 rounded-full">
                <AlertCircle size={48} className="text-red-600 dark:text-red-400" />
            </div>
            <div className="text-center">
                <h3 className="text-xl font-bold text-red-900 dark:text-red-100 mb-2">Error Encountered</h3>
                <p className="text-red-600 dark:text-red-400">{message}</p>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
                >
                    <RefreshCcw size={18} />
                    Try Again
                </button>
            )}
        </div>
    );
};

export default ErrorState;
