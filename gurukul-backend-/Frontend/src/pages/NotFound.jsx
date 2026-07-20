import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
            <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600 mb-4">
                404
            </h1>
            <h2 className="text-2xl font-semibold text-gray-200 mb-4">Page Not Found</h2>
            <p className="text-gray-400 mb-8 max-w-md">
                The path you are looking for does not exist in the Gurukul. Let's get you back on track.
            </p>
            <Link
                to="/"
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:shadow-lg hover:shadow-purple-500/30 transition-all duration-300 font-medium"
            >
                Return Home
            </Link>
        </div>
    );
};

export default NotFound;
