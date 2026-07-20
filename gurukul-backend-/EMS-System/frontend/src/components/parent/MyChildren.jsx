import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { parentAPI } from '../../services/api';

const MyChildren = () => {
  const [children, setChildren] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchChildren();
  }, []);

  const fetchChildren = async () => {
    try {
      setLoading(true);
      const data = await parentAPI.getMyChildren();
      setChildren(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load children. Please try again.';
      setError(`Failed to load children: ${errorMessage}`);
      console.error('Error fetching children:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading children...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
        <button
          onClick={fetchChildren}
          className="mt-4 px-4 py-2 bg-red-600/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-600/30 transition text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  if (children.length === 0) {
    return (
      <div className="card-dark p-8 text-center">
        <div className="text-6xl mb-4">👨‍👩‍👧</div>
        <h2 className="text-2xl font-semibold text-white mb-2">No Children Found</h2>
        <p className="text-gray-400">No students are currently linked to your account.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">My Children</h1>
        <button
          onClick={fetchChildren}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {children.map((child) => (
          <div key={child.id} className="card-dark p-6 border border-[#2A2A3E] hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-2xl">
                  👨‍🎓
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white">{child.name}</h3>
                  <p className="text-sm text-gray-400">{child.email}</p>
                  {child.grade && (
                    <p className="text-sm text-accent-green font-medium mt-1">Grade {child.grade}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-[#2A2A3E]">
              <h4 className="text-sm font-medium text-gray-300 mb-2">Classes ({child.classes?.length || 0}):</h4>
              {child.classes && child.classes.length > 0 ? (
                <div className="space-y-2">
                  {child.classes.map((cls) => (
                    <div key={cls.id} className="bg-[#16162A] rounded-lg p-3">
                      <p className="font-medium text-white">{cls.name}</p>
                      <p className="text-sm text-gray-400">
                        {cls.subject_name || 'No Subject'} • {cls.teacher_name || 'No Teacher'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No classes enrolled</p>
              )}
            </div>
            
            {/* View Content Button */}
            <div className="mt-4 pt-4 border-t border-[#2A2A3E]">
              <Link
                to={`/dashboard/children/${child.id}/content`}
                className="block w-full text-center px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
              >
                📚 View Generated Content
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyChildren;

