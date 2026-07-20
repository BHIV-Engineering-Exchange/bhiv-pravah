import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Search, AlertTriangle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 text-white">
      <div className="w-full max-w-2xl text-center space-y-8">
        {/* 404 Visual */}
        <div className="relative">
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-orange-500/20 to-transparent rounded-full blur-2xl"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-blue-500/20 to-transparent rounded-full blur-xl"></div>
          
          <div className="bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-lg border border-white/20 rounded-2xl shadow-2xl p-8 space-y-6 relative">
            {/* 404 Icon */}
            <div className="flex justify-center">
              <div className="p-6 rounded-full bg-orange-500/20 border border-orange-400/30">
                <AlertTriangle className="h-16 w-16 text-orange-400" />
              </div>
            </div>

            {/* 404 Title */}
            <div className="space-y-4">
              <h1 className="text-6xl font-bold bg-gradient-to-r from-orange-400 via-red-400 to-pink-400 bg-clip-text text-transparent">
                404
              </h1>
              <h2 className="text-2xl font-semibold text-white">
                Page Not Found
              </h2>
              <p className="text-white/70 text-lg max-w-md mx-auto">
                Oops! The page you're looking for doesn't exist. It might have been moved, deleted, or you entered the wrong URL.
              </p>
            </div>

            {/* Helpful Links */}
            <div className="space-y-4">
              <p className="text-white/60 text-sm">
                Here are some helpful links instead:
              </p>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link
                  to="/"
                  className="inline-flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white font-semibold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  <Home className="h-5 w-5" />
                  Go Home
                </Link>
                
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-3 px-6 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/20 hover:border-white/30 rounded-xl transition-all duration-200"
                >
                  <Search className="h-5 w-5" />
                  Dashboard
                </Link>
              </div>

              {/* Quick Navigation */}
              <div className="pt-4 border-t border-white/10">
                <p className="text-white/50 text-sm mb-3">Quick Navigation:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Link
                    to="/assignment"
                    className="px-3 py-1 text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-lg hover:bg-blue-500/30 transition-all"
                  >
                    Take Assessment
                  </Link>
                  <Link
                    to="/intake"
                    className="px-3 py-1 text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 rounded-lg hover:bg-purple-500/30 transition-all"
                  >
                    Edit Profile
                  </Link>
                  <Link
                    to="/admin"
                    className="px-3 py-1 text-xs bg-green-500/20 text-green-300 border border-green-500/30 rounded-lg hover:bg-green-500/30 transition-all"
                  >
                    Admin
                  </Link>
                </div>
              </div>
            </div>

            {/* Go Back Option */}
            <div className="pt-4">
              <button
                onClick={() => window.history.back()}
                className="inline-flex items-center gap-2 text-white/60 hover:text-white/80 text-sm transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Go back to previous page
              </button>
            </div>
          </div>
        </div>

        {/* Additional Help */}
        <div className="text-center space-y-2">
          <p className="text-white/50 text-sm">
            If you believe this is an error, please check the URL or contact support.
          </p>
          <div className="text-white/40 text-xs">
            Error Code: 404 - Page Not Found
          </div>
        </div>
      </div>
    </div>
  );
}