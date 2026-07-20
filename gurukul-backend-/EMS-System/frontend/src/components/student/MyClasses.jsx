import React, { useState, useEffect } from 'react';
import { studentAPI } from '../../services/api';

const MyClasses = () => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const data = await studentAPI.getMyClasses();
      setClasses(data);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load classes. Please try again.';
      setError(`Failed to load classes: ${errorMessage}`);
      console.error('Error fetching classes:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading classes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
        <button
          onClick={fetchClasses}
          className="mt-4 px-4 py-2 bg-red-600/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-600/30 transition text-sm font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  if (classes.length === 0) {
    return (
      <div className="card-dark p-8 text-center">
        <div className="text-6xl mb-4">📚</div>
        <h2 className="text-2xl font-semibold text-white mb-2">No Classes Found</h2>
        <p className="text-gray-400">You are not enrolled in any classes yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">My Classes</h1>
        <button
          onClick={fetchClasses}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {classes.map((cls) => (
          <div key={cls.id} className="card-dark p-6 border border-[#2A2A3E] hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white mb-1">{cls.name}</h3>
                <p className="text-sm text-gray-400">Grade {cls.grade}</p>
              </div>
              <div className="text-3xl">📚</div>
            </div>

            <div className="space-y-3 pt-4 border-t border-[#2A2A3E]">
              <div className="flex items-center text-sm">
                <span className="font-medium text-gray-300 w-20">Subject:</span>
                <span className="text-white">{cls.subject_name || 'N/A'}</span>
              </div>
              <div className="flex items-center text-sm">
                <span className="font-medium text-gray-300 w-20">Teacher:</span>
                <span className="text-white">{cls.teacher_name || 'N/A'}</span>
              </div>
              {cls.academic_year && (
                <div className="flex items-center text-sm">
                  <span className="font-medium text-gray-300 w-20">Year:</span>
                  <span className="text-white">{cls.academic_year}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyClasses;

